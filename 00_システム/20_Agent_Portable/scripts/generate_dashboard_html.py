#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AIシステムダッシュボードHTML 自動生成（AI Company OS風・ダークUI）

vaultの正本md群から お金（予算vs実績・freee数字）・YouTube運営・タスク・期日・
デイリーノート・自動化ジョブ数 を読み取り、テンプレート（dashboard_template.html）に
差し込んで `06_エージェント運用/00_司令塔/AIシステムダッシュボード.html` を書き出す。

- 依存: Python 3.9+ 標準ライブラリのみ
- 読み取り専用（書き込むのは出力HTML 1ファイルだけ）
- 使い方: python3 generate_dashboard_html.py [vaultルート]  # 省略時 ~/2nd-Brain
- 仕様書: 00_システム/20_Agent_Portable/specs/dashboard-html-autogen.md

データ源:
- 予算: 02_経営/目標と計画.md「月間目標・実績」の当月行
- 事業別実績: 05_日誌/*.md「今日の売上」表（Uber Eats/出前館/ロケットナウ=デリバリー、YouTube）
- freee帳簿数字: デイリーノートの dashboard:start ブロック（朝4:00ジョブがfreee APIで記入。
  当月分が空の場合は直近の記入済みブロックを日付付きで表示し、停止警告を出す）
- YouTube運営: 06_エージェント運用/00_司令塔/YouTube週間ボード.md ＋ 来月ネタ草案_YYYY-MM.md ＋ タスクボード📺節
- タスク: タスクボード📌今週やる ＋ 期日タスク.md
- ジョブ数: 01_プロジェクト/AI自動化/導入済み.md
"""

import calendar
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
GOALS_REL = "02_経営/目標と計画.md"
YTBOARD_REL = "06_エージェント運用/00_司令塔/YouTube週間ボード.md"
SLATE_REL_FMT = "06_エージェント運用/00_司令塔/来月ネタ草案_{ym}.md"
DIARY_DIR_REL = "05_日誌"

STATE_EMOJIS = ("🟢", "🟡", "🛑")
EXTRA_GREEN_LABELS = ("com.claude.nightly-refresh", "com.claude.daily-dashboard")
DELIVERY_NAMES = ("Uber Eats", "出前館", "ロケットナウ")


# ---------- 共通ユーティリティ ----------

def strip_md(text: str) -> str:
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("**", "").replace("`", "")
    text = re.sub(r"\s*←.*$", "", text)
    return text.strip()


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def yen(cell: str):
    m = re.search(r"¥\s*([\d,]+)", cell)
    return int(m.group(1).replace(",", "")) if m else None


def fmt(n) -> str:
    return f"¥{n:,}" if n is not None else "—"


def section_lines(text: str, heading_prefix: str, level: str = "## "):
    lines, out, inside = text.splitlines(), [], False
    for line in lines:
        if line.startswith(level):
            if inside:
                break
            inside = heading_prefix in line[len(level):]
            continue
        if inside:
            out.append(line)
    return out


# ---------- タスク・期日・日誌 ----------

def parse_thisweek(board_path: Path, limit: int = 6):
    items = []
    try:
        for line in section_lines(read(board_path), "📌 今週やる"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            body = line[2:].strip()
            if body.startswith(("✅", "[x]", "[-]")):
                continue
            items.append(strip_md(body.removeprefix("⬜").strip()))
    except OSError:
        return None
    return items[:limit]


def parse_deadlines(deadline_path: Path, today: datetime.date, limit: int = 7):
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
        body = strip_md(re.sub(r"[（(].{40,}[)）]", "", m.group(4)))
        mark = "overdue" if d < today else ("soon" if (d - today).days <= 7 else "")
        items.append((d, body[:70], mark))
    items.sort(key=lambda x: x[0])
    return items[:limit], max(0, len(items) - limit)


def parse_daily_note(vault: Path, today: datetime.date, limit: int = 5):
    path = vault / DIARY_DIR_REL / f"{today.isoformat()}.md"
    if not path.exists():
        return None
    bullets, inside = [], False
    for line in read(path).splitlines():
        if re.match(r"^#{1,4} ", line):
            inside = ("思いつきメモ" in line) or ("Inbox" in line) or ("メモ / アイデア" in line)
            continue
        if inside and line.strip().startswith("- ") and line.strip() != "-":
            b = strip_md(line.strip()[2:])
            if b:
                bullets.append(b)
    return bullets[:limit]


# ---------- 自動化ジョブ数 ----------

def parse_job_counts(ledger_path: Path):
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
    if rows < 10:
        return None
    return counts["🟢"], counts["🟡"], counts["🛑"], rows


# ---------- お金 ----------

def parse_budgets(vault: Path, ym: str):
    """目標と計画.md の当月行 → (デリバリー目標, YouTube目標, 合計目標)"""
    try:
        text = read(vault / GOALS_REL)
    except OSError:
        return None
    for line in text.splitlines():
        if re.match(rf"^\|\s*{ym}\s*\|", line):
            cells = [c.strip() for c in line.split("|")]
            # | 月 | D目標 | D実績 | Y目標 | Y実績 | 合計目標 | 合計実績 |
            if len(cells) >= 8:
                return yen(cells[2]), yen(cells[4]), yen(cells[6])
    return None


def parse_month_sales(vault: Path, today: datetime.date):
    """当月デイリーノートの「今日の売上」表を集計。
    返り値: (delivery_sum, youtube_sum, [(day, その日の合計)], days)
    days = [{"day": 3, "Uber Eats": 5140, "出前館": None, ..., "YouTube": None}, ...]"""
    delivery = youtube = 0
    daily_totals = []
    days = []
    names = DELIVERY_NAMES + ("YouTube",)
    for day in range(1, today.day + 1):
        path = vault / DIARY_DIR_REL / f"{today.year}-{today.month:02d}-{day:02d}.md"
        if not path.exists():
            continue
        amounts = {n: None for n in names}
        for line in read(path).splitlines():
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]*)\|", line)
            if not m:
                continue
            name, amount = m.group(1), yen(m.group(2))
            if amount is None or name not in amounts:
                continue
            amounts[name] = (amounts[name] or 0) + amount
        if all(v is None for v in amounts.values()):
            continue
        d_day = sum(amounts[n] or 0 for n in DELIVERY_NAMES)
        y_day = amounts["YouTube"] or 0
        delivery += d_day
        youtube += y_day
        daily_totals.append((day, d_day + y_day))
        days.append({"day": day, **amounts})
    return delivery, youtube, daily_totals, days


def parse_freee_block(vault: Path, today: datetime.date, lookback: int = 70):
    """直近の記入済み経営ダッシュボードブロック（freee数字）を探す"""
    for back in range(lookback):
        d = today - datetime.timedelta(days=back)
        path = vault / DIARY_DIR_REL / f"{d.isoformat()}.md"
        if not path.exists():
            continue
        text = read(path)
        m = re.search(r"<!-- dashboard:start -->(.*?)<!-- dashboard:end -->", text, re.S)
        if not m or "今月売上" not in m.group(1):
            continue
        block = m.group(1)
        data = {"date": d}
        for key in ("今月売上", "今月経費", "今月利益", "口座残高"):
            row = re.search(rf"\|\s*{key}\s*\|\s*([^|]*)\|\s*([^|]*)\|", block)
            if row:
                data[key] = yen(row.group(1))
                if key == "今月売上":
                    data["備考"] = row.group(2).strip()
        if data.get("今月売上") is not None:
            data["stale"] = (d.month != today.month) or ((today - d).days > 3)
            return data
    return None


def build_sales_svg(daily_totals, budget_total):
    """当月の累計売上ライン（SVG）。予算ラインを薄く重ねる。"""
    if len(daily_totals) < 2:
        return '<p class="hint">まだデータが少ないよ（月初か、日誌の売上表が空）</p>'
    W, H, PAD = 600, 170, 14
    cum, s = [], 0
    for day, total in daily_totals:
        s += total
        cum.append((day, s))
    max_day = max(31, cum[-1][0])
    max_val = max(s, budget_total or 0, 1)
    def x(day): return PAD + (W - 2 * PAD) * (day - 1) / (max_day - 1)
    def y(val): return H - PAD - (H - 2 * PAD) * (val / max_val)
    pts = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in cum)
    area = f"{x(cum[0][0]):.1f},{H-PAD:.1f} {pts} {x(cum[-1][0]):.1f},{H-PAD:.1f}"
    budget_line = ""
    if budget_total:
        budget_line = (f'<line x1="{PAD}" y1="{y(budget_total):.1f}" x2="{W-PAD}" y2="{y(budget_total):.1f}" '
                       f'stroke="var(--ink3)" stroke-dasharray="4 5" stroke-width="1"/>'
                       f'<text x="{W-PAD}" y="{y(budget_total)-5:.1f}" text-anchor="end" class="svgt">予算 {fmt(budget_total)}</text>')
    lx, ly = x(cum[-1][0]), y(cum[-1][1])
    anchor = "end" if lx > W - 90 else "start"
    return f"""<svg viewBox="0 0 {W} {H}" role="img" aria-label="今月の累計売上グラフ" style="width:100%;height:auto;display:block;">
  <polygon points="{area}" fill="var(--accent)" opacity="0.10"/>
  {budget_line}
  <polyline points="{pts}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="4" fill="var(--accent)"/>
  <text x="{lx:.1f}" y="{ly-9:.1f}" text-anchor="{anchor}" class="svgt strong">{fmt(cum[-1][1])}</text>
  <text x="{PAD}" y="{H-2}" class="svgt">1日</text>
  <text x="{W-PAD}" y="{H-2}" text-anchor="end" class="svgt">{max_day}日</text>
</svg>"""


def biz_card(name, actual, budget, today, detail_html=""):
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    pct = (actual / budget * 100) if budget else None
    pace = None
    if budget:
        pace = actual - round(budget * today.day / days_in_month)
    pct_s = f"{pct:.0f}%" if pct is not None else "—"
    width = min(100, pct or 0)
    if pace is None:
        pace_html = ""
    else:
        cls = "up" if pace >= 0 else "down"
        sign = "+" if pace >= 0 else "−"
        pace_html = f'<span class="pace {cls}">ペース{sign}¥{abs(pace):,}</span>'
    return f"""      <details class="card exp">
        <summary>
          <div class="cardhead"><h3>{esc(name)}</h3>{pace_html}</div>
          <div class="big">{fmt(actual)}</div>
          <div class="sub">予算 {fmt(budget)} ・ 達成率 <b>{pct_s}</b><span class="opener">日別 ▾</span></div>
          <div class="bar"><i style="width:{width:.0f}%"></i></div>
        </summary>
        {detail_html}
      </details>
"""


def cell(v):
    return f'<td class="r">{fmt(v)}</td>' if v is not None else '<td class="r dim2">—</td>'


def build_daily_details(days, today):
    """日別明細テーブル（新しい日が上）: (デリバリー用, YouTube用, 合計用)"""
    rows_d = rows_y = rows_t = ""
    for e in reversed(days):
        date = f"{today.month}/{e['day']}"
        d_sum = sum(e[n] or 0 for n in DELIVERY_NAMES)
        has_d = any(e[n] is not None for n in DELIVERY_NAMES)
        if has_d:
            rows_d += (f'<tr><td class="strongc">{date}</td>{cell(e["Uber Eats"])}{cell(e["出前館"])}'
                       f'{cell(e["ロケットナウ"])}<td class="r strongc">{fmt(d_sum)}</td></tr>')
        if e["YouTube"] is not None:
            rows_y += f'<tr><td class="strongc">{date}</td>{cell(e["YouTube"])}</tr>'
        rows_t += (f'<tr><td class="strongc">{date}</td>{cell(d_sum if has_d else None)}{cell(e["YouTube"])}'
                   f'<td class="r strongc">{fmt(d_sum + (e["YouTube"] or 0))}</td></tr>')
    t_d = (f'<table class="mini"><tr><th>日付</th><th class="r">Uber</th><th class="r">出前館</th>'
           f'<th class="r">ロケナウ</th><th class="r">計</th></tr>{rows_d}</table>') if rows_d else \
        '<p class="hint">今月はまだ記入なし</p>'
    t_y = (f'<table class="mini"><tr><th>日付</th><th class="r">収益</th></tr>{rows_y}</table>'
           '<p class="hint">YouTube収益は2〜3日遅れで自動記入される仕様</p>') if rows_y else \
        '<p class="hint">今月はまだ記入なし（2〜3日遅れで自動記入される仕様）</p>'
    t_t = (f'<table class="mini"><tr><th>日付</th><th class="r">デリバリー</th><th class="r">YouTube</th>'
           f'<th class="r">計</th></tr>{rows_t}</table>') if rows_t else '<p class="hint">今月はまだ記入なし</p>'
    return t_d, t_y, t_t


def build_money_html(vault: Path, today: datetime.date):
    ym = f"{today.year}-{today.month:02d}"
    budgets = parse_budgets(vault, ym) or (None, None, None)
    d_budget, y_budget, t_budget = budgets
    delivery, youtube, daily_totals, days = parse_month_sales(vault, today)
    filled = len(days)
    total = delivery + youtube
    freee = parse_freee_block(vault, today)

    t_d, t_y, t_t = build_daily_details(days, today)
    cards = biz_card("デリバリー", delivery, d_budget, today, t_d)
    cards += biz_card("YouTube", youtube, y_budget, today, t_y)
    cards += biz_card("合計", total, t_budget, today, t_t)

    if freee:
        stale_note = ""
        if freee.get("stale"):
            stale_note = (f'<p class="warn">⚠ freeeの数字は {freee["date"].strftime("%m/%d")} 時点で止まってる'
                          f'（朝4:00ジョブの自動記入が更新されてない）。あおいに確認して。</p>')
        freee_html = f"""      <div class="card">
        <div class="cardhead"><h3>freee帳簿（{freee["date"].strftime("%m/%d")}時点）</h3></div>
        <table class="mini">
          <tr><td>売上</td><td class="r">{fmt(freee.get("今月売上"))}</td></tr>
          <tr><td>経費</td><td class="r">{fmt(freee.get("今月経費"))}</td></tr>
          <tr><td>利益</td><td class="r strongc">{fmt(freee.get("今月利益"))}</td></tr>
          <tr><td>口座残高</td><td class="r">{fmt(freee.get("口座残高"))}</td></tr>
        </table>
        <p class="hint">経費の項目別はfreee（正本）で確認。{esc(freee.get("備考", ""))}</p>
        {stale_note}
      </div>
"""
    else:
        freee_html = '      <div class="card"><h3>freee帳簿</h3><p class="hint">記入済みの経営ダッシュボードブロックが見つからなかった（朝4:00ジョブを確認）。</p></div>\n'

    chart = build_sales_svg(daily_totals, t_budget)
    return f"""  <section class="sec" id="money">
    <p class="seclabel">Money</p>
    <h2>今月のお金 <span class="dim">{today.month}月・日誌集計は{filled}日分</span></h2>
    <div class="grid3">
{cards}    </div>
    <div class="grid2" style="margin-top:14px;">
      <div class="card">
        <div class="cardhead"><h3>売上の伸び（累計）</h3></div>
        {chart}
      </div>
{freee_html}    </div>
    <p class="hint" style="margin-top:10px;">実績はデイリーノート「今日の売上」表の自動集計（速報値）。確定数字はfreeeが正本。</p>
  </section>
"""


# ---------- YouTube運営 ----------

def parse_yt_board(vault: Path):
    path = vault / YTBOARD_REL
    if not path.exists():
        return None
    text = read(path)
    schedule = []
    for line in section_lines(text, "今週の投稿予定"):
        m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m and m.group(1) not in ("予定日", "---") and not set(m.group(1)) <= set("-: "):
            schedule.append((m.group(1), m.group(2), m.group(3)))
    making = [strip_md(l.strip()[2:]) for l in section_lines(text, "制作中") if l.strip().startswith("- ")]
    todos = [strip_md(l.strip()[6:]) for l in section_lines(text, "やること") if l.strip().startswith("- [ ]")]
    return schedule, making, todos


def parse_slate(vault: Path, today: datetime.date):
    path = vault / SLATE_REL_FMT.format(ym=f"{today.year}-{today.month:02d}")
    if not path.exists():
        return None
    text = read(path)
    ready = len(re.findall(r"台本できてる", text))
    brief = len(re.findall(r"ブリーフ済", text))
    items = []
    for m in re.finditer(r"^\d+\.\s*(.+?)〔(.+?)〕", text, re.M):
        items.append((m.group(1).strip(), m.group(2).strip()))
    fresh = None  # 草案のデータ鮮度（例: 2026-06-28）
    fm = re.search(r"データ鮮度:\s*\D*(\d{4})-(\d{2})-(\d{2})", text)
    if fm:
        fresh = datetime.date(int(fm.group(1)), int(fm.group(2)), int(fm.group(3)))
    return ready, brief, items[:6], fresh


def parse_board_youtube(vault: Path, limit: int = 4):
    try:
        text = read(vault / BOARD_REL)
    except OSError:
        return []
    out = []
    for line in section_lines(text, "📺 YouTube", level="### "):
        line = line.strip()
        if line.startswith("- ⬜"):
            out.append(strip_md(line[3:].strip()))
    return out[:limit]


def build_youtube_html(vault: Path, today: datetime.date):
    board = parse_yt_board(vault)
    slate = parse_slate(vault, today)
    extra = parse_board_youtube(vault)

    if board:
        schedule, making, todos = board
        sched_rows = "".join(
            f'<tr><td class="strongc">{esc(d)}</td><td>{esc(n)}</td><td class="dim2">{esc(s)}</td></tr>'
            for d, n, s in schedule
        ) or '<tr><td colspan="3" class="dim2">予定なし（週間ボードに書くと出るよ）</td></tr>'
        making_lis = "".join(f"<li>{esc(x)}</li>" for x in making) or '<li class="dim2">なし</li>'
        todo_lis = "".join(f"<li>{esc(x)}</li>" for x in todos)
    else:
        sched_rows = '<tr><td colspan="3" class="dim2">YouTube週間ボード.mdが見つからない</td></tr>'
        making_lis, todo_lis = "", ""
    seen = todos[:] if board else []
    seen += making if board else []
    for x in extra:
        # 週間ボードと実質同じ項目（相互に文字列を含む）は重複表示しない
        if any(x[:12] in s or s[:12] in x for s in seen if s):
            continue
        todo_lis += f'<li>{esc(x)}</li>'
        seen.append(x)
    todo_lis = todo_lis or '<li class="dim2">なし</li>'

    if slate:
        ready, brief, items, fresh = slate
        fresh_tag = f' <span class="tag">草案 {fresh.month}/{fresh.day}時点</span>' if fresh else ""
        stock_head = f'台本済 <b class="strongc">{ready}</b> 本 ・ ブリーフ済（台本これから） <b>{brief}</b> 本{fresh_tag}'
        stock_lis = "".join(
            f'<li>{esc(n)} <span class="tag{" ok" if "公開待ち" in s or "台本できてる" in s else ""}">{esc(s)}</span></li>'
            for n, s in items
        )
        stale_warn = ""
        if fresh and (datetime.date.today() - fresh).days > 7:
            stale_warn = ('<p class="warn">⚠ 在庫リストは草案時点の状態で、最新の進捗は反映されてない。'
                          '実際の状況は上の週間ボード（あおいが更新）が正。</p>')
        stock_html = (f'<p class="sub" style="margin:2px 0 6px;">{stock_head}</p><ul class="list">{stock_lis}</ul>'
                      f'{stale_warn}<p class="hint">在庫の正本: 来月ネタ草案（毎月25日更新）</p>')
    else:
        stock_html = '<p class="hint">今月のネタ草案ファイルが見つからない</p>'

    return f"""  <section class="sec" id="youtube">
    <p class="seclabel">YouTube</p>
    <h2>YouTube運営</h2>
    <div class="grid2">
      <div class="card">
        <div class="cardhead"><h3>今週の投稿予定</h3></div>
        <table class="mini"><tr><th>予定日</th><th>ネタ</th><th>状態</th></tr>{sched_rows}</table>
        <div class="cardhead" style="margin-top:14px;"><h3>制作中</h3></div>
        <ul class="list">{making_lis}</ul>
      </div>
      <div class="card">
        <div class="cardhead"><h3>やること</h3></div>
        <ul class="list">{todo_lis}</ul>
        <div class="cardhead" style="margin-top:14px;"><h3>ネタ在庫</h3></div>
        {stock_html}
      </div>
    </div>
    <p class="hint" style="margin-top:10px;">予定と進捗の正本は「YouTube週間ボード.md」（司令塔）。Discordで「投稿予定: 7/20 ◯◯」と言えばあおいが更新。</p>
  </section>
"""


# ---------- タスク ----------

def build_tasks_html(thisweek, deadlines, deadline_rest, daily, today):
    badge = {"overdue": ' <span class="due">期限切れ</span>', "soon": ' <span class="due soon">今週</span>', "": ""}
    li_week = "".join(f"<li>{esc(t)}</li>" for t in (thisweek or [])) or '<li class="dim2">（読み取れなかった）</li>'
    li_dead = "".join(
        f'<li><b>{d.strftime("%m/%d")}</b>　{esc(t)}{badge.get(m, "")}</li>'
        for d, t, m in (deadlines or [])
    ) or "<li>期日つきタスクはゼロ！</li>"
    rest = f'<li class="dim2">…ほか{deadline_rest}件（期日タスク.md）</li>' if deadline_rest else ""
    if daily is None:
        daily_html = '<p class="dim2">今日はまだ作られていない。Obsidianで開くと自動作成、Discordで「メモ: ◯◯」でも入る。</p>'
    elif not daily:
        daily_html = '<p class="dim2">作成済み。メモはまだなし（Discordで「メモ: ◯◯」）。</p>'
    else:
        daily_html = '<ul class="list">' + "".join(f"<li>{esc(b)}</li>" for b in daily) + "</ul>"
    return f"""  <section class="sec" id="tasks">
    <p class="seclabel">Tasks</p>
    <h2>今日のタスク <span class="dim">完了はDiscordで「済: ◯◯」</span></h2>
    <div class="grid3">
      <div class="card"><div class="cardhead"><h3>今週やる</h3></div><ul class="list">{li_week}</ul></div>
      <div class="card"><div class="cardhead"><h3>期日つき</h3></div><ul class="list">{li_dead}{rest}</ul></div>
      <div class="card"><div class="cardhead"><h3>今日のデイリーノート <span class="dim">{today.month}/{today.day}</span></h3></div>{daily_html}</div>
    </div>
  </section>
"""


# ---------- main ----------

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
    values = {"N_GOOD": "—", "N_WATCH": "—", "N_STOP": "—", "N_TOTAL": "—"}
    if counts:
        good, watch, stop, total_jobs = counts
        values = {"N_GOOD": str(good), "N_WATCH": str(watch), "N_STOP": str(stop), "N_TOTAL": str(total_jobs)}
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    out = out.replace("{{MONEY_HTML}}", build_money_html(vault, today))
    out = out.replace("{{YOUTUBE_HTML}}", build_youtube_html(vault, today))
    out = out.replace("{{TASKS_HTML}}", build_tasks_html(thisweek, deadlines, rest, daily, today))

    if "{{" in out:
        sys.exit("テンプレートに未解決のプレースホルダが残っている")
    dest = vault / OUTPUT_REL
    dest.write_text(out, encoding="utf-8")
    print(f"OK: {dest} ({dest.stat().st_size} bytes) 今週={len(thisweek or [])} 期日={len(deadlines or [])} counts={counts}")


if __name__ == "__main__":
    main()
