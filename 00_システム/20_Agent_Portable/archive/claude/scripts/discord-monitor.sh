#!/bin/bash
# Discord監視スクリプト - 数分おきに新着メッセージを確認して処理

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
export LANG="ja_JP.UTF-8"

security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db 2>/dev/null

LAST_ID_FILE="/Users/kojinn/.claude/scripts/discord-last-id.txt"
LOG_FILE="/Users/kojinn/.claude/scripts/discord-monitor.log"
LOCK_FILE="/Users/kojinn/.claude/scripts/discord-monitor.lock"

# 多重起動防止
if [ -f "$LOCK_FILE" ]; then
  LOCK_PID=$(cat "$LOCK_FILE")
  if kill -0 "$LOCK_PID" 2>/dev/null; then
    echo "$(date): Already running (PID $LOCK_PID), skipping" >> "$LOG_FILE"
    exit 0
  fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

# ログローテーション（1MB超えたらリセット）
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || echo 0) -gt 1048576 ]; then
  tail -100 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
fi

echo "$(date): Checking Discord for new messages" >> "$LOG_FILE"

# 最後に処理したメッセージIDを取得
LAST_ID=""
if [ -f "$LAST_ID_FILE" ]; then
  LAST_ID=$(cat "$LAST_ID_FILE")
fi

# Discord新着チェック＆処理プロンプト
PROMPT="Discordメインチャンネル 1486946641389817899 の最新メッセージを5件取得して確認してください。

最後に処理済みのメッセージID: ${LAST_ID:-なし}

以下のルールで処理してください：
1. 処理済みIDより新しいメッセージのみ対象（IDが空なら最新1件のみ対象）
2. 自分（bot）のメッセージは無視
3. 画像添付があればレシート処理（CLAUDE.mdのルール通り）
4. 売上報告（例：Uber 4500 出前館 3000）があれば売上記録処理
5. 質問や会話があれば適切に返信
6. 処理対象がなければ何もしない

重要：
- 処理したメッセージのうち最新のメッセージIDを必ず最後に出力してください。フォーマット: LAST_PROCESSED_ID:メッセージID
- 処理対象がなかった場合も最新メッセージIDを出力: LAST_PROCESSED_ID:メッセージID
- corocoro0908 からのメッセージのみ処理してください"

RESULT=$(echo "$PROMPT" | claude -p --permission-mode auto 2>&1)
echo "$RESULT" >> "$LOG_FILE"

# 最後に処理したIDを保存
NEW_ID=$(echo "$RESULT" | grep "LAST_PROCESSED_ID:" | tail -1 | sed 's/.*LAST_PROCESSED_ID://')
if [ -n "$NEW_ID" ]; then
  echo "$NEW_ID" > "$LAST_ID_FILE"
  echo "$(date): Updated last ID to $NEW_ID" >> "$LOG_FILE"
fi

echo "$(date): Done" >> "$LOG_FILE"
