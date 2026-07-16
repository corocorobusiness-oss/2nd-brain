#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIシステムダッシュボードHTML 自動生成

vaultの正本md群からタスク・期日・今日のデイリーノート・自動化ジョブ数を読み取り、
テンプレート（dashboard_template.html）に差し込んで
`06_エージェント運用/00_司令塔/AIシステムダッシュボード.html` を書き出す。

- 依存: Python 3.9+ 標準ライブラリのみ
- 読み取り専用（書き込むのは出力HTML 1ファイルだけ）
- 使い方: python3 generate_dashboard_html.py [vaultルート]  # 省略時 ~/2nd-Brain
- 仕様書: 00_システム/20_Agent_Portable/specs/dashboard-html-autogen.md
"""

import datetime
import html
import re
import sys
from pathlib import Path

TEMPLATE_NAME = "dashboard_template.html"
OUTPUT_REL = "06_エージェント運用/00_司令塔/AIシステムダッシュボード.html"
BOARD_REL = "06_エージェント運用/00_司令塔/タスクボード.md"
DEADLINE_REL = "06_エージェント運用/00_司令塔/期日タスク.md"
LEDGER_REL = "01_プロジェクト/AI自動化/導入済み.md"
DIARY_DIR_REL = "05_日誌"

STATE_EMOJIS = ("🟢", "🟡", "🛑")
# 台帳の詳細表に載らない常駐2本（載るようになったらここを空にする）
EXTRA_GREEN_LABELS = ("com.claude.nightly-refresh", "com.claude.daily-dashboard")


def strip_md(text: str) -> str:
    """wikiリンク・強調・行末の出典リンクを落として素のテキストにする"""
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"\s*←.*$", "", text)  # 「← 出典」以降は表示しない
    return text.strip()


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section_lines(text: str, heading_prefix: str):
    """指定見出し（前方一致）から次の同レベル見出しまでの行を返す"""
    lines = text.splitlines()
    out, inside = [], False
    for line in lines:
        if line.startswith("## "):
            if inside:
                break
            inside = line[3:].strip().startswith(heading_prefix)
            continue
        if inside:
            out.append(line)
    return out


def parse_thisweek(board_path: Path, limit: int = 6):
    """タスクボード「📌 今週やる」の箇条書き（表示専用）"""
    items = []
    try:
        for line in section_lines(read(board_path), "📌 今週やる"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            body = line[2:].strip()
            if body.startswith(("✅", "[x]", "[-]")):
                continue
            body = body.removeprefix("⬜").strip()
            items.append(strip_md(body))
    except OSError:
        return None
    return items[:limit]


def parse_deadlines(deadline_path: Path, today: datetime.date, limit: int = 8):
    """期日タスク（- [ ] YYYY-MM-DD 本文）を期日順に。(日付, 本文, 印) のリスト"""
    items = []
    try:
        text = read(deadline_path)
    except OSError:
        return None, 0
    for line in text.splitlines():
        m = re.match(r"^\s*[-*] \[ \] (\d{4})-(\d{2})-(\d{2})\s+(.+)$", line)
        if not m:
            continue
        d = datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        body = strip_md(re.sub(r"[（(].{40,}[)）]", "", m.group(4)))  # 長い括弧注は省く
        if d < today:
            mark = "🔴 期限切れ"
        elif (d - today).days <= 7:
            mark = "🟡 今週"
        else:
            mark = ""
        items.append((d, body[:80], mark))
    items.sort(key=lambda x: x[0])
    return items[:limit], max(0, len(items) - limit)


def parse_daily_note(vault: Path, today: datetime.date, limit: int = 5):
    """今日のデイリーノートのメモ欄（思いつきメモ / Inbox）を抜粋"""
    path = vault / DIARY_DIR_REL / f"{today.isoformat()}.md"
    if not path.exists():
        return None
    bullets, inside = [], False
    for line in read(path).splitlines():
        if re.match(r"^#{1,4} ", line):
            inside = ("思いつきメモ" in line) or ("Inbox" in line)
            continue
        if inside and line.strip().startswith("- "):
            bullets.append(strip_md(line.strip()[2:]))
    return bullets[:limit]


def parse_job_counts(ledger_path: Path):
    """台帳の詳細表（| com.xxx | ... |）から 🟢/🟡/🛑 を数える。失敗時 None"""
    try:
        text = read(ledger_path)
    except OSError:
        return None
    counts = {e: 0 for e in STATE_EMOJIS}
    rows = 0
    for line in text.splitlines():
        if not re.match(r"^\|\s*com\.", line):
            continue
        rows += 1
        for cell in line.split("|"):
            hit = next((e for e in STATE_EMOJIS if e in cell), None)
            if hit:
                counts[hit] += 1
                break
    for label in EXTRA_GREEN_LABELS:
        if label in text:
            counts["🟢"] += 1
            rows += 1
    if rows < 10:  # 台帳の形式が変わった等。嘘の数字を出すより出さない
        return None
    return counts["🟢"], counts["🟡"], counts["🛑"], rows


def build_tasks_html(thisweek, deadlines, deadline_rest, daily, today):
    li_week = "".join(f"<li>{esc(t)}</li>" for t in (thisweek or [])) or "<li>（読み取れなかった）</li>"
    li_dead = "".join(
        f'<li><b>{d.strftime("%m/%d")}</b> {esc(t)}'
        + (f' <span class="due">{m}</span>' if m else "")
        + "</li>"
        for d, t, m in (deadlines or [])
    ) or "<li>期日つきタスクはゼロ！</li>"
    rest = f'<li>…ほか{deadline_rest}件（期日タスク.md）</li>' if deadline_rest else ""
    if daily is None:
        daily_html = "今日はまだ作られていない（Obsidianで開くと自動作成／Discordで「メモ: ◯◯」でも入る）"
    elif not daily:
        daily_html = "作成済み。メモはまだなし（Discordで「メモ: ◯◯」）"
    else:
        daily_html = "<ul>" + "".join(f"<li>{esc(b)}</li>" for b in daily) + "</ul>"
    return f"""  <h2>📋 今日のタスク<span class="sub">完了操作はDiscordで「済: ◯◯」（期日タスクはObsidianでチェックも可）</span></h2>
  <div class="cats">
    <div class="cat">
      <h3>📌 今週やる（タスクボードより）</h3>
      <ul>{li_week}</ul>
    </div>
    <div class="cat">
      <h3>⏰ 期日つき（期日順）</h3>
      <ul>{li_dead}{rest}</ul>
    </div>
  </div>
  <div class="cat" style="margin-top:12px;">
    <h3>📓 今日のデイリーノート（{today.strftime("%m/%d")}）</h3>
    <div style="font-size:13px; color:var(--ink2);">{daily_html}</div>
  </div>
