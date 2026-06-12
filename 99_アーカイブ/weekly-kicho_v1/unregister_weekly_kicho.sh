#!/bin/zsh
set -euo pipefail

LABEL="com.yuma.weekly-kicho"
DOMAIN="gui/$(id -u)"
DEST_PLIST="$HOME/Library/LaunchAgents/com.yuma.weekly-kicho.plist"

launchctl bootout "$DOMAIN" "$DEST_PLIST" 2>/dev/null || true
launchctl disable "$DOMAIN/$LABEL" 2>/dev/null || true
rm -f "$DEST_PLIST"

echo "Unregistered $LABEL"

