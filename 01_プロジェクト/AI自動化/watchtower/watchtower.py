#!/usr/bin/env python3
"""Yuma OS Watchtower.

Daily read-only-ish health check for the Second Brain.
It may create today's daily note and append a small report, but it never deletes
files, posts externally, finalizes accounting, or creates new jobs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


VAULT = Path(__file__).resolve().parents[3]
DAILY_DIR = VAULT / "05_日誌"
DAILY_TEMPLATE = VAULT / "00_システム" / "Templates" / "Daily_Note_Template.md"
AUTOMATION_DIR = VAULT / "01_プロジェクト" / "AI自動化"
AUTOMATION_LEDGER = AUTOMATION_DIR / "導入済み.md"
HEALTH_LOG = VAULT / "06_エージェント運用" / "30_ヘルスチェック" / "ヘルスチェックログ.md"
YOUTUBE_DIR = VAULT / "01_プロジェクト" / "YouTube"
CLAUDE_SCRIPTS = Path.home() / ".claude" / "scripts"
WEEKLY_LOG = CLAUDE_SCRIPTS / "weekly_accounting.log"
REGISTRY = CLAUDE_SCRIPTS / "freee_registered_txns.json"
WATCHDOG_LOG = CLAUDE_SCRIPTS / "listener-watchdog.log"
WATCHTOWER_LOG_DIR = Path(__file__).resolve().parent / "logs"


@dataclass
class Check:
    label: str
    status: str
    message: str
    action: str | None = None


def now_jst() -> dt.datetime:
    if ZoneInfo:
        return dt.datetime.now(ZoneInfo("Asia/Tokyo"))
    return dt.datetime.now()


def yen_placeholder_left(text: str) -> bool:
    return "| Uber Eats | 円 | |" in text or "| 合計 | 円 | |" in text


def ensure_daily_note(today: dt.date, dry_run: bool) -> tuple[Path, bool]:
    path = DAILY_DIR / f"{today.isoformat()}.md"
    existed = path.exists()
    if existed or dry_run:
        return path, existed

    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    if DAILY_TEMPLATE.exists():
        body = DAILY_TEMPLATE.read_text(encoding="utf-8").replace("{{date}}", today.isoformat())
    else:
        body = f"# {today.isoformat()}\n\n## ✅ 今日のタスク\n- [ ] \n\n## 💡 メモ / アイデア\n- \n"
    path.write_text(body.rstrip() + "\n", encoding="utf-8")
    return path, existed


def check_daily_note(path: Path, existed_before: bool) -> Check:
    if not path.exists():
        return Check("デイリーノート", "warn", f"{path.name} がまだありません", "日誌を作成する")
    if not existed_before:
        return Check("デイリーノート", "info", f"{path.name} をWatchtowerが作成しました")
    return Check("デイリーノート", "ok", f"{path.name} は存在します")


def check_yesterday_sales(today: dt.date) -> Check:
    """昨日の売上が未記録のままなら指摘する（朝の時点で今日を見ても無意味なため昨日を見る）"""
    ypath = DAILY_DIR / f"{(today - dt.timedelta(days=1)).isoformat()}.md"
    if not ypath.exists():
        return Check("売上記録", "info", "昨日のデイリーノートがありません")
    if yen_placeholder_left(ypath.read_text(encoding="utf-8")):
        return Check("売上記録", "warn", "昨日の売上が未記録のままです", "昨日の売上を#お金に送って記録する")
    return Check("売上記録", "ok", "昨日の売上は記録済み")


def check_keiri(now: dt.datetime) -> Check:
    """経理: 週次ジョブ(毎週月曜9:05)のログ鮮度と処理済み台帳の健全性を見る。帳簿の正本はfreee"""
    issues = []
    if not WEEKLY_LOG.exists():
        issues.append("週次経理ログが未生成（初回は月曜9:05）")
    else:
        age_days = (now - dt.datetime.fromtimestamp(WEEKLY_LOG.stat().st_mtime, tz=now.tzinfo)).days
        if age_days >= 9:
            issues.append(f"週次経理の最終実行が{age_days}日前（月曜ジョブが止まってる可能性）")
    try:
        import json as _json
        _json.load(REGISTRY.open(encoding="utf-8"))
    except FileNotFoundError:
        issues.append("処理済み台帳(freee_registered_txns.json)が見つからない")
    except Exception:
        issues.append("処理済み台帳のJSONが壊れている")
    if issues:
        return Check("経理(freee)", "warn", " / ".join(issues), "週次経理ジョブと台帳を確認する")
    return Check("経理(freee)", "ok", "週次ジョブ・処理済み台帳とも正常")


def check_listener(now: dt.datetime) -> Check:
    """あおい(Discordリスナー)の見張り役が動いているか（5分毎更新のログ鮮度で判定）"""
    if not WATCHDOG_LOG.exists():
        return Check("あおい監視", "warn", "listener-watchdogのログがありません", "launchctl list | grep listener-watchdog で確認")
    age_min = (now - dt.datetime.fromtimestamp(WATCHDOG_LOG.stat().st_mtime, tz=now.tzinfo)).total_seconds() / 60
    if age_min > 20:
        return Check("あおい監視", "warn", f"ウォッチドッグのログが{int(age_min)}分更新されていません", "ウォッチドッグ自体の生存を確認する")
    return Check("あおい監視", "ok", "ウォッチドッグ稼働中（あおいの死活は5分毎に監視されている）")


def check_automation_ledger() -> Check:
    if not AUTOMATION_LEDGER.exists():
        return Check("自動化台帳", "warn", "導入済み.md が見つかりません", "自動化台帳を確認する")

    text = AUTOMATION_LEDGER.read_text(encoding="utf-8")
    warnings = []
    if "Yuma OS Watchtower" not in text and "yuma-watchtower" not in text:
        warnings.append("Watchtowerが台帳に未記録")
    # launchdの実態と台帳の突合（ゾンビ＝動いてるのに台帳に無い／幽霊＝台帳にあるのに動いてない）
    try:
        import subprocess
        out = subprocess.run(["launchctl", "list"], capture_output=True, text=True, timeout=10).stdout
        running = set(re.findall(r"(com\.(?:claude|korokoro)\.[A-Za-z0-9._-]+)", out))
        recorded = set(re.findall(r"(com\.(?:claude|korokoro)\.[A-Za-z0-9._-]+)", text))
        zombies = sorted(running - recorded)
        ghosts = sorted(recorded - running)
        if zombies:
            warnings.append(f"台帳未記録のジョブ: {', '.join(zombies)}")
        if ghosts:
            warnings.append(f"台帳にあるが未ロード: {', '.join(ghosts)}")
    except Exception:
        warnings.append("launchctlとの突合に失敗（手動確認推奨）")

    if warnings:
        return Check("自動化台帳", "warn", " / ".join(warnings), "導入済み.mdを実態に合わせて更新する")
    return Check("自動化台帳", "ok", f"台帳とlaunchdが一致（{len(running)}ジョブ稼働中）")


def check_youtube_tasks() -> Check:
    if not YOUTUBE_DIR.exists():
        return Check("YouTube制作", "info", "YouTubeプロジェクトフォルダがまだありません")

    tasks: list[str] = []
    for path in sorted(YOUTUBE_DIR.rglob("*.md")):
        if "制作アーカイブ" in str(path) or "制作アーカイブ" in str(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for line in text.splitlines():
            m = re.match(r"\s*-\s*\[\s*\]\s*(.+?)\s*$", line)
            if m and m.group(1).strip():
                tasks.append(f"{path.name}: {m.group(1).strip()}")

    if not tasks:
        return Check("YouTube制作", "ok", "未完了タスクの明示はありません")
    sample = " / ".join(tasks[:3])
    more = "" if len(tasks) <= 3 else f" ほか{len(tasks) - 3}件"
    return Check("YouTube制作", "info", f"未完了タスク {len(tasks)}件: {sample}{more}", "YouTubeの次アクションを1つ決める")


def build_daily_block(now: dt.datetime, checks: list[Check]) -> str:
    warn_count = sum(1 for c in checks if c.status == "warn")
    info_count = sum(1 for c in checks if c.status == "info")
    ok_count = sum(1 for c in checks if c.status == "ok")
    state = "要確認" if warn_count else "正常"

    actions = [c.action for c in checks if c.action]
    if not actions:
        actions = ["特になし"]

    lines = [
        "## 🗼 Yuma OS Watchtower",
        f"<!-- watchtower:{now.date().isoformat()}:start -->",
        f"- 実行: {now.strftime('%H:%M')}",
        f"- 状態: {state}（OK {ok_count} / 注意 {warn_count} / 情報 {info_count}）",
        "- チェック結果:",
    ]
    for c in checks:
        icon = {"ok": "OK", "warn": "注意", "info": "情報"}.get(c.status, c.status)
        lines.append(f"  - {icon}: {c.label} - {c.message}")
    lines.append("- 今日見ること:")
    for action in actions:
        lines.append(f"  - [ ] {action}")
    lines.append(f"<!-- watchtower:{now.date().isoformat()}:end -->")
    return "\n".join(lines) + "\n"


def upsert_daily_block(path: Path, now: dt.datetime, block: str, dry_run: bool) -> None:
    if dry_run:
        return
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    start = f"<!-- watchtower:{now.date().isoformat()}:start -->"
    end = f"<!-- watchtower:{now.date().isoformat()}:end -->"
    pattern = re.compile(rf"\n?## 🗼 Yuma OS Watchtower\n{re.escape(start)}.*?{re.escape(end)}\n?", re.S)
    if start in text and end in text:
        text = pattern.sub("\n" + block, text).rstrip() + "\n"
    else:
        text = text.rstrip() + "\n\n" + block
    path.write_text(text, encoding="utf-8")


def append_health_log(now: dt.datetime, checks: list[Check], dry_run: bool) -> None:
    if dry_run:
        return
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    warn_count = sum(1 for c in checks if c.status == "warn")
    heading = f"## {now.date().isoformat()}"
    lines = [
        "",
        heading,
        f"- 実行: {now.strftime('%H:%M:%S')}",
        f"- 状態: {'要確認' if warn_count else '正常'}",
    ]
    for c in checks:
        lines.append(f"- {c.status.upper()} {c.label}: {c.message}")
    HEALTH_LOG.write_text(
        (HEALTH_LOG.read_text(encoding="utf-8") if HEALTH_LOG.exists() else "# AIエージェント ヘルスチェックログ\n")
        .rstrip() + "\n" + "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def append_runtime_log(now: dt.datetime, checks: list[Check], dry_run: bool) -> None:
    if dry_run:
        return
    WATCHTOWER_LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{now.isoformat()} " + " | ".join(f"{c.status}:{c.label}" for c in checks) + "\n"
    with (WATCHTOWER_LOG_DIR / "watchtower.log").open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    now = now_jst()
    daily_path, existed_before = ensure_daily_note(now.date(), args.dry_run)
    checks = [
        check_daily_note(daily_path, existed_before),
        check_yesterday_sales(now.date()),
        check_keiri(now),
        check_listener(now),
        check_automation_ledger(),
        check_youtube_tasks(),
    ]

    block = build_daily_block(now, checks)
    upsert_daily_block(daily_path, now, block, args.dry_run)
    append_health_log(now, checks, args.dry_run)
    append_runtime_log(now, checks, args.dry_run)

    if args.dry_run:
        print(block)
    else:
        print(f"Watchtower OK: {daily_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
