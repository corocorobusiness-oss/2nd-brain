#!/bin/zsh
# Yuma OS Watchtower ON（毎日8:30のヘルスチェックを有効化）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.korokoro.yuma-watchtower"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents" "$SCRIPT_DIR/logs"
cp "$SCRIPT_DIR/$LABEL.plist" "$DEST"
launchctl bootout "$DOMAIN" "$DEST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$DEST"
launchctl enable "$DOMAIN/$LABEL"

echo "Yuma OS Watchtower ON（毎日8:30）"
echo "確認: launchctl list | grep yuma-watchtower"
echo "台帳（01_プロジェクト/AI自動化/導入済み.md）の状態も更新すること"

