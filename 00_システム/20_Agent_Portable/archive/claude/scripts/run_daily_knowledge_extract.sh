#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "daily-knowledge-extractスキルを使って、今日(と未処理なら前日)のデイリーノートから価値ある気づき・アイデア・学びを抽出し、2nd-Brainの知識ベースに追記＋[[リンク]]で保存して。昇華した分は日誌に✅昇華済を付けて。結果を Discord #メモ(chat_id 1512911464439087295) に簡潔報告。追記のみ・削除はしない。" \
  --permission-mode auto \
  --allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep,Skill" \
  2>&1 | tee /Users/kojinn/.claude/scripts/daily_knowledge_extract.log
