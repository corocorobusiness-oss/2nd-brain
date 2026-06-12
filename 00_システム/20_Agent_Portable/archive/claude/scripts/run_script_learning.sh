#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "$(cat /Users/kojinn/.claude/scripts/script_learning.md)" --permission-mode auto --allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep" 2>&1 | tee /Users/kojinn/.claude/scripts/script_learning.log
