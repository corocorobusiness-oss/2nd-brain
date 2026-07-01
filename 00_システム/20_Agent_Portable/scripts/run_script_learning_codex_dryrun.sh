#!/bin/bash
set -u

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.bun/bin:$(/bin/ls -d /Users/kojinn/.nvm/versions/node/*/bin 2>/dev/null | /usr/bin/sort -V | /usr/bin/tail -1):/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="/Users/kojinn/.claude/scripts"
PROMPT_FILE="$SCRIPT_DIR/script_learning.md"
AGENT_RUN="/Users/kojinn/agent-adapters/bin/agent-run"
WORKDIR="${SCRIPT_LEARNING_CODEX_WORKDIR:-/Users/kojinn/2nd-Brain-master}"
ADD_DIRS="${SCRIPT_LEARNING_CODEX_ADD_DIRS:-}"
SANDBOX="${SCRIPT_LEARNING_CODEX_SANDBOX:-read-only}"
RULEBOOK="/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md"
RETENTION_JSON="/Users/kojinn/.claude/skills/neta-research/data/retention_analysis.json"
PRODUCTION_LOG_DIR="/Users/kojinn/Projects/youtube/制作ログ"
LEGACY_LOG="$SCRIPT_DIR/script_learning.log"
RAW="$(/usr/bin/mktemp)"
SUMMARY="$(/usr/bin/mktemp)"

cleanup() {
  /bin/rm -f "$RAW" "$SUMMARY"
}
trap cleanup EXIT

mtime_or_zero() {
  [ -e "$1" ] && /usr/bin/stat -f %m "$1" 2>/dev/null || echo 0
}

if [ ! -x "$AGENT_RUN" ]; then
  echo "[dry-run] agent-run is not executable: $AGENT_RUN" >&2
  exit 1
fi

if [ ! -r "$PROMPT_FILE" ]; then
  echo "[dry-run] prompt is not readable: $PROMPT_FILE" >&2
  exit 1
fi

if [ ! -d "$WORKDIR" ]; then
  echo "[dry-run] workdir does not exist: $WORKDIR" >&2
  exit 1
fi

BEFORE_RULEBOOK_MTIME="$(mtime_or_zero "$RULEBOOK")"
BEFORE_LOG_MTIME="$(mtime_or_zero "$LEGACY_LOG")"

/usr/bin/python3 - "$RETENTION_JSON" "$PRODUCTION_LOG_DIR" "$RULEBOOK" "$SUMMARY" <<'PYEOF'
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

retention_path, log_dir, rulebook_path, summary_path = sys.argv[1:5]

def pct(value):
    return f"{value * 100:.1f}%"

lines = []
lines.append("# Pre-collected script-learning dry-run evidence")
lines.append("")

try:
    with open(retention_path, encoding="utf-8") as f:
        rows = json.load(f)
except Exception as exc:
    rows = []
    lines.append(f"retention_json_error: {type(exc).__name__}: {exc}")

if rows:
    by_month = defaultdict(list)
    for row in rows:
        month = str(row.get("published", ""))[:7] or "unknown"
        by_month[month].append(row)
    months = sorted(m for m in by_month if m != "unknown")
    lines.append(f"retention_file: {retention_path}")
    lines.append(f"retention_items: {len(rows)}")
    lines.append(f"months: {', '.join(months[-4:])}")
    for month in months[-3:]:
        group = by_month[month]
        lines.append(
            f"month {month}: n={len(group)}, "
            f"intro={pct(statistics.mean(r.get('intro_hold', 0) for r in group))}, "
            f"q1={pct(statistics.mean(r.get('q1', 0) for r in group))}, "
            f"q2={pct(statistics.mean(r.get('q2', 0) for r in group))}, "
            f"q3={pct(statistics.mean(r.get('q3', 0) for r in group))}, "
            f"q4={pct(statistics.mean(r.get('q4', 0) for r in group))}"
        )
    latest_month = months[-1] if months else None
    previous_month = months[-2] if len(months) > 1 else None
    if latest_month and previous_month:
        latest_q4 = statistics.mean(r.get("q4", 0) for r in by_month[latest_month])
        previous_q4 = statistics.mean(r.get("q4", 0) for r in by_month[previous_month])
        lines.append(f"latest_vs_previous_q4: {latest_month} {pct(latest_q4)} vs {previous_month} {pct(previous_q4)} diff={(latest_q4 - previous_q4) * 100:+.1f}pt")

    drop_counter = Counter()
    for row in rows:
        for drop in row.get("worst_drops", [])[:3]:
            drop_counter[int(drop.get("at_percent", -1))] += 1
    if drop_counter:
        lines.append("frequent_drop_points: " + ", ".join(f"{point}% x{count}" for point, count in drop_counter.most_common(6)))

    best = max(rows, key=lambda r: (r.get("q4", 0), r.get("q3", 0)))
    worst = min(rows, key=lambda r: (r.get("q4", 0), r.get("q3", 0)))
    lines.append(f"best_q4: {best.get('published')} q4={pct(best.get('q4', 0))} title={best.get('title', '')[:80]}")
    lines.append(f"worst_q4: {worst.get('published')} q4={pct(worst.get('q4', 0))} title={worst.get('title', '')[:80]}")

lines.append("")
lines.append("# Production log signals")
if os.path.isdir(log_dir):
    log_files = sorted(
        os.path.join(log_dir, name)
        for name in os.listdir(log_dir)
        if name.endswith(".md")
    )
    lines.append(f"production_log_dir: {log_dir}")
    lines.append(f"production_log_files: {len(log_files)}")
    keywords = ("修正指示", "次回どうするか", "ファクト", "裏取り", "解説者", "スレタイ", "WebSearch", "形式", "フォーマット", "タイトル")
    for path in log_files[:8]:
        lines.append(f"file: {os.path.basename(path)}")
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                selected = [line.strip() for line in f if any(k in line for k in keywords)]
        except Exception as exc:
            selected = [f"read_error: {type(exc).__name__}: {exc}"]
        for line in selected[:18]:
            if line:
                lines.append(f"- {line[:220]}")
else:
    lines.append(f"production_log_dir_missing: {log_dir}")

lines.append("")
lines.append("# Current rulebook excerpt")
try:
    with open(rulebook_path, encoding="utf-8", errors="replace") as f:
        rule_lines = f.readlines()
    lines.append(f"rulebook: {rulebook_path}")
    for line in rule_lines:
        stripped = line.strip()
        if stripped.startswith("### R") or stripped.startswith("- **") or stripped.startswith("- 2026-"):
            lines.append(stripped[:240])
except Exception as exc:
    lines.append(f"rulebook_error: {type(exc).__name__}: {exc}")

with open(summary_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines).strip() + "\n")
PYEOF

DRY_PROMPT="You are reviewing a monthly YouTube script-learning job in dry-run mode.

Hard constraints:
- Do not call tools.
- Do not read files.
- Do not browse.
- Do not run shell commands.
- Do not write, edit, delete, move, or create any file.
- Do not post to Discord.
- Use only the pre-collected evidence below.
- Output only the required marker blocks plus one short summary.

Task:
Based on the pre-collected evidence, propose what the monthly script-learning job would change in the rulebook, without applying it.

Required output format:

<<<RULEBOOK_PATCH
Proposed rulebook changes or NO_CHANGE. Keep this under 1200 Japanese characters. Mention evidence names briefly.
RULEBOOK_PATCH>>>

<<<DISCORD_PROPOSAL
Message that would have been posted to #レポート, or NO_POST. Keep this under 700 Japanese characters.
DISCORD_PROPOSAL>>>

Short dry-run summary:

$(/bin/cat "$SUMMARY")
"

echo "[dry-run] script-learning via Codex"
echo "[dry-run] no file writes, no Discord posting, no tool calls by inner Codex"
echo "[dry-run] workdir: $WORKDIR"
echo "[dry-run] add_dirs: $ADD_DIRS"
echo "[dry-run] sandbox: $SANDBOX"
echo

AGENT_VENDOR=codex \
AGENT_RUN_CODEX_SANDBOX="$SANDBOX" \
AGENT_RUN_CODEX_WORKDIR="$WORKDIR" \
AGENT_RUN_CODEX_ADD_DIRS="$ADD_DIRS" \
"$AGENT_RUN" -p "$DRY_PROMPT" > "$RAW" 2>&1
RC=$?

/bin/cat "$RAW"

if [ "$RC" != "0" ]; then
  echo
  echo "[dry-run] Codex run failed: exit $RC"
  exit "$RC"
fi

/usr/bin/python3 - "$RAW" <<'PYEOF'
import io
import re
import sys

raw_path = sys.argv[1]
raw = io.open(raw_path, encoding="utf-8", errors="replace").read()
failed = False

patch = re.search(r"<<<RULEBOOK_PATCH\s*\n(.*?)\nRULEBOOK_PATCH>>>", raw, re.S)
if not patch:
    print("[dry-run] VALIDATION: FAIL RULEBOOK_PATCH block missing")
    failed = True
else:
    body = patch.group(1).strip()
    if not body:
        print("[dry-run] VALIDATION: FAIL RULEBOOK_PATCH empty")
        failed = True
    elif "RULEBOOK_PATCH" in body or "<!--" in body:
        print("[dry-run] VALIDATION: FAIL RULEBOOK_PATCH has forbidden marker text")
        failed = True
    elif len(body) > 6000:
        print(f"[dry-run] VALIDATION: FAIL RULEBOOK_PATCH too long chars={len(body)}")
        failed = True
    else:
        print(f"[dry-run] VALIDATION: OK RULEBOOK_PATCH chars={len(body)}")

proposal = re.search(r"<<<DISCORD_PROPOSAL\s*\n(.*?)\nDISCORD_PROPOSAL>>>", raw, re.S)
if not proposal:
    print("[dry-run] VALIDATION: FAIL DISCORD_PROPOSAL block missing")
    failed = True
else:
    msg = proposal.group(1).strip()
    if not msg:
        print("[dry-run] VALIDATION: FAIL DISCORD_PROPOSAL empty")
        failed = True
    elif "DISCORD_PROPOSAL" in msg or "<!--" in msg:
        print("[dry-run] VALIDATION: FAIL DISCORD_PROPOSAL has forbidden marker text")
        failed = True
    elif msg != "NO_POST" and len(msg) > 1900:
        print(f"[dry-run] VALIDATION: FAIL DISCORD_PROPOSAL too long chars={len(msg)}")
        failed = True
    else:
        print(f"[dry-run] VALIDATION: OK DISCORD_PROPOSAL chars={len(msg)} not posted")

sys.exit(2 if failed else 0)
PYEOF

VALIDATION_RC=$?

AFTER_RULEBOOK_MTIME="$(mtime_or_zero "$RULEBOOK")"
AFTER_LOG_MTIME="$(mtime_or_zero "$LEGACY_LOG")"

if [ "$AFTER_RULEBOOK_MTIME" != "$BEFORE_RULEBOOK_MTIME" ]; then
  echo "[dry-run] VALIDATION: FAIL rulebook mtime changed ($BEFORE_RULEBOOK_MTIME -> $AFTER_RULEBOOK_MTIME)"
  VALIDATION_RC=2
else
  echo "[dry-run] VALIDATION: OK rulebook unchanged"
fi

if [ "$AFTER_LOG_MTIME" != "$BEFORE_LOG_MTIME" ]; then
  echo "[dry-run] VALIDATION: FAIL legacy log mtime changed ($BEFORE_LOG_MTIME -> $AFTER_LOG_MTIME)"
  VALIDATION_RC=2
else
  echo "[dry-run] VALIDATION: OK legacy log unchanged"
fi

exit "$VALIDATION_RC"
