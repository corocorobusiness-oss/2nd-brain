#!/bin/bash
# 朝のデイリーノートルーティン - 毎朝9:00実行

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
export LANG="ja_JP.UTF-8"

# launchdからキーチェーンアクセスを確保
security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db 2>/dev/null

VAULT_DIR="/Users/kojinn/2nd-Brain"
TODAY=$(date +%Y-%m-%d)
DAILY_NOTE="${VAULT_DIR}/05_日誌/${TODAY}.md"
TEMPLATE="${VAULT_DIR}/00_システム/Templates/Daily_Note_Template.md"

LOG_FILE="/Users/kojinn/.claude/scripts/morning.log"
echo "$(date): Starting daily morning script" > "$LOG_FILE"

# デイリーノートが存在しなければテンプレートから作成
if [ ! -f "$DAILY_NOTE" ]; then
  sed "s/{{date}}/${TODAY}/g" "$TEMPLATE" > "$DAILY_NOTE"
  echo "$(date): Created daily note: $DAILY_NOTE" >> "$LOG_FILE"
else
  echo "$(date): Daily note already exists: $DAILY_NOTE" >> "$LOG_FILE"
fi

PROMPT="Discordチャンネル 1486946641389817899 に以下のメッセージを送信してください（mcp__plugin_discord_discord__reply を使って）：おはよう、祐馬！今日は${TODAY}だよ。デイリーノート作っておいたよ。今日やりたいこと・予定・タスクがあったら教えてね！あと、昨日のデリバリーの売上わかったら教えて。 ※ Discord への送信だけ行ってください。他の操作は不要です。"

# リトライ付きで実行（最大3回）
for i in 1 2 3; do
  echo "$(date): Attempt $i" >> "$LOG_FILE"
  RESULT=$(echo "$PROMPT" | claude -p --permission-mode auto --allowed-tools "mcp__plugin_discord_discord__reply" 2>&1)
  echo "$RESULT" >> "$LOG_FILE"

  # 成功判定（"Not logged in" や "error" がなければ成功）
  if ! echo "$RESULT" | grep -qi "not logged in\|error\|failed"; then
    echo "$(date): Success on attempt $i" >> "$LOG_FILE"
    exit 0
  fi

  echo "$(date): Attempt $i failed, waiting 10s..." >> "$LOG_FILE"
  sleep 10
done

echo "$(date): All attempts failed" >> "$LOG_FILE"
exit 1
