#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_PLIST="$SCRIPT_DIR/com.yuma.weekly-kicho.plist"
DEST_PLIST="$HOME/Library/LaunchAgents/com.yuma.weekly-kicho.plist"
LABEL="com.yuma.weekly-kicho"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$SCRIPT_DIR/../logs"
cp "$SRC_PLIST" "$DEST_PLIST"

launchctl bootout "$DOMAIN" "$DEST_PLIST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$DEST_PLIST"
launchctl enable "$DOMAIN/$LABEL"

echo "Registered $LABEL"
echo "Schedule: every Monday at 09:30"
echo "Plist: $DEST_PLIST"

