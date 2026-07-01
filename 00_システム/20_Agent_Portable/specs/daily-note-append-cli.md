# Daily Note Append CLI

作成日: 2026-07-01
分類: 重要
型: オンデマンドCLI

## 目的
今日のデイリーノートがなければテンプレートから作成し、指定テキストをメモ欄へ安全に追記する。

## 本体
`00_システム/20_Agent_Portable/scripts/daily_note_append.py`

## 使い方

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append.py "メモ本文"
```

dry-run:

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append.py --dry-run "メモ本文"
```

日付指定:

```bash
python3 00_システム/20_Agent_Portable/scripts/daily_note_append.py --date 2026-07-01 "メモ本文"
```

## 追記先
優先順:

1. `## 💡 メモ / アイデア`
2. `### 💡 思いつきメモ / Inbox`

見出しがない場合、デフォルトでは非0終了して止まる。
`--create-section` を付けた時だけ、現行見出しを作って追記する。

## 安全設計
- 外部送信なし
- 認証情報なし
- 常駐化なし
- launchd登録なし
- デフォルトで重複追記をno-opにする
- `--dry-run` で書き込み前に差分確認できる
- 本番日誌への検証書き込みはしない

## 止め方
オンデマンドCLIなので、呼ばなければ動かない。
完全に止める場合は、本体ファイルを退避する。

## 壊れた時
- `--dry-run` で対象ファイル、日付、見出し、差分を確認する
- 見出しが見つからない場合は、日誌テンプレートまたは対象日誌の見出し名を確認する
- テンプレートが読めない場合は、`00_システム/Templates/Daily_Note_Template.md` の存在を確認する

## 検証済み
- 日誌なしケース: テンプレートから作成
- 現行見出しへの追記
- 旧形式見出しへの追記
- 重複追記no-op
- 見出しなしエラー
- 空文字エラー
- `--create-section`
- 本番日誌へのdry-run

## 保守
保守担当/確認者: あおい（AI運用）
次回点検日: 2026-08-01

見出し名やデイリーノートテンプレートが変わったら、このCLIの `DEFAULT_HEADINGS` とテストを更新する。
