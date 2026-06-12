#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_PLIST="$SCRIPT_DIR/com.yuma.agent-runtime-backup.plist"
DEST_PLIST="$HOME/Library/LaunchAgents/com.yuma.agent-runtime-backup.plist"
LABEL="com.yuma.agent-runtime-backup"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents"
cp "$SRC_PLIST" "$DEST_PLIST"

launchctl bootout "$DOMAIN" "$DEST_PLIST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$DEST_PLIST"
launchctl enable "$DOMAIN/$LABEL"

echo "Registered $LABEL"
echo "Schedule: every day at 23:30"
echo "Plist: $DEST_PLIST"
