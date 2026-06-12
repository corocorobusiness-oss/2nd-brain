#!/usr/bin/env python3
"""AI帳簿 週次記帳ジョブ weekly-kicho.

できること:
- inbox に置かれた新規銀行明細CSVを本体CSVへ安全に追記
- 仕訳帳を再生成し、ledger.py で検証
- 02_経営/収支管理.md を更新
- 当日のデイリーノートへ実行結果を追記

freee MCP/API 取得部分は、このCodex環境で freee ツールが使えるようになった後に
fetch_freee_rows() へ接続する。現状はCSV投入フォールバックで同じ記帳処理を回す。
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
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
VAULT = BASE.parents[1]
BANK_CSV = BASE / "data" / "2026_銀行明細_GMOあおぞら.csv"
INBOX = BASE / "inbox"
JOURNAL = BASE / "2026_仕訳帳.csv"
README = BASE / "README.md"
LEDGER = BASE / "scripts" / "ledger.py"
BUILD = BASE / "scripts" / "build_2026_journal.py"
SHUSHI = VAULT / "02_経営" / "収支管理.md"
DAILY_DIR = VAULT / "05_日誌"
DAILY_TEMPLATE = VAULT / "00_システム" / "Templates" / "Daily_Note_Template.md"

PL_INCOME = {"売上高", "雑収入"}
PL_EXPENSE = {"研修費", "通信費", "車両費", "消耗品費", "支払手数料", "減価償却費"}
EXPENSE_ORDER = ["研修費", "通信費", "車両費", "消耗品費", "支払手数料", "減価償却費"]


def today_jst() -> dt.date:
    return dt.datetime.now().date()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_csv_rows(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def bank_key(row: dict[str, str]) -> tuple[str, str, str, str, str]:
    return (
        row.get("date", ""),
        row.get("side", ""),
        str(row.get("amount", "")),
        str(row.get("balance", "")),
        row.get("description", ""),
    )


def last_bank_date(rows: list[dict[str, str]]) -> dt.date | None:
    dates = [r.get("date", "") for r in rows if r.get("date")]
    if not dates:
        return None
    return dt.date.fromisoformat(max(dates))


def normalize_pattern(text: str) -> list[str]:
    text = re.sub(r"（.*?）", "", text)
    text = text.replace("・", " / ")
    text = text.replace("、", " / ")
    text = text.replace(" 入金", "")
    out = []
    for token in text.split("/"):
        token = token.strip()
        if token:
            out.append(token)
    return out


def load_known_patterns_from_readme() -> dict[str, list[str]]:
    """READMEの仕訳ルール表から、side別の既知明細パターンを読む。

    会計ロジックはREADMEを正として使う。ここでは未知明細を止めるための
    パターン判定だけ行い、仕訳生成は既存 build_2026_journal.py に任せる。
    """
    text = README.read_text(encoding="utf-8")
    patterns = {"income": [], "expense": []}
    in_table = False
    for line in text.splitlines():
        if line.startswith("| 明細パターン |"):
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if line.startswith("|---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        pat, journal = cells[0], cells[1]
        side = "income" if "(借)普通預金" in journal else "expense"
        patterns[side].extend(normalize_pattern(pat))

    # READMEの表記ゆれに対する補助。帳簿READMEのルールに含まれる「出光」を
    # 銀行明細の英字表記でも止めないための同義語。
    if "出光" in patterns["expense"] and "IDEMITSU" not in patterns["expense"]:
        patterns["expense"].append("IDEMITSU")
    return patterns


def is_known_row(row: dict[str, str], patterns: dict[str, list[str]]) -> bool:
    side = row.get("side", "")
    desc = row.get("description", "")
    if side not in patterns:
        return False
    return any(pat and pat in desc for pat in patterns[side])


def load_inbox_rows(existing_last_date: dt.date | None) -> tuple[list[dict[str, str]], list[Path]]:
    rows: list[dict[str, str]] = []
    used_files: list[Path] = []
    if not INBOX.exists():
        return rows, used_files
    for path in sorted(INBOX.glob("*.csv")):
        file_rows = read_csv_rows(path)
        if not file_rows:
            continue
        used_files.append(path)
        for row in file_rows:
            if not row.get("date"):
                continue
            row_date = dt.date.fromisoformat(row["date"])
            if existing_last_date and row_date <= existing_last_date:
                continue
            rows.append(row)
    return rows, used_files


# ---- freee API 直接取得（エージェント/MCP不要・トークンはfreee-mcpと共有） ----
FREEE_CONFIG_DIR = Path.home() / ".config" / "freee-mcp"
FREEE_TOKEN_URL = "https://accounts.secure.freee.co.jp/public_api/token"
FREEE_API_BASE = "https://api.freee.co.jp"
GMO_WALLETABLE_ID = 4635538  # GMOあおぞらネット銀行（API）

# 銀行明細の表記ゆれ → 帳簿の正規表記（NFKC正規化後に適用。仕訳ルールにマッチさせるため）
DESC_REPLACEMENTS = [
    ("グ-グル", "グーグル"),
    ("アポロステ-シヨン", "アポロステーション"),
    ("キヤツシユバツク", "キャッシュバック"),
    ("デビツト", "デビット"),
    ("ネツト", "ネット"),
]


def normalize_description(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    for old, new in DESC_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def _expires_to_epoch_sec(value) -> float:
    """tokens.json の expires_at（ms/sec/ISOいずれか）を epoch秒に解釈する。"""
    if isinstance(value, (int, float)):
        v = float(value)
        return v / 1000.0 if v > 1e12 else v
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _make_expires_at(old_value, created_sec: float, expires_in: float):
    """既存のexpires_atと同じ型・スケールで新しい値を作る（freee-mcpとの互換維持）。"""
    exp = created_sec + expires_in
    if isinstance(old_value, (int, float)):
        return int(exp * 1000) if float(old_value) > 1e12 else int(exp)
    return dt.datetime.fromtimestamp(exp).astimezone().isoformat()


def _save_tokens(path: Path, tokens: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(tokens, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    os.chmod(path, 0o600)


def _refresh_freee_tokens(config: dict, tokens: dict, tokens_path: Path) -> dict:
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
    new_tokens = dict(tokens)
    new_tokens.update({
        "access_token": body["access_token"],
        "refresh_token": body.get("refresh_token", tokens["refresh_token"]),
        "token_type": body.get("token_type", tokens.get("token_type", "bearer")),
        "scope": body.get("scope", tokens.get("scope", "")),
        "expires_at": _make_expires_at(tokens.get("expires_at"), created, float(body.get("expires_in", 21600))),
    })
    _save_tokens(tokens_path, new_tokens)
    return new_tokens


def _freee_get(path: str, params: dict, tokens: dict) -> dict:
    url = f"{FREEE_API_BASE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tokens['access_token']}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def fetch_freee_rows(since: dt.date | None) -> tuple[list[dict[str, str]], str]:
    """freee APIから銀行明細(wallet_txns)を直接取得し、BANK_CSVと同じ列形式へ変換する。

    認証は freee-mcp と共有の ~/.config/freee-mcp/{config,tokens}.json を使用。
    期限切れならリフレッシュして同ファイルへ保存（トークンローテーション互換）。
    失敗してもジョブ全体は止めず、空リスト＋警告メッセージを返す（inbox CSVは処理される）。
    """
    config_path = FREEE_CONFIG_DIR / "config.json"
    tokens_path = FREEE_CONFIG_DIR / "tokens.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    except Exception as e:
        return [], f"⚠️ freee認証情報を読めない（{e}）→ inbox CSVのみ処理"

    company_id = config.get("currentCompanyId") or config.get("defaultCompanyId")
    try:
        if _expires_to_epoch_sec(tokens.get("expires_at")) < time.time() + 120:
            tokens = _refresh_freee_tokens(config, tokens, tokens_path)
    except Exception as e:
        return [], f"⚠️ freeeトークン更新失敗（{e}）。口座連携の再同意切れの可能性 → inbox CSVのみ処理"

    start = (since or dt.date(2026, 1, 1)).isoformat()
    end = today_jst().isoformat()
    txns: list[dict] = []
    try:
        offset = 0
        while True:
            params = {
                "company_id": company_id,
                "walletable_type": "bank_account",
                "walletable_id": GMO_WALLETABLE_ID,
                "start_date": start,
                "end_date": end,
                "limit": 100,
                "offset": offset,
            }
            try:
                body = _freee_get("/api/1/wallet_txns", params, tokens)
            except urllib.error.HTTPError as he:
                if he.code == 401 and offset == 0:
                    tokens = _refresh_freee_tokens(config, tokens, tokens_path)
                    body = _freee_get("/api/1/wallet_txns", params, tokens)
                else:
                    raise
            page = body.get("wallet_txns", [])
            txns.extend(page)
            if len(page) < 100:
                break
            offset += 100
    except Exception as e:
        return [], f"⚠️ freee明細取得失敗（{e}）。口座連携の再同意切れの可能性 → inbox CSVのみ処理"

    rows = []
    for t in txns:
        rows.append({
            "date": t.get("date", ""),
            "side": t.get("entry_side", ""),
            "amount": str(t.get("amount", "")),
            "balance": str(t.get("balance", "")),
            "status": "registered" if t.get("status") == 2 else "pending",
            "description": normalize_description(t.get("description", "")),
        })

    # 既存CSVとの重複排除は (date, side, amount, balance) で行う
    # （説明文は銀行表記ゆれの正規化差があるためキーに含めない。残高つきなので実質一意）
    existing = read_csv_rows(BANK_CSV)
    seen = {(r.get("date", ""), r.get("side", ""), str(r.get("amount", "")), str(r.get("balance", ""))) for r in existing}
    fresh = [r for r in rows if (r["date"], r["side"], r["amount"], r["balance"]) not in seen]
    latest = max((r["date"] for r in rows), default="なし")
    return fresh, f"freee APIから取得: 新規{len(fresh)}件（明細最終日: {latest}）"


def append_new_bank_rows(new_rows: list[dict[str, str]]) -> int:
    existing = read_csv_rows(BANK_CSV)
    fieldnames = ["date", "side", "amount", "balance", "status", "description"]
    seen = {bank_key(r) for r in existing}
    added = []
    for row in new_rows:
        normalized = {k: str(row.get(k, "")).strip() for k in fieldnames}
        if bank_key(normalized) in seen:
            continue
        seen.add(bank_key(normalized))
        added.append(normalized)
    if not added:
        return 0
    merged = existing + added
    merged.sort(key=lambda r: (r["date"], r.get("description", ""), int(r.get("amount", "0") or 0)))
    write_csv_rows(BANK_CSV, merged, fieldnames)
    return len(added)


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def run_build_and_ledger() -> tuple[bool, str]:
    build = run_command([sys.executable, str(BUILD)], BASE)
    ledger = run_command([sys.executable, str(LEDGER)], BASE)
    ok = build.returncode == 0 and ledger.returncode == 0 and "❌" not in ledger.stdout
    return ok, f"--- build_2026_journal.py ---\n{build.stdout}\n--- ledger.py ---\n{ledger.stdout}"


def journal_monthly() -> tuple[dict[int, dict[str, int]], dict[str, int]]:
    monthly: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    expense_total: dict[str, int] = defaultdict(int)
    with JOURNAL.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            month = int(r["日付"][5:7])
            dr, cr = r["借方科目"], r["貸方科目"]
            dr_amt, cr_amt = int(r["借方金額"]), int(r["貸方金額"])
            if dr in PL_EXPENSE:
                monthly[month][dr] += dr_amt
                expense_total[dr] += dr_amt
            if dr in PL_INCOME:
                monthly[month][dr] -= dr_amt
            if cr in PL_INCOME:
                monthly[month][cr] += cr_amt
            if cr in PL_EXPENSE:
                monthly[month][cr] -= cr_amt
                expense_total[cr] -= cr_amt
    return monthly, expense_total


def yen(n: int) -> str:
    return f"¥{n:,}"


def update_shushi(last_date: dt.date) -> tuple[int, int, int]:
    monthly, expense_total = journal_monthly()
    months = sorted(monthly)
    rows = []
    total_income = total_expense = total_profit = 0
    for m in months:
        income = sum(monthly[m].get(a, 0) for a in PL_INCOME)
        expense = sum(monthly[m].get(a, 0) for a in PL_EXPENSE)
        profit = income - expense
        total_income += income
        total_expense += expense
        total_profit += profit
        memo = ""
        if m == 4:
            memo = "AdSense ¥38,246含む（freee計上漏れを補正）"
        elif m == 5:
            memo = "AdSense ¥28,041含む（同上）"
        elif m == last_date.month:
            memo = f"{last_date.month}/{last_date.day}時点"
        rows.append(f"| {m}月 | {yen(income)} | {yen(expense)} | {yen(profit)} | {memo} |")
    rows.append(f"| **累計** | **{yen(total_income)}** | **{yen(total_expense)}** | **{yen(total_profit)}** | {last_date.month}/{last_date.day}時点 |")

    expense_lines = []
    for acct in EXPENSE_ORDER:
        amount = expense_total.get(acct, 0)
        if amount:
            expense_lines.append(f"| {acct} | {yen(amount)} |")
    expense_lines.append(f"| **合計** | **{yen(total_expense)}** |")

    existing = SHUSHI.read_text(encoding="utf-8") if SHUSHI.exists() else ""
    confirm = ""
    memo = ""
    if "## 確認事項" in existing:
        confirm = "## 確認事項" + existing.split("## 確認事項", 1)[1]
        if "## メモ" in confirm:
            confirm, memo_tail = confirm.split("## メモ", 1)
            memo = "## メモ" + memo_tail
    if not confirm:
        confirm = """## 確認事項

