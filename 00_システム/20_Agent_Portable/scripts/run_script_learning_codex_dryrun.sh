#!/bin/bash
set -u

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.bun/bin:$(/bin/ls -d /Users/kojinn/.nvm/versions/node/*/bin 2>/dev/null | /usr/bin/sort -V | /usr/bin/tail -1):/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="/Users/kojinn/.claude/scripts"
PROMPT_FILE="$SCRIPT_DIR/script_learning.md"
AGENT_RUN="/Users/kojinn/agent-adapters/bin/agent-run"
WORKDIR="${SCRIPT_LEARNING_CODEX_WORKDIR:-/Users/kojinn/2nd-Brain-master}"
ADD_DIRS="${SCRIPT_LEARNING_CODEX_ADD_DIRS:-/Users/kojinn/2nd-Brain:/Users/kojinn/Projects/youtube:/Users/kojinn/.claude/skills/neta-research/data}"
SANDBOX="${SCRIPT_LEARNING_CODEX_SANDBOX:-read-only}"
RULEBOOK="/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md"
LEGACY_LOG="$SCRIPT_DIR/script_learning.log"
RAW="$(/usr/bin/mktemp)"

cleanup() {
  /bin/rm -f "$RAW"
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

DRY_PROMPT="$(/bin/cat "$PROMPT_FILE")

## Codex dry-run override

This is a migration dry-run for script-learning. Keep the learning task intent, but follow these hard constraints:

- Do not write, edit, delete, move, or create any file.
- Do not post to Discord or call any notification tool.
- Do not use network access.
- Do not run shell commands.
- Read local files only.
- Do not execute analyze_retention.py. Instead, read the existing JSON at /Users/kojinn/.claude/skills/neta-research/data/retention_analysis.json.
- Read /Users/kojinn/Projects/youtube/制作ログ/ if available.
- Read the existing rulebook at /Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md.
- Output proposed changes only. The wrapper will not apply them.

Required output format:

<<<RULEBOOK_PATCH
Proposed rulebook changes or 'NO_CHANGE'. Include concise reasons and source files consulted.
RULEBOOK_PATCH>>>

<<<DISCORD_PROPOSAL
Message that would have been posted to #レポート, or 'NO_POST'.
DISCORD_PROPOSAL>>>

End with one short dry-run summary paragraph.
"

echo "[dry-run] script-learning via Codex"
echo "[dry-run] no file writes, no Discord posting, no shell commands by inner Codex"
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
