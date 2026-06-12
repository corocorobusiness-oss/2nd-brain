#!/usr/bin/env python3
"""AI帳簿 週次自動記帳 v2「kicho」 — 家電型（エージェント不要で完走する）

毎週月曜9:30にlaunchdから起動され、以下を無人実行する:
  1. freee API（口座連携経由のGMOあおぞら銀行明細）から新規明細を取得
     - 認証は freee-mcp と共有（~/.config/freee-mcp/）。期限切れは自動リフレッシュ
  2. 表記ゆれを正規化し、(date, side, amount, balance) で重複排除して銀行明細CSVへ追記
  3. build_2026_journal.py で仕訳帳を再生成（仕訳ルールはあちらが唯一の正）
  4. ledger.py で検証（貸借一致・銀行残高一致）。NGなら自動ロールバック
  5. 収支管理.md のマーカー区間（月次サマリー・経費内訳）を更新
  6. 当日のデイリーノートに結果を1行報告

安全装置:
  - 未知の明細パターンが1件でもあれば「自動計上せず」要確認リストを報告して停止（exit 2）
  - 実行前にCSV/仕訳帳をバックアップ、検証NGで復元（exit 1）
  - 新規明細が7日以上ゼロなら「freee再同意切れの可能性」を警告

判断が必要な仕事（要確認の解消・月次監査・申告準備）はAIエージェントの担当。
→ 月初に「帳簿監査して」（02_経営/帳簿/README.md の月次ルーチン参照）

実行: python3 kicho.py [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

# 仕訳ルールの唯一の正（build_2026_journal.py）をそのまま使う
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_2026_journal import EXPENSE_RULES, INCOME_RULES, match  # noqa: E402

# ---- パス ----
BASE = Path(__file__).resolve().parents[1]          # 02_経営/帳簿
VAULT = BASE.parents[1]                              # 2nd-Brain
BANK_CSV = BASE / "data" / "2026_銀行明細_GMOあおぞら.csv"
JOURNAL = BASE / "2026_仕訳帳.csv"
BACKUP_DIR = BASE / "data" / "backups"
SHUSHI = VAULT / "02_経営" / "収支管理.md"
DAILY_DIR = VAULT / "05_日誌"
DAILY_TEMPLATE = VAULT / "00_システム" / "Templates" / "Daily_Note_Template.md"
SCRIPTS = Path(__file__).resolve().parent

# ---- freee API（認証はfreee-mcpと共有） ----
FREEE_CONFIG_DIR = Path.home() / ".config" / "freee-mcp"
FREEE_TOKEN_URL = "https://accounts.secure.freee.co.jp/public_api/token"
FREEE_API_BASE = "https://api.freee.co.jp"
GMO_WALLETABLE_ID = 4635538  # GMOあおぞらネット銀行（API）

# 銀行明細の表記ゆれ → 帳簿の正規表記（NFKC正規化後に適用）
DESC_REPLACEMENTS = [
    ("グ-グル", "グーグル"),
    ("アポロステ-シヨン", "アポロステーション"),
    ("キヤツシユバツク", "キャッシュバック"),
    ("デビツト", "デビット"),
    ("ネツト", "ネット"),
]

PL_INCOME = {"売上高", "雑収入"}
PL_EXPENSE = {"研修費", "通信費", "車両費", "消耗品費", "支払手数料", "減価償却費"}

AUTO_START = "<!-- kicho:auto:start -->"
AUTO_END = "<!-- kicho:auto:end -->"


# ================= 基本ユーティリティ =================

def today() -> dt.date:
    return dt.datetime.now().date()


def read_bank_rows() -> list[dict[str, str]]:
    if not BANK_CSV.exists():
        return []
    with BANK_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def last_bank_date(rows: list[dict[str, str]]) -> dt.date | None:
    dates = [r["date"] for r in rows if r.get("date")]
    return dt.date.fromisoformat(max(dates)) if dates else None


def normalize_description(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    for old, new in DESC_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def yen(n: int) -> str:
    return f"¥{n:,}"


# ================= freee API =================

def _expires_to_epoch_sec(value) -> float:
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 1000.0 if v > 1e12 else v
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _make_expires_at(old_value, created_sec: float, expires_in: float):
    """既存tokens.jsonのexpires_atと同じ型・スケールを保つ（freee-mcp互換）。"""
    exp = created_sec + expires_in
    if isinstance(old_value, (int, float)):
        return int(exp * 1000) if float(old_value) > 1e12 else int(exp)
    return dt.datetime.fromtimestamp(exp).astimezone().isoformat()


def _refresh_tokens(config: dict, tokens: dict, tokens_path: Path) -> dict:
    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": config["clientId"],
        "client_secret": config["clientSecret"],
        "refresh_token": tokens["refresh_token"],
    }).encode()
    req = urllib.request.Request(
        FREEE_TOKEN_URL, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode())
    created = float(body.get("created_at") or time.time())
    tokens = dict(tokens)
    tokens.update({
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token", tokens["refresh_token"]),
        "token_type": body.get("token_type", tokens.get("token_type", "bearer")),
        "scope": body.get("scope", tokens.get("scope", "")),
        "expires_at": _make_expires_at(tokens.get("expires_at"), created,
                                       float(body.get("expires_in", 21600))),
    })
    tmp = tokens_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, tokens_path)
    os.chmod(tokens_path, 0o600)
    return tokens


def _api_get(path: str, params: dict, tokens: dict) -> dict:
    url = f"{FREEE_API_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_freee_rows(since: dt.date | None) -> tuple[list[dict[str, str]], str]:
    """新規の銀行明細を取得してCSV行形式で返す。失敗時は空＋警告文（ジョブは続行）。"""
    try:
        config = json.loads((FREEE_CONFIG_DIR / "config.json").read_text(encoding="utf-8"))
        tokens_path = FREEE_CONFIG_DIR / "tokens.json"
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [], f"⚠️ freee認証情報を読めない（{e}）"

    company_id = config.get("currentCompanyId") or config.get("defaultCompanyId")
    try:
        if _expires_to_epoch_sec(tokens.get("expires_at")) < time.time() + 120:
            tokens = _refresh_tokens(config, tokens, tokens_path)
    except Exception as e:
        return [], f"⚠️ freeeトークン更新失敗（{e}）— 口座連携の再同意切れの可能性"

    txns: list[dict] = []
    try:
        offset = 0
        while True:
            params = {
                "company_id": company_id,
                "walletable_type": "bank_account",
                "walletable_id": GMO_WALLETABLE_ID,
                "start_date": (since or dt.date(2026, 1, 1)).isoformat(),
                "end_date": today().isoformat(),
                "limit": 100,
                "offset": offset,
            }
            try:
                body = _api_get("/api/1/wallet_txns", params, tokens)
            except urllib.error.HTTPError as he:
                if he.code == 401 and offset == 0:
                    tokens = _refresh_tokens(config, tokens, tokens_path)
                    body = _api_get("/api/1/wallet_txns", params, tokens)
                else:
                    raise
            page = body.get("wallet_txns", [])
            txns.extend(page)
            if len(page) < 100:
                break
            offset += 100
    except Exception as e:
        return [], f"⚠️ freee明細取得失敗（{e}）— 口座連携の再同意切れの可能性"

    rows = [{
        "date": t.get("date", ""),
        "side": t.get("entry_side", ""),
        "amount": str(t.get("amount", "")),
        "balance": str(t.get("balance", "")),
        "status": "registered" if t.get("status") == 2 else "pending",
        "description": normalize_description(t.get("description", "")),
    } for t in txns]

    # 重複排除キーに説明文は使わない（表記ゆれの影響を受けないように。残高込みで実質一意）
    seen = {(r["date"], r["side"], str(r["amount"]), str(r["balance"])) for r in read_bank_rows()}
    fresh = [r for r in rows if (r["date"], r["side"], r["amount"], r["balance"]) not in seen]
    latest = max((r["date"] for r in rows), default="なし")
    return fresh, f"freee取得OK（新規{len(fresh)}件・明細最終日{latest}）"


# ================= 記帳パイプライン =================

def classify(row: dict[str, str]):
    rules = INCOME_RULES if row["side"] == "income" else EXPENSE_RULES
    return match(rules, row["description"])


def append_bank_rows(new_rows: list[dict[str, str]]) -> None:
    fieldnames = ["date", "side", "amount", "balance", "status", "description"]
    merged = read_bank_rows() + [{k: r.get(k, "") for k in fieldnames} for r in new_rows]
    merged.sort(key=lambda r: r["date"])  # 安定ソート: 同日内の並び（残高の連鎖）は保持
    with BANK_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(merged)


def run_build_and_ledger() -> tuple[bool, str]:
    out = []
    for script in ("build_2026_journal.py", "ledger.py"):
        p = subprocess.run([sys.executable, str(SCRIPTS / script)], cwd=str(BASE),
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out.append(f"--- {script} ---\n{p.stdout}")
        if p.returncode != 0 or "❌" in p.stdout:
            return False, "\n".join(out)
    return True, "\n".join(out)


def journal_monthly() -> dict[int, dict[str, int]]:
    monthly: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with JOURNAL.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            m = int(r["日付"][5:7])
            dr, cr = r["借方科目"], r["貸方科目"]
            if dr in PL_EXPENSE:
                monthly[m][dr] += int(r["借方金額"])
            if dr in PL_INCOME:
                monthly[m][dr] -= int(r["借方金額"])
            if cr in PL_INCOME:
                monthly[m][cr] += int(r["貸方金額"])
            if cr in PL_EXPENSE:
                monthly[m][cr] -= int(r["貸方金額"])
    return monthly


def update_shushi(asof: dt.date) -> int:
    """収支管理.md のマーカー区間だけを書き換える。区間外の手書きは保持。"""
    monthly = journal_monthly()
    months = sorted(monthly)
    lines = [AUTO_START,
             f"最終更新: {today().isoformat()}（weekly-kicho自動更新・{asof.month}/{asof.day}時点の明細まで）",
             "",
             "| 月 | 収入 | 経費 | 利益 |",
             "|----|------:|------:|------:|"]
    total_i = total_e = 0
    for m in months:
        i = sum(v for a, v in monthly[m].items() if a in PL_INCOME)
        e = sum(v for a, v in monthly[m].items() if a in PL_EXPENSE)
        total_i += i
        total_e += e
        lines.append(f"| {m}月 | {yen(i)} | {yen(e)} | {yen(i - e)} |")
    profit = total_i - total_e
    lines.append(f"| **累計** | **{yen(total_i)}** | **{yen(total_e)}** | **{yen(profit)}** |")

    expense_total: dict[str, int] = defaultdict(int)
    for m in months:
        for a, v in monthly[m].items():
            if a in PL_EXPENSE:
                expense_total[a] += v
    lines += ["", "| 経費科目 | 累計 |", "|------|------:|"]
    for a, v in sorted(expense_total.items(), key=lambda x: -x[1]):
        if v:
            lines.append(f"| {a} | {yen(v)} |")
    lines.append(AUTO_END)
    block = "\n".join(lines)

    text = SHUSHI.read_text(encoding="utf-8")
    if AUTO_START in text and AUTO_END in text:
        pre = text.split(AUTO_START)[0]
        post = text.split(AUTO_END, 1)[1]
        SHUSHI.write_text(pre + block + post, encoding="utf-8")
    else:  # マーカー未設置なら末尾に追加（初回のみ）
        SHUSHI.write_text(text.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    return profit


def append_daily_note(message: str, details: list[str]) -> None:
    path = DAILY_DIR / f"{today().isoformat()}.md"
    if not path.exists():
        DAILY_DIR.mkdir(parents=True, exist_ok=True)
        if DAILY_TEMPLATE.exists():
            base = DAILY_TEMPLATE.read_text(encoding="utf-8").replace("{{date}}", today().isoformat())
        else:
            base = f"# {today().isoformat()}\n\n## 💡 メモ / アイデア\n"
        path.write_text(base, encoding="utf-8")
    text = path.read_text(encoding="utf-8")
    report = "\n".join([f"- {message}"] + [f"  - {d}" for d in details if d])
    marker = "## 💡 メモ / アイデア"
    if marker in text:
        pre, post = text.split(marker, 1)
        text = pre + marker + "\n" + report + post
    else:
        text = text.rstrip() + f"\n\n{marker}\n" + report + "\n"
    path.write_text(text, encoding="utf-8")


# ================= メイン =================

def main() -> int:
    parser = argparse.ArgumentParser(description="AI帳簿 週次自動記帳 v2")
    parser.add_argument("--dry-run", action="store_true", help="取得と判定のみ。書き込みしない")
    args = parser.parse_args()

    bank_before = read_bank_rows()
    since = last_bank_date(bank_before)
    new_rows, fetch_note = fetch_freee_rows(since)

    unknown = [r for r in new_rows if classify(r) is None]
    known = [r for r in new_rows if classify(r) is not None]

    print(f"[kicho] {fetch_note} / 既知{len(known)}件・未知{len(unknown)}件")

    if args.dry_run:
        for r in unknown:
            print(f"  未知: {r['date']} {r['side']} {r['amount']} {r['description']}")
        return 0

    # 未知パターンがあれば自動計上せず停止（誤記帳ゼロ原則）
    if unknown:
        details = [f"{r['date']} {r['side']} ¥{int(r['amount']):,} 「{r['description']}」"
                   for r in unknown]
        append_daily_note(
            f"📒 週次記帳: ⏸ 要確認{len(unknown)}件あり、自動計上を停止（既知{len(known)}件も保留）。"
            "エージェントに『要確認を解消して』と伝えてください。", details + [fetch_note])
        print("UNKNOWN_PATTERNS — stopped before booking")
        return 2

    # バックアップ → 追記 → 生成・検証 → NGならロールバック
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bank_bak = BACKUP_DIR / f"bank_{stamp}.csv"
    journal_bak = BACKUP_DIR / f"journal_{stamp}.csv"
    shutil.copy2(BANK_CSV, bank_bak)
    shutil.copy2(JOURNAL, journal_bak)

    if known:
        append_bank_rows(known)
    ok, output = run_build_and_ledger()
    if not ok:
        shutil.copy2(bank_bak, BANK_CSV)
        shutil.copy2(journal_bak, JOURNAL)
        append_daily_note("📒 週次記帳: ❌ 検証エラーのためロールバックしました。"
                          "エージェントに『帳簿のログを見て』と伝えてください。", [fetch_note])
        print(output)
        return 1

    asof = last_bank_date(read_bank_rows()) or today()
    profit = update_shushi(asof)

    warnings = []
    if not new_rows and since and (today() - since).days >= 7:
        warnings.append("⚠️ 新規明細が7日以上ゼロ。freee口座連携の再同意切れの可能性"
                        "（freeeアプリ→口座→GMOあおぞら→再連携。次回目安2026年9月上旬）")

    monthly = journal_monthly()
    m = asof.month
    m_profit = (sum(v for a, v in monthly[m].items() if a in PL_INCOME)
                - sum(v for a, v in monthly[m].items() if a in PL_EXPENSE))
    msg = f"📒 週次記帳: 新規{len(known)}件 / {m}月利益{yen(m_profit)} / 累計利益{yen(profit)}"
    append_daily_note(msg, [fetch_note] + warnings)
    print(msg)
    for w in warnings:
        print(w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
