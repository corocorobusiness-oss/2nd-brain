#!/usr/bin/env python3
"""Second Brainを読み取り専用で集計するローカル経営ダッシュボード。"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_VAULT = Path("~/2nd-Brain").expanduser()
DEFAULT_YOUTUBE = Path("~/Projects/youtube").expanduser()
DEFAULT_AGENT_SKILLS = Path("~/agent-skills").expanduser()
DEFAULT_CODEX_SKILLS = Path("~/.codex/skills").expanduser()
DEFAULT_CLAUDE_SKILLS = Path("~/.claude/skills").expanduser()
DEFAULT_EXPENSE_ROOT = Path(
    "~/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算"
).expanduser()
FREEE_TOKENS = Path("~/.config/freee-mcp/tokens.json").expanduser()
FREEE_API_BASE = "https://api.freee.co.jp/api/1"
FREEE_COMPANY_ID = 12511831
FREEE_REFRESH_SECONDS = 30 * 60
FREEE_ERROR_RETRY_SECONDS = 5 * 60
EXPENSE_FILE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".pdf", ".md"}
_FREEE_CACHE: dict[str, Any] = {"key": None, "loaded": 0.0, "data": None, "error": None}
_FREEE_CACHE_LOCK = threading.Lock()
DELIVERY_NAMES = {"Uber Eats", "Uber", "出前館", "ロケットナウ", "ロケットなう"}
YOUTUBE_NAMES = {"YouTube"}
YOUTUBE_OVERRIDES = {
    "2026-07-17": {
        "title": "毛利軍｜秀吉を追撃しなかった理由",
        "folder": "2026-07-17_毛利軍_秀吉を追撃しなかった理由",
        "predicted_views": 16457,
    }
}

JOB_LABELS = {
    "com.claude.discord-monitor": ("スマホの相談窓口", "Discordのメッセージを受け取り、あおいに届けます"),
    "com.claude.listener-watchdog": ("相談窓口の見張り", "メッセージの受信が止まっていないか見張ります"),
    "com.claude.channel-lifecycle": ("動画用チャットの整理", "制作ごとのチャットを整理する旧機能です"),
    "com.claude.youtube-revenue": ("YouTube収益の記録", "YouTube収益をデイリーノートへ記録します"),
    "com.claude.uber-earnings": ("Uber売上の記録", "その日のUber売上を集計して記録します"),
    "com.claude.daily-knowledge-extract": ("今日の学びを保存", "日誌から大事な気づきを拾って知識にします"),
    "com.claude.gmail-cleanup": ("メールの整理", "不要なメールを週に一度整理します"),
    "com.claude.weekly-accounting": ("週次の経理", "一週間分の取引をfreeeへ記録します"),
    "com.claude.weekly-stocktake": ("タスクの棚卸し", "たまったタスクから今やるものを整理します"),
    "com.claude.neta-retrain": ("動画データの学習", "動画の実績を使ってネタ予測を更新します"),
    "com.claude.uber-weekly-plan": ("来週のUber計画", "天気と過去実績から来週の稼働案を作ります"),
    "com.claude.knowledge-gardener": ("Second Brainの整理", "関連ノートをつなぎ、重複や古い情報を整理します"),
    "com.claude.corpus-collect": ("動画ネタの学習素材集め", "創作スレの文章パターンを週に一度集めます"),
    "com.claude.thread-format-learning": ("台本文体の学習", "過去台本から読みやすい書き方を学びます"),
    "com.claude.trash-cleanup": ("不要ファイルの整理", "安全に消せる一時ファイルを月に一度整理します"),
    "com.claude.demaecan-reminder": ("出前館の明細リマインド", "出前館の売上明細を忘れないよう知らせます"),
    "com.claude.monthly-accounting": ("旧・月次経理", "以前の月次経理機能です。現在は使っていません"),
    "com.korokoro.monthly-accounting-recheck": ("月次経理の再チェック", "売上とfreeeの数字が合うか別ルートで確認します"),
    "com.claude.freee-uncleared-monitor": ("freee未処理の確認", "freeeに残っている未処理の明細を確認します"),
    "com.claude.script-learning": ("台本結果の振り返り", "公開後の結果から次の台本改善案を作ります"),
    "com.claude.neta-slate-reminder": ("来月の動画予定リマインド", "来月のネタを決める時期になったら知らせます"),
    "com.claude.monthly-backup": ("月次バックアップ", "会社の大事なデータを月に一度まとめて保存します"),
    "com.claude.vault-snapshot": ("週次バックアップ", "Second Brainと売上証拠を週に一度保存します"),
    "com.claude.restore-drill": ("バックアップの復元確認", "保存したデータが本当に戻せるか確認します"),
    "com.claude.ssd-backup": ("外付けSSDへの保存", "Macが壊れても戻せるようSSDにも控えを作ります"),
    "com.korokoro.kicho-weekly": ("旧・週次記帳", "以前の記帳機能です。現在は使っていません"),
    "com.korokoro.yuma-watchtower": ("自動化の見守り役", "すべての自動化が正常か毎朝確認します"),
    "com.claude.vault-autocommit": ("Second Brainの自動保存", "変更を10分ごとに履歴として保存します"),
    "com.claude.satellite-autocommit": ("制作データの自動保存", "YouTube制作物やスキルを10分ごとに保存します"),
    "com.claude.vault-mirror": ("旧・Driveコピー", "以前のGoogle Driveコピー機能です。現在は使っていません"),
    "com.claude.youtube-drafts-ssd-mirror": ("YouTube制作物のSSD保存", "制作中の動画データをSSDにもコピーします"),
    "com.claude.nightly-refresh": ("あおいの夜間リフレッシュ", "翌朝も軽快に動けるよう、夜中に状態を整えます"),
    "com.claude.daily-dashboard": ("朝の経営レポート", "売上と今日のタスクを毎朝まとめます"),
}


def friendly_schedule(value: str) -> str:
    return (value.replace("常駐（KeepAlive）", "常に動作")
                 .replace("常駐（KeepAlive / 30秒監視）", "常に動作・30秒ごとに確認")
                 .replace("常駐", "常に動作")
                 .replace("SSDマウント時（StartOnMount）", "SSDをつないだ時"))


def friendly_job(name: str, schedule: str, group: str, raw_state: str, raw_detail: str) -> dict[str, Any]:
    label, summary = JOB_LABELS.get(name, (name.replace("com.claude.", "").replace("com.korokoro.", ""), "自動で動く社内業務です"))
    state = {"running": "順調", "watch": "確認中", "stopped": "停止中"}[group]
    return {
        "name": label,
        "summary": summary,
        "schedule": friendly_schedule(schedule),
        "state": state,
        "technical_name": name,
        "technical_state": raw_state,
        "technical_detail": raw_detail,
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def yen(value: str) -> int | None:
    value = value.strip().replace("**", "")
    if not re.search(r"\d", value):
        return None
    match = re.search(r"-?[\d,]+", value.replace("¥", "").replace("円", ""))
    return int(match.group(0).replace(",", "")) if match else None


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_sales_note(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"rows": [], "delivery": 0, "youtube": 0, "warnings": []}
    if not path.exists():
        result["exists"] = False
        result["warnings"].append("デイリーノートがありません")
        return result
    result["exists"] = True
    in_sales = False
    for line in read_text(path).splitlines():
        if line.startswith("## "):
            in_sales = "今日の売上" in line
            continue
        if not in_sales or not line.startswith("|"):
            continue
        cells = table_cells(line)
        if len(cells) < 2 or cells[0] in {"事業", "------", "合計"} or set(cells[0]) == {"-"}:
            continue
        amount = yen(cells[1])
        memo = cells[2] if len(cells) > 2 else ""
        row = {"name": cells[0], "amount": amount, "memo": memo}
        result["rows"].append(row)
        if cells[0] in DELIVERY_NAMES and amount is not None:
            result["delivery"] += amount
        if cells[0] in YOUTUBE_NAMES and amount is not None:
            result["youtube"] += amount
    delivery_rows = [r for r in result["rows"] if r["name"] in DELIVERY_NAMES]
    youtube_rows = [r for r in result["rows"] if r["name"] in YOUTUBE_NAMES]
    result["has_delivery"] = any(r["amount"] is not None for r in delivery_rows)
    result["has_youtube"] = any(r["amount"] is not None for r in youtube_rows)
    result["provisional"] = any("時点" in r["memo"] or "暫定" in r["memo"] or "暂定" in r["memo"] for r in delivery_rows)
    if not result["has_delivery"]:
        result["warnings"].append("配達売上が未取得です")
    if not result["has_youtube"]:
        result["warnings"].append("YouTube収益は未取得です（通常2〜3日遅れ）")
    return result


def parse_budget_and_schedule(path: Path, month: str) -> tuple[dict[int, int], int, list[dict[str, Any]], int]:
    text = read_text(path)
    year, mon = map(int, month.split("-"))
    budgets: dict[int, int] = {}
    in_budget = False
    for line in text.splitlines():
        if line.startswith("### "):
            in_budget = f"{year}年{mon}月 日割り計画" in line
            continue
        if in_budget and line.startswith("|"):
            cells = table_cells(line)
            if cells and re.fullmatch(r"\d{1,2}", cells[0]):
                budgets[int(cells[0])] = yen(cells[2]) or 0
    delivery_target = 0
    youtube_target = 0
    for line in text.splitlines():
        cells = table_cells(line) if line.startswith("|") else []
        if cells and cells[0] == month and len(cells) >= 5:
            delivery_target = yen(cells[1]) or 0
            youtube_target = yen(cells[3]) or 0
            break

    schedule: list[dict[str, Any]] = []
    in_schedule = False
    for line in text.splitlines():
        if line.startswith("#### "):
            in_schedule = f"{year}年{mon}月 YouTube投稿計画" in line
            continue
        if in_schedule and line.startswith("|"):
            cells = table_cells(line)
            match = re.fullmatch(r"(\d{1,2})/(\d{1,2})", cells[0]) if cells else None
            if match and int(match.group(1)) == mon:
                date = dt.date(year, mon, int(match.group(2)))
                schedule.append({
                    "date": date.isoformat(), "weekday": cells[1], "title": cells[2],
                    "predicted_views": yen(cells[3]) or 0, "goal": cells[4] if len(cells) > 4 else "",
                })
    return budgets, delivery_target, schedule, youtube_target


def latest_freee_snapshot(vault: Path, cutoff: dt.date) -> Path | None:
    root = vault / "02_経営/帳簿/freee_export"
    candidates = []
    if root.exists():
        for path in root.iterdir():
            try:
                stamp = dt.date.fromisoformat(path.name)
            except ValueError:
                continue
            if path.is_dir() and stamp <= cutoff:
                candidates.append((stamp, path))
    return max(candidates, default=(None, None))[1]


def file_timestamp(path: Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")
    except OSError:
        return None


def latest_timestamp(*values: str | None) -> str | None:
    parsed: list[tuple[dt.datetime, str]] = []
    for value in values:
        if not value:
            continue
        try:
            parsed.append((dt.datetime.fromisoformat(value), value))
        except ValueError:
            continue
    return max(parsed, default=(None, None))[1]


def normalize_merchant(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").lower()
    aliases = [
        (("eneos", "enejet", "エネオス"), "eneos"),
        (("apollo", "アポロ", "出光", "idemitsu"), "idemitsu"),
        (("anthropic", "claude"), "anthropic"),
        (("openai", "chatgpt"), "openai"),
        (("ニコニコ", "ドワンゴ", "niconico"), "dwango"),
        (("google", "グーグル"), "google"),
    ]
    for words, canonical in aliases:
        if any(word in text for word in words):
            return canonical
    text = re.sub(r"(?:株式会社|有限会社|合同会社|\(株\)|（株）|inc\.?|llc)", "", text)
    return re.sub(r"[^0-9a-zぁ-んァ-ヶ一-龠]", "", text)


def merchants_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left == right:
        return True
    return min(len(left), len(right)) >= 4 and (left in right or right in left)


def freee_api_get(access_token: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{FREEE_API_BASE}/{path}?{query}",
        headers={"Authorization": f"Bearer {access_token}", "User-Agent": "local-management-dashboard/1.0"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)


def fetch_freee_live(month: str, through_date: dt.date) -> dict[str, Any]:
    token_data = json.loads(read_text(FREEE_TOKENS))
    access_token = token_data.get("access_token")
    if not access_token:
        raise ValueError("access_token missing")

    start_date = f"{month}-01"
    common = {"company_id": FREEE_COMPANY_ID}
    deals: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = freee_api_get(access_token, "deals", {
            **common,
            "start_issue_date": start_date,
            "end_issue_date": through_date.isoformat(),
            "limit": 100,
            "offset": offset,
        }).get("deals", [])
        deals.extend(page)
        if len(page) < 100:
            break
        offset += 100

    partners: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = freee_api_get(access_token, "partners", {**common, "limit": 100, "offset": offset}).get("partners", [])
        partners.extend(page)
        if len(page) < 100:
            break
        offset += 100

    return {
        "deals": deals,
        "account_items": freee_api_get(access_token, "account_items", common).get("account_items", []),
        "partners": partners,
        "wallet_txns": freee_api_get(access_token, "wallet_txns", {**common, "limit": 100}).get("wallet_txns", []),
        "retrieved_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
    }


def cached_freee_live(month: str, through_date: dt.date) -> tuple[dict[str, Any] | None, str | None]:
    key = f"{month}:{through_date.isoformat()}"
    now = time.monotonic()
    with _FREEE_CACHE_LOCK:
        cache_seconds = FREEE_ERROR_RETRY_SECONDS if _FREEE_CACHE["error"] else FREEE_REFRESH_SECONDS
        if _FREEE_CACHE["key"] == key and now - float(_FREEE_CACHE["loaded"]) < cache_seconds:
            return _FREEE_CACHE["data"], _FREEE_CACHE["error"]
        previous = _FREEE_CACHE["data"] if _FREEE_CACHE["key"] == key else None
        try:
            data = fetch_freee_live(month, through_date)
            error = None
        except urllib.error.HTTPError as exc:
            data, error = previous, f"HTTP {exc.code}"
        except (OSError, ValueError, urllib.error.URLError, TimeoutError) as exc:
            data, error = previous, type(exc).__name__
        _FREEE_CACHE.update({"key": key, "loaded": now, "data": data, "error": error})
        return data, error


def summarize_freee_expenses(
    payload: dict[str, Any],
    month: str,
    through_date: dt.date,
    *,
    as_of: str,
    updated_at: str | None,
    source: str,
) -> dict[str, Any]:
    items = payload.get("account_items", [])
    partners = payload.get("partners", [])
    deals = payload.get("deals", [])
    wallet_txns = payload.get("wallet_txns", [])
    item_names = {item.get("id"): item.get("name", "分類不明") for item in items}
    partner_names = {partner.get("id"): partner.get("name", "") for partner in partners}
    categories: dict[str, int] = {}
    matching_deals = []
    for deal in deals:
        issue_date = str(deal.get("issue_date") or "")
        try:
            deal_date = dt.date.fromisoformat(issue_date)
        except ValueError:
            continue
        if deal.get("type") != "expense" or not issue_date.startswith(month) or deal_date > through_date:
            continue
        for detail in deal.get("details", []):
            if detail.get("entry_side") != "debit":
                continue
            name = item_names.get(detail.get("account_item_id"), "分類不明")
            categories[name] = categories.get(name, 0) + int(detail.get("amount") or 0)
        partner_name = partner_names.get(deal.get("partner_id"), "")
        merchant_reliable = bool(partner_name)
        if not partner_name:
            descriptions = [str(detail.get("description") or "") for detail in deal.get("details", [])]
            partner_name = next((value for value in descriptions if value), "")
        matching_deals.append({
            "id": deal.get("id"),
            "date": issue_date,
            "amount": int(deal.get("amount") or 0),
            "merchant": partner_name,
            "merchant_key": normalize_merchant(partner_name),
            "merchant_reliable": merchant_reliable,
        })

    wallet_dates = [
        str(row.get("date")) for row in wallet_txns
        if row.get("date") and row.get("walletable_type") == "bank_account"
    ]
    latest_bank_date = max(wallet_dates, default=None)
    bank_stale = True
    if latest_bank_date:
        try:
            bank_stale = (through_date - dt.date.fromisoformat(latest_bank_date)).days > 7
        except ValueError:
            bank_stale = True
    try:
        source_stale = (through_date - dt.date.fromisoformat(as_of[:10])).days > 1
    except ValueError:
        source_stale = True

    return {
        "available": True,
        "total": sum(categories.values()),
        "categories": [
            {"name": name, "amount": amount, "status": "確認済み"}
            for name, amount in sorted(categories.items(), key=lambda item: -item[1])
        ],
        "matching_deals": matching_deals,
        "as_of": as_of,
        "updated_at": updated_at,
        "source": source,
        "latest_bank_date": latest_bank_date,
        "stale": source_stale or bank_stale,
        "bank_stale": bank_stale,
        "latest_check_failed": False,
    }


def parse_freee_expenses(
    vault: Path,
    month: str,
    through_date: dt.date,
    allow_live: bool = False,
) -> dict[str, Any]:
    warnings = []
    live_error = None
    if allow_live:
        live, live_error = cached_freee_live(month, through_date)
        if live:
            result = summarize_freee_expenses(
                live,
                month,
                through_date,
                as_of=live["retrieved_at"][:10],
                updated_at=live["retrieved_at"],
                source="freee最新確認",
            )
            if live_error:
                warnings.append("freeeの最新確認に失敗したため、直前に確認できた数字を表示しています")
            result["latest_check_failed"] = bool(live_error)
            result["warnings"] = warnings
            return result

    snapshot = latest_freee_snapshot(vault, through_date)
    if not snapshot:
        return {
            "available": False,
            "total": 0,
            "categories": [],
            "matching_deals": [],
            "as_of": None,
            "updated_at": None,
            "source": "未取得",
            "latest_bank_date": None,
            "stale": True,
            "bank_stale": True,
            "latest_check_failed": bool(live_error),
            "warnings": ["freeeの経費データを確認できません"],
        }
    try:
        payload = {
            "deals": json.loads(read_text(snapshot / "deals.json")).get("deals", []),
            "account_items": json.loads(read_text(snapshot / "account_items.json")).get("account_items", []),
            "partners": json.loads(read_text(snapshot / "partners.json")).get("partners", []),
            "wallet_txns": json.loads(read_text(snapshot / "wallet_txns.json")).get("wallet_txns", []),
        }
    except (OSError, ValueError):
        return {
            "available": False,
            "total": 0,
            "categories": [],
            "matching_deals": [],
            "as_of": snapshot.name,
            "updated_at": None,
            "source": "未取得",
            "latest_bank_date": None,
            "stale": True,
            "bank_stale": True,
            "latest_check_failed": bool(live_error),
            "warnings": ["freeeの保存データが壊れているため、経費を確定できません"],
        }
    updated_at = latest_timestamp(*(
        file_timestamp(snapshot / name)
        for name in ("deals.json", "account_items.json", "partners.json", "wallet_txns.json")
    ))
    result = summarize_freee_expenses(
        payload,
        month,
        through_date,
        as_of=snapshot.name,
        updated_at=updated_at,
        source="freee保存データ",
    )
    if allow_live and live_error:
        result["latest_check_failed"] = True
        if live_error == "HTTP 401":
            warnings.append(f"freeeとの接続が切れているため、{snapshot.name.replace('-', '/')}の控えを表示しています")
        else:
            warnings.append(f"freeeの最新確認ができないため、{snapshot.name.replace('-', '/')}の控えを表示しています")
    result["warnings"] = warnings
    return result


def parse_drive_expenses(expense_root: Path, month: str, through_date: dt.date) -> dict[str, Any]:
    if not expense_root.exists():
        return {
            "available": False,
            "receipts": [],
            "updated_at": None,
            "unparsed_count": 0,
            "duplicate_count": 0,
        }
    year, mon = month.split("-")
    month_dir = expense_root / year / mon
    if not month_dir.exists():
        return {
            "available": True,
            "receipts": [],
            "updated_at": None,
            "unparsed_count": 0,
            "duplicate_count": 0,
        }

    receipt_pattern = re.compile(r"^(\d{8})_(.+)_((?:\d{1,3}(?:,\d{3})+)|(?:\d+))$")
    receipts = []
    unparsed_count = 0
    try:
        paths = sorted(path for path in month_dir.iterdir() if path.is_file())
    except OSError:
        return {
            "available": False,
            "receipts": [],
            "updated_at": None,
            "unparsed_count": 0,
            "duplicate_count": 0,
        }
    for path in paths:
        if path.suffix.lower() not in EXPENSE_FILE_EXTENSIONS:
            continue
        match = receipt_pattern.fullmatch(path.stem)
        if not match:
            unparsed_count += 1
            continue
        try:
            date = dt.datetime.strptime(match.group(1), "%Y%m%d").date()
            amount = int(match.group(3).replace(",", ""))
        except (ValueError, OverflowError):
            unparsed_count += 1
            continue
        if date.strftime("%Y-%m") != month or date > through_date or amount <= 0:
            continue
        merchant = unicodedata.normalize("NFKC", match.group(2)).strip()
        try:
            fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            unparsed_count += 1
            continue
        receipts.append({
            "date": date.isoformat(),
            "merchant": merchant,
            "merchant_key": normalize_merchant(merchant),
            "amount": amount,
            "updated_at": file_timestamp(path),
            "file_name": path.name,
            "fingerprint": fingerprint,
        })

    unique = {}
    for receipt in receipts:
        key = (
            receipt["date"],
            receipt["merchant_key"] or receipt["merchant"],
            receipt["amount"],
            receipt["fingerprint"],
        )
        current = unique.get(key)
        if current is None or (receipt["updated_at"] or "") > (current["updated_at"] or ""):
            unique[key] = receipt
    deduplicated = sorted(unique.values(), key=lambda row: (row["date"], row["merchant"], row["amount"]))
    for receipt in deduplicated:
        receipt.pop("fingerprint", None)
    return {
        "available": True,
        "receipts": deduplicated,
        "updated_at": latest_timestamp(*(row["updated_at"] for row in deduplicated)),
        "unparsed_count": unparsed_count,
        "duplicate_count": len(receipts) - len(deduplicated),
    }


def reconcile_expenses(freee: dict[str, Any], drive: dict[str, Any]) -> dict[str, Any]:
    receipts = drive["receipts"]
    deals = freee["matching_deals"]
    used_receipts: set[int] = set()
    used_deals: set[int] = set()
    pending = []
    ambiguous = []
    matched_count = 0

    # カード明細はレシート日より遅れるため、同額・同じ店なら3日差まで同一取引とみなす。
    # 取引先がfreeeで確認できないものは自動確定せず、次の曖昧照合へ回す。
    reliable_candidates: dict[int, list[tuple[int, int]]] = {}
    for receipt_index, receipt in enumerate(receipts):
        try:
            receipt_date = dt.date.fromisoformat(receipt["date"])
        except ValueError:
            continue
        for deal_index, deal in enumerate(deals):
            if receipt["amount"] != deal["amount"] or not deal.get("merchant_reliable"):
                continue
            if not merchants_match(receipt["merchant_key"], deal["merchant_key"]):
                continue
            try:
                date_gap = abs((receipt_date - dt.date.fromisoformat(deal["date"])).days)
            except ValueError:
                continue
            if date_gap <= 3:
                reliable_candidates.setdefault(receipt_index, []).append((date_gap, deal_index))

    # 単純な「近い順」では組める件数を減らす場合があるため、増加路で最大一対一照合にする。
    def maximum_pairs(candidates: dict[int, list[tuple[int, int]]]) -> dict[int, int]:
        deal_to_receipt: dict[int, int] = {}

        def assign_receipt(receipt_index: int, seen_deals: set[int]) -> bool:
            for _, deal_index in sorted(candidates.get(receipt_index, [])):
                if deal_index in seen_deals:
                    continue
                seen_deals.add(deal_index)
                current_receipt = deal_to_receipt.get(deal_index)
                if current_receipt is None or assign_receipt(current_receipt, seen_deals):
                    deal_to_receipt[deal_index] = receipt_index
                    return True
            return False

        for receipt_index in sorted(candidates, key=lambda index: receipts[index]["date"]):
            assign_receipt(receipt_index, set())
        return deal_to_receipt

    reliable_matches = maximum_pairs(reliable_candidates)
    used_deals.update(reliable_matches)
    used_receipts.update(reliable_matches.values())
    matched_count = len(reliable_matches)

    # 店名が分からないなど確定できない組み合わせも、同額かつ3日差以内なら二重加算せず要確認にする。
    uncertain_candidates: dict[int, list[tuple[int, int]]] = {}
    for receipt_index, receipt in enumerate(receipts):
        if receipt_index in used_receipts:
            continue
        try:
            receipt_date = dt.date.fromisoformat(receipt["date"])
        except ValueError:
            continue
        for deal_index, deal in enumerate(deals):
            if deal_index in used_deals or receipt["amount"] != deal["amount"]:
                continue
            # 両方の店名が信頼でき、明確に別店舗なら別件。ここで曖昧一致させると経費を過少計上する。
            if (
                deal.get("merchant_reliable")
                and receipt.get("merchant_key")
                and deal.get("merchant_key")
                and not merchants_match(receipt["merchant_key"], deal["merchant_key"])
            ):
                continue
            try:
                date_gap = abs((receipt_date - dt.date.fromisoformat(deal["date"])).days)
            except ValueError:
                continue
            if date_gap <= 3:
                uncertain_candidates.setdefault(receipt_index, []).append((date_gap, deal_index))
    uncertain_matches = maximum_pairs(uncertain_candidates)
    for deal_index, receipt_index in uncertain_matches.items():
        used_receipts.add(receipt_index)
        used_deals.add(deal_index)
        ambiguous.append({**receipts[receipt_index], "status": "要確認"})

    for receipt_index, receipt in enumerate(receipts):
        if receipt_index not in used_receipts:
            pending.append({**receipt, "status": "反映待ち"})

    confirmed = int(freee["total"] or 0) if freee["available"] else None
    pending_total = sum(row["amount"] for row in pending)
    pending_value = pending_total if drive["available"] else None
    if freee["available"]:
        known_total = int(confirmed or 0) + pending_total
    elif drive["available"] and pending:
        known_total = pending_total
    else:
        known_total = None
    partial = (
        not freee["available"]
        or not drive["available"]
        or freee["stale"]
        or freee.get("latest_check_failed", False)
        or bool(ambiguous)
        or bool(drive["unparsed_count"])
    )
    if not freee["available"] or not drive["available"]:
        status = "未取得あり"
    elif freee["stale"] or freee.get("latest_check_failed", False) or ambiguous or drive["unparsed_count"]:
        status = "要確認"
    elif pending:
        status = "反映待ちあり"
    else:
        status = "確認済み"

    breakdown = list(freee["categories"])
    if pending_total:
        breakdown.append({"name": "freee反映待ち", "amount": pending_total, "status": "反映待ち"})
    warnings = list(freee.get("warnings", []))
    if freee["bank_stale"]:
        if freee["latest_bank_date"]:
            warnings.append(f"freeeの銀行データは{freee['latest_bank_date'].replace('-', '/')}から更新されていません")
        else:
            warnings.append("freeeの銀行データを確認できません")
    if not drive["available"]:
        warnings.append("レシートの保存先を確認できないため、速報経費が未取得です")
    if pending:
        warnings.append(f"freee反映待ちの経費が{len(pending)}件あります")
    if ambiguous:
        warnings.append(f"同じ日・同じ金額の経費が重なり、{len(ambiguous)}件は確認が必要です")
    if drive["unparsed_count"]:
        warnings.append(f"ファイル名から金額を読めない証憑が{drive['unparsed_count']}件あります")
    if drive["duplicate_count"]:
        warnings.append(f"内容が同じレシートファイル{drive['duplicate_count']}件は二重に足していません")

    return {
        "total": known_total,
        "confirmed": confirmed,
        "pending": pending_value,
        "pending_count": len(pending),
        "matched_receipt_count": matched_count,
        "ambiguous_count": len(ambiguous),
        "unparsed_count": drive["unparsed_count"],
        "duplicate_count": drive["duplicate_count"],
        "pending_receipts": sorted(pending + ambiguous, key=lambda row: (row["date"], row["merchant"], row["amount"])),
        "breakdown": breakdown,
        "status": status,
        "partial": partial,
        "as_of": freee["as_of"],
        "source": freee["source"],
        "latest_bank_date": freee["latest_bank_date"],
        "updated_at": latest_timestamp(freee["updated_at"], drive["updated_at"]),
        "freee_updated_at": freee["updated_at"],
        "drive_updated_at": drive["updated_at"],
        "warnings": list(dict.fromkeys(warnings)),
    }


def classify_job(state: str) -> str | None:
    if "🟢" in state:
        return "running"
    if "🟡" in state:
        return "watch"
    if "🛑" in state:
        return "stopped"
    return None


def parse_jobs(path: Path) -> dict[str, Any]:
    groups = {"running": [], "watch": [], "stopped": []}
    for line in read_text(path).splitlines():
        if not re.match(r"^\|\s*com\.", line):
            continue
        cells = table_cells(line)
        state_index = next((i for i, cell in enumerate(cells) if any(mark in cell for mark in ("🟢", "🟡", "🛑"))), None)
        if state_index is None:
            continue
        group = classify_job(cells[state_index])
        if not group:
            continue
        groups[group].append(friendly_job(
            cells[0],
            cells[1] if len(cells) > 1 else "",
            group,
            cells[state_index],
            cells[state_index + 1] if state_index + 1 < len(cells) else "",
        ))
    # 台帳の詳細表外だが、既存ダッシュボード仕様で稼働中に含める2ジョブ。
    text = read_text(path)
    extras = [
        ("com.claude.nightly-refresh", "毎晩3:10・3:50", "あおいのセッションを安全にリフレッシュ"),
        ("com.claude.daily-dashboard", "毎朝4:00", "経営ダッシュボードとタスクを集約"),
    ]
    existing = {job["technical_name"] for values in groups.values() for job in values}
    for name, schedule, detail in extras:
        if name in text and name not in existing:
            groups["running"].append(friendly_job(name, schedule, "running", "🟢 稼働中", detail))
    return {"counts": {key: len(value) for key, value in groups.items()}, "groups": groups}


def youtube_stages(folder: Path | None) -> list[dict[str, Any]]:
    files = {p.name for p in folder.iterdir()} if folder and folder.exists() else set()
    rules = [
        ("企画内容を決める", lambda: "brief.json" in files),
        ("台本を作る", lambda: any(name.endswith(".csv") and "台本" in name for name in files)),
        ("タイトルと説明文を作る", lambda: "title.txt" in files and "description.txt" in files),
        ("読み方辞書を用意する", lambda: any(name.endswith(".dic") for name in files)),
        ("公開前に最終確認する", lambda: any("review" in name.lower() or "レビュー" in name for name in files)),
    ]
    stages = [{"name": name, "done": bool(check())} for name, check in rules]
    first = next((stage["name"] for stage in stages if not stage["done"]), "投稿準備完了")
    for stage in stages:
        stage["next"] = stage["name"] == first
    return stages


def enrich_schedule(schedule: list[dict[str, Any]], youtube_root: Path, cutoff: dt.date) -> list[dict[str, Any]]:
    week_start = cutoff - dt.timedelta(days=cutoff.weekday())
    week_end = week_start + dt.timedelta(days=6)
    drafts = youtube_root / "創作スレ下書き"
    result = []
    for item in schedule:
        date = dt.date.fromisoformat(item["date"])
        if not week_start <= date <= week_end:
            continue
        override = YOUTUBE_OVERRIDES.get(item["date"])
        if override:
            item = {**item, **override}
        folder = drafts / override["folder"] if override else None
        if folder is None and drafts.exists():
            candidates = sorted(drafts.glob(f"{item['date']}_*"))
            folder = candidates[0] if len(candidates) == 1 else None
        item["folder"] = str(folder) if folder and folder.exists() else None
        item["stages"] = youtube_stages(folder)
        item["completed"] = sum(stage["done"] for stage in item["stages"])
        item["total_stages"] = len(item["stages"])
        result.append(item)
    return result


def simple_task(text: str) -> str:
    rules = [
        ("出前館", "出前館の6月後半の売上明細を確認する"),
        ("A1外部レビュー", "自動チェックが正しく動いているか確認する"),
        ("vault-snapshot", "バックアップに売上明細が入っているか確認する"),
        ("corpus-collect", "動画学習の自動処理が動いたか確認する"),
        ("freeeトークン", "freeeとの接続をやり直す"),
        ("正本4ファイル", "大事な設定ファイルの確認を終える"),
        ("柱①", "AI開発の進め方が使いやすいか見直す"),
    ]
    for keyword, label in rules:
        if keyword in text:
            return label
    text = re.sub(r"\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"（[^）]{20,}）", "", text)
    return text.strip()[:70]


def parse_today_note(vault: Path, today: dt.date) -> dict[str, Any]:
    path = vault / "05_日誌" / f"{today.isoformat()}.md"
    if not path.exists():
        return {"exists": False, "sales": [], "sales_total": 0, "tasks": [], "notes": []}
    text = read_text(path)
    sales = parse_sales_note(path)
    tasks = []
    in_tasks = False
    for line in text.splitlines():
        if "<!-- tasks:start -->" in line:
            in_tasks = True
            continue
        if "<!-- tasks:end -->" in line:
            in_tasks = False
            continue
        if not in_tasks:
            continue
        match = re.match(r"^- \[([ xX])\]\s+(?:(\d{4}-\d{2}-\d{2})\s+)?(?:（(\d+)日超過）)?\s*(.+)$", line.strip())
        if not match:
            continue
        tasks.append({
            "done": match.group(1).lower() == "x",
            "due": match.group(2),
            "overdue_days": int(match.group(3)) if match.group(3) else 0,
            "title": simple_task(match.group(4)),
        })
    notes = []
    wanted = False
    for line in text.splitlines():
        if line.startswith("## "):
            wanted = "メモ / アイデア" in line or "ログ" in line
            continue
        if wanted and line.startswith("- ") and line[2:].strip():
            notes.append(line[2:].strip())
    return {
        "exists": True,
        "sales": sales["rows"],
        "sales_total": sum(row["amount"] or 0 for row in sales["rows"] if row["name"] != "YouTube"),
        "tasks": tasks[:8],
        "notes": notes[:6],
    }


def build_dashboard(
    vault: Path,
    youtube_root: Path,
    today: dt.date | None = None,
    expense_root: Path = DEFAULT_EXPENSE_ROOT,
    allow_live_freee: bool = False,
) -> dict[str, Any]:
    today = today or dt.date.today()
    cutoff = today - dt.timedelta(days=1)
    month = cutoff.strftime("%Y-%m")
    budgets, delivery_target, schedule, youtube_target = parse_budget_and_schedule(vault / "02_経営/目標と計画.md", month)
    days_in_month = calendar.monthrange(cutoff.year, cutoff.month)[1]
    daily = []
    delivery_total = youtube_total = 0
    captured_delivery = captured_youtube = 0
    warnings = []
    for day in range(1, cutoff.day + 1):
        date = dt.date(cutoff.year, cutoff.month, day)
        parsed = parse_sales_note(vault / "05_日誌" / f"{date.isoformat()}.md")
        budget = budgets.get(day, 0)
        youtube_daily_target = (
            round(youtube_target * day / days_in_month)
            - round(youtube_target * (day - 1) / days_in_month)
            if youtube_target else 0
        )
        youtube_cumulative_target = round(youtube_target * day / days_in_month) if youtube_target else 0
        youtube_actual = parsed["youtube"] if parsed.get("has_youtube") else None
        delivery_total += parsed["delivery"]
        youtube_total += parsed["youtube"]
        captured_delivery += int(bool(parsed.get("has_delivery")))
        captured_youtube += int(bool(parsed.get("has_youtube")))
        status = "未取得" if not parsed.get("has_delivery") and budget else "暫定" if parsed.get("provisional") else "確定"
        daily.append({
            "date": date.isoformat(), "day": day, "budget": budget, "delivery": parsed["delivery"],
            "difference": parsed["delivery"] - budget, "status": status, "rows": parsed["rows"],
            "youtube_target": youtube_daily_target,
            "youtube_actual": youtube_actual,
            "youtube_difference": youtube_actual - youtube_daily_target if youtube_actual is not None else None,
            "youtube_cumulative": youtube_total,
            "youtube_cumulative_target": youtube_cumulative_target,
        })
    yesterday = daily[-1] if daily else None
    if yesterday and yesterday["status"] != "確定":
        warnings.append(f"昨日（{cutoff.strftime('%-m/%-d')}）の配達売上は{yesterday['status']}です")
    if captured_youtube < cutoff.day:
        warnings.append(f"YouTube収益は{captured_youtube}/{cutoff.day}日分のみ取得済みです")
    freee_expenses = parse_freee_expenses(vault, month, today, allow_live=allow_live_freee)
    drive_expenses = parse_drive_expenses(expense_root, month, today)
    expenses = reconcile_expenses(freee_expenses, drive_expenses)
    warnings.extend(expenses["warnings"])
    budget_to_date = sum(budgets.get(day, 0) for day in range(1, cutoff.day + 1))
    youtube_calendar_target_to_date = round(youtube_target / days_in_month * cutoff.day) if youtube_target else 0
    youtube_last_day = max((row["day"] for row in daily if row["youtube_actual"] is not None), default=0)
    youtube_target_to_date = round(youtube_target / days_in_month * youtube_last_day) if youtube_target else 0
    youtube_last_date = daily[youtube_last_day - 1]["date"] if youtube_last_day else None
    revenue_total = delivery_total + youtube_total
    overall_target_to_date = budget_to_date + youtube_calendar_target_to_date
    jobs = parse_jobs(vault / "01_プロジェクト/AI自動化/導入済み.md")
    return {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="minutes"),
        "today": today.isoformat(), "cutoff": cutoff.isoformat(), "month": month,
        "warnings": warnings,
        "delivery": {
            "actual": delivery_total, "target": delivery_target, "budget_to_date": budget_to_date,
            "difference": delivery_total - budget_to_date,
            "achievement": round(delivery_total / budget_to_date * 100, 1) if budget_to_date else None,
            "captured_days": captured_delivery, "expected_days": cutoff.day, "yesterday": yesterday,
        },
        "youtube": {
            "actual": youtube_total, "target": youtube_target,
            "achievement": round(youtube_total / youtube_target * 100, 1) if youtube_target else None,
            "target_to_date": youtube_target_to_date,
            "calendar_target_to_date": youtube_calendar_target_to_date,
            "difference_to_date": youtube_total - youtube_target_to_date,
            "pace": round(youtube_total / youtube_target_to_date * 100, 1) if youtube_target_to_date else None,
            "daily_target_average": round(youtube_target / days_in_month) if youtube_target else 0,
            "last_revenue_date": youtube_last_date,
            "captured_days": captured_youtube, "expected_days": cutoff.day,
            "schedule": enrich_schedule(schedule, youtube_root, cutoff),
        },
        "finance": {
            "revenue": revenue_total,
            "expenses": expenses["total"],
            "profit": None if expenses["partial"] or expenses["total"] is None else revenue_total - expenses["total"],
            "target_to_date": overall_target_to_date,
            "difference_to_date": revenue_total - overall_target_to_date,
            "achievement": round(revenue_total / overall_target_to_date * 100, 1) if overall_target_to_date else None,
            "expense_categories": expenses["breakdown"], "expense_as_of": expenses["as_of"],
            "expense_status": expenses["status"],
            "expense_confirmed": expenses["confirmed"],
            "expense_pending": expenses["pending"],
            "expense_pending_count": expenses["pending_count"],
            "expense_pending_receipts": expenses["pending_receipts"],
            "expense_ambiguous_count": expenses["ambiguous_count"],
            "expense_unparsed_count": expenses["unparsed_count"],
            "expense_partial": expenses["partial"],
            "expense_updated_at": expenses["updated_at"],
            "expense_freee_updated_at": expenses["freee_updated_at"],
            "expense_drive_updated_at": expenses["drive_updated_at"],
            "expense_latest_bank_date": expenses["latest_bank_date"],
            "expense_source": expenses["source"],
            "expense_period_end": today.isoformat(),
        },
        "daily": daily,
        "jobs": jobs,
        "today_note": parse_today_note(vault, today),
    }


class Handler(BaseHTTPRequestHandler):
    vault = DEFAULT_VAULT
    youtube_root = DEFAULT_YOUTUBE
    expense_root = DEFAULT_EXPENSE_ROOT
    allow_live_freee = True
    fixed_today: dt.date | None = None

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/dashboard":
            try:
                payload = json.dumps(build_dashboard(
                    self.vault,
                    self.youtube_root,
                    self.fixed_today,
                    self.expense_root,
                    self.allow_live_freee,
                ), ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as exc:  # fail-close: 集計失敗を空の数字にしない
                payload = json.dumps({"error": str(exc)}, ensure_ascii=False).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            return
        if path in {"/", "/index.html"}:
            payload = read_text(HERE / "index.html").encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_error(404)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--youtube-root", type=Path, default=DEFAULT_YOUTUBE)
    parser.add_argument("--expense-root", type=Path, default=DEFAULT_EXPENSE_ROOT)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--date", type=dt.date.fromisoformat, help="検証用の今日（YYYY-MM-DD）")
    parser.add_argument("--json", action="store_true", help="画面を起動せず集計JSONを表示")
    parser.add_argument("--no-live-freee", action="store_true", help="freeeを直接確認せず、保存済みデータだけを使う")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(build_dashboard(
            args.vault.expanduser(),
            args.youtube_root.expanduser(),
            args.date,
            args.expense_root.expanduser(),
            not args.no_live_freee,
        ), ensure_ascii=False, indent=2))
        return
    Handler.vault = args.vault.expanduser()
    Handler.youtube_root = args.youtube_root.expanduser()
    Handler.expense_root = args.expense_root.expanduser()
    Handler.allow_live_freee = not args.no_live_freee
    Handler.fixed_today = args.date
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"経営ダッシュボード: http://{args.host}:{args.port}")
    print("終了: Control-C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
