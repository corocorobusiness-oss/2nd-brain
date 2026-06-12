#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "uber-earningsスキルを使って、今日のUber売上（配達＋プロモ）を取得し、デイリーノートに記入・予算比較して、Discordの #お金(chat_id 1512911463180800120) に結果を投稿して。ログインが切れていたら集計せず再ログインが必要な旨を #お金 に通知して。出前館は触らない。" \
  --permission-mode auto \
  --allowedTools "mcp__playwright__browser_navigate,mcp__playwright__browser_evaluate,mcp__playwright__browser_click,mcp__playwright__browser_snapshot,mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep,Skill" \
  2>&1 | tee /Users/kojinn/.claude/scripts/uber_earnings.log