- [ ] メルカリ購入の備品（6/10・¥21,343）の品名を教えてもらい仕訳帳に追記
- [ ] 車両運搬具（¥1,032,986・中古軽自動車）の取得日・初度登録年月 → 減価償却計算に必要（年末まで）
- [ ] freee口座連携の再同意（90日ごと・次回2026年9月上旬目安）
"""
    if not memo:
        memo = """## メモ

- 免税事業者（消費税申告を前提に話を進めない）
- 申告: 青色65万円控除。確定申告書等作成コーナー（無料）からe-Tax送信
- (株)コロコロへの貸付金: ¥451,400（短期貸付金）
"""

    content = f"""# 収支管理

**2026-06-10より「AI帳簿」（`02_経営/帳簿/`）が正式な帳簿。** freee会計からは移行済み（経緯・運用ルールは [帳簿/README.md](帳簿/README.md) を参照）。

- **更新方法**: 「記帳して」または週次自動記帳 → freee/APIまたは銀行CSVから明細取得 → 仕訳追記＋検証＋下表更新
- 検証済み: freee試算表と全項目照合一致（差異はfreee側の記帳漏れ補正のみ）

最終更新: {today_jst().isoformat()}（AI帳簿 weekly-kicho）

## 月次サマリー（2026年・AI帳簿）

