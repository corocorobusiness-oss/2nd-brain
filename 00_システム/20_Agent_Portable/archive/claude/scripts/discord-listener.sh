#!/bin/bash
# Discord常駐リスナー - claude --channels で直接監視

export HOME="/Users/kojinn"
export PATH="/Users/kojinn/.nvm/versions/node/v24.14.1/bin:/usr/local/bin:/usr/bin:/bin"
export LANG="ja_JP.UTF-8"

security unlock-keychain -p "" ~/Library/Keychains/login.keychain-db 2>/dev/null

cd "$HOME"
exec /usr/bin/expect -f /Users/kojinn/.claude/scripts/discord-listener.exp
