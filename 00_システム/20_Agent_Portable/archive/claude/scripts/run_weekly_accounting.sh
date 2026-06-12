#!/bin/bash
export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
cd /Users/kojinn
claude -p "$(cat /Users/kojinn/.claude/scripts/weekly_accounting.md)" --permission-mode auto --allowedTools "mcp__claude_ai_Gmail__gmail_search_messages,mcp__claude_ai_Gmail__gmail_read_message,mcp__claude_ai_Gmail__gmail_read_thread,mcp__playwright__browser_navigate,mcp__playwright__browser_snapshot,mcp__playwright__browser_click,mcp__playwright__browser_tabs,mcp__plugin_discord_discord__reply,Bash,Read,Write,Glob,Grep" 2>&1 | tee /Users/kojinn/.claude/scripts/weekly_accounting.log
