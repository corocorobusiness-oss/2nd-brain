#!/usr/bin/env python3
"""Second Brainを読み取り専用で集計するローカル経営ダッシュボード。"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
DEFAULT_VAULT = Path("~/2nd-Brain").expanduser()
DEFAULT_YOUTUBE = Path("~/Projects/youtube").expanduser()
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


def parse_freee_expenses(vault: Path, month: str, cutoff: dt.date) -> dict[str, Any]:
    snapshot = latest_freee_snapshot(vault, cutoff)
    empty = {"total": 0, "categories": [], "as_of": None, "status": "未取得", "warning": "freeeスナップショットがありません"}
    if not snapshot:
        return empty
    try:
        deals = json.loads(read_text(snapshot / "deals.json")).get("deals", [])
        items = json.loads(read_text(snapshot / "account_items.json")).get("account_items", [])
    except (OSError, ValueError):
        return empty
    names = {item.get("id"): item.get("name", "不明") for item in items}
    categories: dict[str, int] = {}
    for deal in deals:
        if deal.get("type") != "expense" or not str(deal.get("issue_date", "")).startswith(month):
            continue
        for detail in deal.get("details", []):
            if detail.get("entry_side") != "debit":
                continue
            name = names.get(detail.get("account_item_id"), "分類不明")
            categories[name] = categories.get(name, 0) + int(detail.get("amount") or 0)
    total = sum(categories.values())
    return {
        "total": total,
        "categories": [{"name": name, "amount": amount} for name, amount in sorted(categories.items(), key=lambda x: -x[1])],
        "as_of": snapshot.name,
        "status": "暫定",
        "warning": "freeeの最新ローカル取得分のみ。未同期取引は含みません",
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


def build_dashboard(vault: Path, youtube_root: Path, today: dt.date | None = None) -> dict[str, Any]:
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
    expenses = parse_freee_expenses(vault, month, cutoff)
    warnings.append(expenses["warning"])
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
            "revenue": revenue_total, "expenses": expenses["total"], "profit": revenue_total - expenses["total"],
            "target_to_date": overall_target_to_date,
            "difference_to_date": revenue_total - overall_target_to_date,
            "achievement": round(revenue_total / overall_target_to_date * 100, 1) if overall_target_to_date else None,
            "expense_categories": expenses["categories"], "expense_as_of": expenses["as_of"],
            "expense_status": expenses["status"],
        },
        "daily": daily,
        "jobs": jobs,
        "today_note": parse_today_note(vault, today),
    }


class Handler(BaseHTTPRequestHandler):
    vault = DEFAULT_VAULT
    youtube_root = DEFAULT_YOUTUBE
    fixed_today: dt.date | None = None

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/api/dashboard":
            try:
                payload = json.dumps(build_dashboard(self.vault, self.youtube_root, self.fixed_today), ensure_ascii=False).encode()
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
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--date", type=dt.date.fromisoformat, help="検証用の今日（YYYY-MM-DD）")
    parser.add_argument("--json", action="store_true", help="画面を起動せず集計JSONを表示")
    args = parser.parse_args()
    if args.json:
        print(json.dumps(build_dashboard(args.vault.expanduser(), args.youtube_root.expanduser(), args.date), ensure_ascii=False, indent=2))
        return
    Handler.vault = args.vault.expanduser()
    Handler.youtube_root = args.youtube_root.expanduser()
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
