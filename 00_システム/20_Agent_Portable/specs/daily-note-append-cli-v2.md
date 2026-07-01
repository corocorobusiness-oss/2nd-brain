# Daily Note Append CLI v2

作成日: 2026-07-01
分類: 重要
型: オンデマンドCLI
状態: 完成 / 現行差し替え済み

## Goal固定
旧版を `daily_note_append_v1_legacy.py` として残したうえで、現行入口 `daily_note_append.py` を同等以上の安全性を持つv2実装へ差し替える。

## 本体
`00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py`

現行入口 `00_システム/20_Agent_Portable/scripts/daily_note_append.py` は、このv2実装と同一内容。
旧版は `00_システム/20_Agent_Portable/scripts/daily_note_append_v1_legacy.py` に保存。

## テスト
`00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py`

## 使い方

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py "メモ本文"
```

直接実行:

```bash
00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py "メモ本文"
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
- 旧版を `daily_note_append_v1_legacy.py` として残す
- 現行入口 `daily_note_append.py` はv2実装へ差し替え済み
- デフォルトで重複追記をno-opにする
- `--dry-run` は書き込まない
- 本番日誌への検証書き込みはしない
- `--date` は `YYYY-MM-DD` のゼロ埋め形式だけ許可する

## 旧版との互換方針
- 基本CLIオプションは旧版と揃える
- 新規作成、現行見出し、旧見出し、重複no-op、複数行、一部重複、見出しなし、`--create-section`、空文字エラーを維持する
- 見出し境界の判定は旧版と同じく、行頭が `#` の行だけを次見出しとして扱う
- 直接実行できるように実行権限を旧版と同等にする
- 置換後も `daily_note_append.py` と `daily_note_append_v2.py` の内容一致を確認する

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
- 既存日誌への `--dry-run` も書き込まない
- 空文字は終了コード2
- 非ゼロ埋め日付は終了コード2
- テンプレート欠落時は終了コード2で止まり、新規日誌を作らない
- `--allow-duplicate` で既存弾も追記できる
- インデントされた `#` 行を見出し扱いせず、旧版と出力一致
- 直接実行で `--help` が表示できる
- 基本ケースで旧版と出力一致
- 本番日誌コピーを使った影環境比較で旧版と出力一致
- 影環境比較後も本番日誌のSHA256不変

## 止め方
オンデマンドCLIなので、呼ばなければ動かない。
現行CLIを旧版へ戻す場合は、`daily_note_append_v1_legacy.py` の内容を `daily_note_append.py` に戻し、同じテストを再実行する。

## 保守
保守担当/確認者: あおい（AI運用）
次回点検日: 2026-08-01

見出し名やデイリーノートテンプレートが変わったら、`daily_note_append_v2.py` の `TARGET_HEADINGS` とテストを更新する。
