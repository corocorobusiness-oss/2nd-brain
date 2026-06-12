#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "knowledge-gardenerスキルを使って、2nd-Brain全体を俯瞰し、関連ノートを[[リンク]]で繋ぎ、重複統合候補・要更新を検出、MEMORY.md indexを整備して。リンク追加は自動、削除/統合は提案のみ。結果を Discord #レポート(chat_id 1512911466628386837) に報告。" \
  --permission-mode auto \
  --allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep,Skill" \
  2>&1 | tee /Users/kojinn/.claude/scripts/knowledge_gardener.log
