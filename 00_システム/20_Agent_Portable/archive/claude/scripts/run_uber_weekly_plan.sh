#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "uber-weekly-planスキルを使って、来週(次の月曜〜日曜)のUber最適稼働プランを生成して、Discordの #お金(chat_id 1512911463180800120) に投稿して。天気予報はOpen-Meteoで自動取得、クエスト型と実績データはスキルのdata/patterns.mdを参照。雨予報の日を最優先に、月〜木の40配達クエストと時間枠クエストを織り込んで。" \
  --permission-mode auto \
  --allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Glob,Grep,Skill,mcp__playwright__browser_navigate,mcp__playwright__browser_evaluate" \
  2>&1 | tee /Users/kojinn/.claude/scripts/uber_weekly_plan.log