"""


def main():
    vault = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("~/2nd-Brain").expanduser()
    if not (vault / "CLAUDE.md").exists():
        sys.exit(f"vaultが見つからない: {vault}")
    today = datetime.date.today()

    template = read(Path(__file__).resolve().parent / TEMPLATE_NAME)

    thisweek = parse_thisweek(vault / BOARD_REL)
    deadlines, rest = parse_deadlines(vault / DEADLINE_REL, today)
    daily = parse_daily_note(vault, today)
    counts = parse_job_counts(vault / LEDGER_REL)

    out = template.replace("{{GENERATED_AT}}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    if counts:
        good, watch, stop, total = counts
        values = {"N_GOOD": str(good), "N_WATCH": str(watch), "N_STOP": str(stop), "N_TOTAL": str(total)}
    else:
        values = {"N_GOOD": "—", "N_WATCH": "—", "N_STOP": "—", "N_TOTAL": "—"}
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    out = out.replace("{{TASKS_HTML}}", build_tasks_html(thisweek, deadlines, rest, daily, today))

    if "{{" in out:
        sys.exit("テンプレートに未解決のプレースホルダが残っている")
    dest = vault / OUTPUT_REL
    dest.write_text(out, encoding="utf-8")
    print(f"OK: {dest} ({dest.stat().st_size} bytes) 今週={len(thisweek or [])} 期日={len(deadlines or [])} counts={counts}")


if __name__ == "__main__":
    main()
