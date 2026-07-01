#!/bin/bash
set -u

TARGET="/Users/kojinn/.claude/scripts/run_script_learning.sh"
RULEBOOK="/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md"
LEGACY_LOG="/Users/kojinn/.claude/scripts/script_learning.log"
RAW="$(/usr/bin/mktemp)"

cleanup() {
  /bin/rm -f "$RAW"
}
trap cleanup EXIT

mtime_or_zero() {
  [ -e "$1" ] && /usr/bin/stat -f %m "$1" 2>/dev/null || echo 0
}

require_output() {
  local pattern="$1"
  local label="$2"
  if /usr/bin/grep -Fq "$pattern" "$RAW"; then
    echo "[terminal-gate] OK $label"
    return 0
  fi
  echo "[terminal-gate] FAIL $label missing: $pattern"
  return 1
}

if [ ! -x "$TARGET" ]; then
  echo "[terminal-gate] FAIL target is not executable: $TARGET" >&2
  exit 1
fi

BEFORE_RULEBOOK_MTIME="$(mtime_or_zero "$RULEBOOK")"
BEFORE_LOG_MTIME="$(mtime_or_zero "$LEGACY_LOG")"

echo "[terminal-gate] command: SCRIPT_LEARNING_AGENT_VENDOR=codex $TARGET"
echo "[terminal-gate] expected: dry-run only, no Discord post, no rulebook/log update"
echo

SCRIPT_LEARNING_AGENT_VENDOR=codex "$TARGET" > "$RAW" 2>&1
RC=$?

/bin/cat "$RAW"
echo
echo "[terminal-gate] command_exit=$RC"

FAILED=0

if [ "$RC" != "0" ]; then
  echo "[terminal-gate] FAIL command exit was not 0"
  FAILED=1
fi

require_output "SCRIPT_LEARNING_AGENT_VENDOR=codex -> dry-run only" "wrapper reached dry-run branch" || FAILED=1
require_output "[dry-run] VALIDATION: OK RULEBOOK_PATCH" "rulebook patch block validated" || FAILED=1
require_output "[dry-run] VALIDATION: OK DISCORD_PROPOSAL" "discord proposal block validated" || FAILED=1
require_output "not posted" "discord proposal not posted" || FAILED=1
require_output "[dry-run] VALIDATION: OK rulebook unchanged" "dry-run reported rulebook unchanged" || FAILED=1
require_output "[dry-run] VALIDATION: OK legacy log unchanged" "dry-run reported legacy log unchanged" || FAILED=1

AFTER_RULEBOOK_MTIME="$(mtime_or_zero "$RULEBOOK")"
AFTER_LOG_MTIME="$(mtime_or_zero "$LEGACY_LOG")"

if [ "$AFTER_RULEBOOK_MTIME" = "$BEFORE_RULEBOOK_MTIME" ]; then
  echo "[terminal-gate] OK rulebook mtime unchanged"
else
  echo "[terminal-gate] FAIL rulebook mtime changed ($BEFORE_RULEBOOK_MTIME -> $AFTER_RULEBOOK_MTIME)"
  FAILED=1
fi

if [ "$AFTER_LOG_MTIME" = "$BEFORE_LOG_MTIME" ]; then
  echo "[terminal-gate] OK legacy log mtime unchanged"
else
  echo "[terminal-gate] FAIL legacy log mtime changed ($BEFORE_LOG_MTIME -> $AFTER_LOG_MTIME)"
  FAILED=1
fi

if [ "$FAILED" = "0" ]; then
  echo "[terminal-gate] PASS script-learning wrapper Codex dry-run gate"
  exit 0
fi

echo "[terminal-gate] FAIL script-learning wrapper Codex dry-run gate"
exit 2
