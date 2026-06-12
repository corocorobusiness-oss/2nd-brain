---
name: daily-target
description: >-
  今日または明日の日割り目標、月次進捗、デリバリー売上の必要ペースを確認するスキル。
  「今日の日割り」「明日の日割り」「今日いくら稼げばいい」「目標との差分」
  「デリバリー目標」などで使用する。
---

# 日割り確認スキル

## トリガー
- 「今日の日割り」「明日の日割り」等の質問

## 手順
1. **目標ファイル読み込み**: `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/02_経営/目標と計画.md`
2. **当日の目標を特定**: 日割り計画テーブルから該当日を検索
3. **累計進捗を計算**: 当月のデイリーノートから実績を集計
4. **Discord返信**: 日割り目標と累計進捗を返信
