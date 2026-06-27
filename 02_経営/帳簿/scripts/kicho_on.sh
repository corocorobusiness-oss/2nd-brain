#!/bin/zsh
# 凍結済み weekly-kicho v2 スイッチON
# 2026-06-27以降、会計正本はfreee。旧kichoはCSV/収支管理/日誌を書き換えるため記帳係から外す。
set -euo pipefail

if [ "${KICHO_ALLOW_LAUNCHD_ON:-}" != "1" ]; then
  echo "⏸ weekly-kicho ON は既定停止（2026-06-27 会計正本整理）"
  echo "   会計正本はfreee。旧kichoを再有効化しないでください。"
  echo "   どうしても起動する場合は、Watchtower/台帳/README整合の承認後に KICHO_ALLOW_LAUNCHD_ON=1 を明示してください。"
  exit 0
fi

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