| 月 | 収入 | 経費 | 利益 | メモ |
|----|------:|------:|------:|------|
{chr(10).join(rows)}

詳細な月次内訳・B/S・検証結果: [帳簿/レポート/2026_試算表.md](帳簿/レポート/2026_試算表.md)

## 経費内訳（2026年累計・{last_date.month}/{last_date.day}まで）

| 科目 | 累計 |
|------|------:|
{chr(10).join(expense_lines)}

{confirm.strip()}

{memo.strip()}
"""
    SHUSHI.write_text(content + "\n", encoding="utf-8")
    return total_income, total_expense, total_profit


def ensure_daily_note(day: dt.date) -> Path:
    path = DAILY_DIR / f"{day.isoformat()}.md"
    if path.exists():
        return path
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    if DAILY_TEMPLATE.exists():
        text = DAILY_TEMPLATE.read_text(encoding="utf-8").replace("{{date}}", day.isoformat())
    else:
        text = f"# {day.isoformat()}\n\n## 💡 メモ / アイデア\n- \n"
    path.write_text(text, encoding="utf-8")
    return path


def append_daily_report(message: str, details: list[str] | None = None) -> None:
    path = ensure_daily_note(today_jst())
    text = path.read_text(encoding="utf-8")
    report_lines = [f"- {message}"]
    if details:
        report_lines.extend([f"  - {d}" for d in details])
    report = "\n".join(report_lines)

    if "## 💡 メモ / アイデア" in text:
        parts = text.split("## 💡 メモ / アイデア", 1)
        text = parts[0] + "## 💡 メモ / アイデア\n" + report + "\n" + parts[1].lstrip("\n")
    else:
        text = text.rstrip() + "\n\n## 💡 メモ / アイデア\n" + report + "\n"
    path.write_text(text, encoding="utf-8")


def archive_inbox_files(files: list[Path]) -> None:
    if not files:
        return
    archive = INBOX / "processed"
    archive.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    for path in files:
        shutil.move(str(path), str(archive / f"{path.stem}_{stamp}{path.suffix}"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="検証のみ。CSVやレポートを書き換えない")
    args = parser.parse_args()

    before_bank = read_csv_rows(BANK_CSV)
    before_last = last_bank_date(before_bank)
    patterns = load_known_patterns_from_readme()

    freee_rows, fetch_note = fetch_freee_rows(before_last)
    inbox_rows, inbox_files = load_inbox_rows(before_last)
    candidate_rows = freee_rows + inbox_rows

    unknown = [r for r in candidate_rows if not is_known_row(r, patterns)]
    if unknown:
        details = [f"{r.get('date')} {r.get('side')} {r.get('amount')} {r.get('description')}" for r in unknown]
        if not args.dry_run:
            append_daily_report(f"📒 週次記帳: 要確認{len(unknown)}件。未知の明細パターンのため自動計上を停止。", details)
        print("UNKNOWN_ROWS")
        print("\n".join(details))
        return 2

    if args.dry_run:
        print(f"DRY RUN: candidate_rows={len(candidate_rows)} / {fetch_note}")
        return 0

    backup_dir = BASE / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    bank_backup = backup_dir / f"2026_銀行明細_GMOあおぞら_{backup_stamp}.csv"
    journal_backup = backup_dir / f"2026_仕訳帳_{backup_stamp}.csv"
    shutil.copy2(BANK_CSV, bank_backup)
    shutil.copy2(JOURNAL, journal_backup)

    added = append_new_bank_rows(candidate_rows)
    ok, output = run_build_and_ledger()
    if not ok:
        shutil.copy2(bank_backup, BANK_CSV)
        shutil.copy2(journal_backup, JOURNAL)
        append_daily_report("📒 週次記帳: 検証エラー。帳簿の自動更新を確認してください。")
        print(output)
        return 1

    after_bank = read_csv_rows(BANK_CSV)
    after_last = last_bank_date(after_bank) or before_last or today_jst()
    total_income, total_expense, total_profit = update_shushi(after_last)
    archive_inbox_files(inbox_files)

    warnings = []
    if added == 0 and before_last and (today_jst() - before_last).days >= 7:
        warnings.append("freee口座連携の再同意切れの可能性（次回目安: 2026年9月上旬。freeeアプリで「口座→GMOあおぞら→再連携」）")

    msg = f"📒 週次記帳: 新規{added}件・{after_last.month}月利益{yen(sum(journal_monthly()[0][after_last.month].get(a, 0) for a in PL_INCOME) - sum(journal_monthly()[0][after_last.month].get(a, 0) for a in PL_EXPENSE))} / 累計利益{yen(total_profit)}"
    details = [fetch_note] + warnings
    append_daily_report(msg, [d for d in details if d])
    print(msg)
    if warnings:
        print("\n".join(warnings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
