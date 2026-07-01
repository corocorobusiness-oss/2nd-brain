# Daily Note Append CLI v2

作成日: 2026-07-01
分類: 重要
型: オンデマンドCLI
状態: 検証済み / 現行置換前

## Goal固定
既存の `daily_note_append.py` を消さずに、同等以上の安全性を持つ `daily_note_append_v2.py` を横に作り、`/tmp` 検証だけで完成候補にする。

## 本体
`00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py`

## テスト
`00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py`

## 使い方

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py "メモ本文"
```

dry-run:

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py --dry-run "メモ本文"
```

日付指定:

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py --date 2026-07-01 "メモ本文"
```

## 追記先
優先順:

1. `## 💡 メモ / アイデア`
2. `### 💡 思いつきメモ / Inbox`

見出しがない場合、デフォルトでは終了コード2で止まる。
`--create-section` を付けた時だけ、現行見出しを作って追記する。

## 安全設計
- 外部送信なし
- 認証情報なし
- 常駐化なし
- launchd登録なし
- 既存CLIを削除しない
- 現行置換はしない
- デフォルトで重複追記をno-opにする
- `--dry-run` は書き込まない
- 本番日誌への検証書き込みはしない

## 旧版との互換方針
- 基本CLIオプションは旧版と揃える
- 新規作成、現行見出し、旧見出し、重複no-op、複数行、一部重複、見出しなし、`--create-section`、空文字エラーを維持する
- 置き換える場合は、別途人間確認後に `daily_note_append.py` への統合または呼び出し側変更を行う

## 検証済み
- 新規日誌をテンプレートから作成
- 空の `- ` プレースホルダーを置換
- 現行見出しへの追記
- 旧形式見出しへの追記
- 重複追記no-op
- 複数行入力
- 一部重複は新規行だけ追加
- 見出しなしはデフォルトで停止
- `--create-section` で現行見出しを作成
- `--dry-run` は新規ファイルを作らない
- 空文字は終了コード2
- 基本ケースで旧版と出力一致
- 本番日誌コピーを使った影環境比較で旧版と出力一致
- 影環境比較後も本番日誌のSHA256不変

## 止め方
オンデマンドCLIなので、呼ばなければ動かない。
現行CLIは `daily_note_append.py` のままなので、v2を使わなければ既存運用に影響しない。

## 保守
保守担当/確認者: あおい（AI運用）
次回点検日: 2026-08-01

見出し名やデイリーノートテンプレートが変わったら、`daily_note_append_v2.py` の `TARGET_HEADINGS` とテストを更新する。
