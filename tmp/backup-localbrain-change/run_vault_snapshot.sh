#!/bin/bash
# ============================================================
# vault-snapshot.sh のlaunchd用ラッパー（毎週日曜 4:30）
#   launchd直のbashはGoogle Driveの証憑フォルダを読めない（TCC）場合があるので、
#   まず直接実行を試し、ダメなら agent-run 経由のClaude（Full Disk Access持ち）で実行。
# ============================================================
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.bun/bin:$(/bin/ls -d /Users/kojinn/.nvm/versions/node/*/bin 2>/dev/null | /usr/bin/sort -V | /usr/bin/tail -1):/usr/local/bin:/usr/bin:/bin"
export LANG="ja_JP.UTF-8"

SCRIPT="$HOME/.claude/scripts/vault-snapshot.sh"
NOTIFY="$HOME/.claude/scripts/discord_notify.sh"
LOG="$HOME/.claude/scripts/vault-snapshot.log"
AGENT_RUN="$HOME/agent-adapters/bin/agent-run"

echo "$(date): start" >> "$LOG"

# 1) 直接（TCCが許す環境ならこれで済む）
if [ -s "$HOME/2nd-Brain-master/CLAUDE.md" ] \
  && ls "$HOME/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/経費精算" >/dev/null 2>&1 \
  && ls "$HOME/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/売上証憑" >/dev/null 2>&1; then
  bash "$SCRIPT" direct >> "$LOG" 2>&1
  exit $?
fi

# 2) agent-run 経由（現時点はClaude固定。将来のAI差し替え用の入口だけ中立化）
echo "$(date): TCCブロック → agent-run 経由で実行（AGENT_VENDOR=claude）" >> "$LOG"
if [ ! -x "$AGENT_RUN" ]; then
  echo "$(date): agent-runが実行できない: $AGENT_RUN" >> "$LOG"
  bash "$NOTIFY" "🔴【Vaultスナップショット】agent-runが実行できない。ログ: vault-snapshot.log" || true
  exit 1
fi
for i in 1 2 3; do
  RESULT=$(echo "Bashツールで bash /Users/kojinn/.claude/scripts/vault-snapshot.sh direct を実行して、出力をそのまま返してください。他の操作は不要です。" \
    | AGENT_VENDOR=claude "$AGENT_RUN" -p --permission-mode auto --allowed-tools "Bash" 2>&1)
  echo "$RESULT" >> "$LOG"
  if echo "$RESULT" | grep -q "✅ Vaultスナップショット完了"; then
    exit 0
  fi
  echo "$(date): attempt $i failed, retry in 30s" >> "$LOG"
  sleep 30
done

bash "$NOTIFY" "🔴【Vaultスナップショット】直接・agent-run経由とも失敗。ログ: vault-snapshot.log" || true
exit 1
