#!/bin/zsh
# Yuma OS Watchtower OFF（停止・ゾンビ防止: unload＋ファイル削除＋台帳更新）
set -euo pipefail

LABEL="com.korokoro.yuma-watchtower"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$DEST" 2>/dev/null || true
rm -f "$DEST"

echo "Yuma OS Watchtower OFF"
echo "台帳（01_プロジェクト/AI自動化/導入済み.md）の状態も停止へ更新すること"

