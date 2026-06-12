#!/bin/bash
# 夕方のデイリーノート振り返りルーティン - 毎日16:00実行
# 売上の入力も促す

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:$PATH"

TODAY=$(date +%Y-%m-%d)

PROMPT="Discordチャンネル 1486946641389817899 に以下のメッセージを送信してください（mcp__plugin_discord_discord__reply を使って）：お疲れさま、祐馬！振り返りの時間だよ。今日の売上教えて！（例：Uber 4500 出前館 3000 YouTube 0）あと、やったこと・気づいたことも教えてね。入力忘れると21時にもう一回聞くからね！ ※ Discord への送信だけ行ってください。他の操作は不要です。"

echo "$PROMPT" | claude -p --permission-mode auto --allowed-tools "mcp__plugin_discord_discord__reply"
