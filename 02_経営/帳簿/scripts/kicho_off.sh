#!/bin/zsh
# weekly-kicho v2 スイッチOFF（自動記帳を停止・ゾンビ防止の3点セット: unload＋ファイル削除＋台帳更新）
set -euo pipefail

LABEL="com.korokoro.kicho-weekly"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

launchctl bootout "$DOMAIN" "$DEST" 2>/dev/null || true
rm -f "$DEST"

echo "🛑 weekly-kicho OFF"
echo "   台帳（01_プロジェクト/AI自動化/導入済み.md）の状態も「停止」へ更新すること"
