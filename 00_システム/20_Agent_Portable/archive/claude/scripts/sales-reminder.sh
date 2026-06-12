#!/bin/bash
# 売上リマインド - 毎日21:00実行
# デイリーノートに売上が未記入なら催促する

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
export LANG="ja_JP.UTF-8"

security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db 2>/dev/null

VAULT_DIR="/Users/kojinn/2nd-Brain"
TODAY=$(date +%Y-%m-%d)
DAILY_NOTE="${VAULT_DIR}/05_日誌/${TODAY}.md"
LOG_FILE="/Users/kojinn/.claude/scripts/sales-reminder.log"

echo "$(date): Starting sales reminder" > "$LOG_FILE"

# デイリーノートが存在しない or 売上が未記入かチェック
NEED_REMINDER=false

if [ ! -f "$DAILY_NOTE" ]; then
  NEED_REMINDER=true
elif grep -q "| Uber Eats |.*[0-9]" "$DAILY_NOTE" 2>/dev/null; then
  NEED_REMINDER=false
elif grep -q "| デリバリー計 |.*[0-9]" "$DAILY_NOTE" 2>/dev/null; then
  NEED_REMINDER=false
else
  NEED_REMINDER=true
fi

if [ "$NEED_REMINDER" = true ]; then
  PROMPT="Discordチャンネル 1486946641389817899 に以下のメッセージを送信してください（mcp__plugin_discord_discord__reply を使って）：祐馬、今日の売上まだ入ってないよ！Uber Eats・出前館・YouTubeそれぞれ教えて。例：Uber 4500 出前館 3000 YouTube 500 って感じでOK！ ※ Discord への送信だけ行ってください。他の操作は不要です。"

  for i in 1 2 3; do
    echo "$(date): Attempt $i" >> "$LOG_FILE"
    RESULT=$(echo "$PROMPT" | claude -p --permission-mode auto --allowed-tools "mcp__plugin_discord_discord__reply" 2>&1)
    echo "$RESULT" >> "$LOG_FILE"

    if ! echo "$RESULT" | grep -qi "not logged in\|error\|failed"; then
      echo "$(date): Success on attempt $i" >> "$LOG_FILE"
      exit 0
    fi
    sleep 10
  done
  echo "$(date): All attempts failed" >> "$LOG_FILE"
else
  echo "$(date): Sales already recorded, no reminder needed" >> "$LOG_FILE"
fi
