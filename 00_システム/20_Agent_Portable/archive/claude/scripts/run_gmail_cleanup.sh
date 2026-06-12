#!/bin/bash
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:$PATH"
cd /Users/kojinn
claude -p "$(cat /Users/kojinn/.claude/scripts/weekly_gmail_cleanup.md)" --allowedTools "mcp__claude_ai_Gmail__gmail_search_messages,mcp__claude_ai_Gmail__gmail_read_message,mcp__playwright__browser_navigate,mcp__playwright__browser_snapshot,mcp__playwright__browser_click,mcp__playwright__browser_tabs,mcp__playwright__browser_fill_form,mcp__plugin_discord_discord__reply,Bash,Read,Write,Glob,Grep" 2>&1 | tee /Users/kojinn/.claude/scripts/gmail_cleanup.log
