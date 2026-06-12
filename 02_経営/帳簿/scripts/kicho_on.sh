#!/bin/zsh
# weekly-kicho v2 スイッチON（毎週月曜9:30の自動記帳を有効化）
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.korokoro.kicho-weekly"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"
DOMAIN="gui/$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents" "$SCRIPT_DIR/../logs"
cp "$SCRIPT_DIR/$LABEL.plist" "$DEST"
launchctl bootout "$DOMAIN" "$DEST" 2>/dev/null || true
launchctl bootstrap "$DOMAIN" "$DEST"
launchctl enable "$DOMAIN/$LABEL"

echo "✅ weekly-kicho ON（毎週月曜9:30・次回実行を待つ）"
echo "   確認: launchctl list | grep kicho"
echo "   台帳（01_プロジェクト/AI自動化/導入済み.md）の状態も「稼働中」へ更新すること"
