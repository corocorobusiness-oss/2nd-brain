#!/bin/bash
# ネタリサーチ予測モデルの週次再学習
# 1) YouTubeチャンネル全動画の最新統計を取得
# 2) feature_db.json を再構築（人物別・時代別・カテゴリ別実績を更新）
set -e
SCRIPTS="/Users/kojinn/.claude/skills/neta-research/scripts"
LOG="/Users/kojinn/.claude/scripts/neta-retrain.log"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') 再学習開始 ====="
  cd "$SCRIPTS"
  /usr/bin/python3 fetch_channel_stats.py
  /usr/bin/python3 build_feature_db.py | head -8
  echo "--- 予測vs実績の答え合わせ ---"
  /usr/bin/python3 verify_predictions.py
  echo "===== 完了 ====="
} >> "$LOG" 2>&1
