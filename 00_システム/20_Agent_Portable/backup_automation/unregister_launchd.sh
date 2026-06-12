#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST_PLIST="$HOME/Library/LaunchAgents/com.yuma.agent-runtime-backup.plist"
LABEL="com.yuma.agent-runtime-backup"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$DEST_PLIST" 2>/dev/null || true
launchctl disable "$DOMAIN/$LABEL" 2>/dev/null || true
rm -f "$DEST_PLIST"

echo "Unregistered $LABEL"
