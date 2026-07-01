# Mask Slurs CLI v2

作成日: 2026-07-01
分類: 通常
型: オンデマンドCLI
状態: v2検証候補 / 現行未差し替え

## Goal固定
現行 `mask_slurs.py` を消さず、同じ `qa_check.py` の `SLUR_RE` を単一ソースとして使う、より安全な `mask_slurs_v2.py` を横に作る。

## 本体
`00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs_v2.py`

現行入口:
`00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs.py`

現時点では、現行入口は未差し替え。

## テスト
`00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/test_mask_slurs_v2.py`

## 使い方

標準入力:

```bash
cat in.md | python3 00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs_v2.py
```

ファイル入力・ファイル出力:

```bash
python3 00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs_v2.py in.md -o out.md
```

dry-run:

```bash
python3 00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs_v2.py in.md -o out.md --dry-run
```

置換文字を変える:

```bash
python3 00_システム/20_Agent_Portable/codex-skills-ready/creative-thread-gen/mask_slurs_v2.py in.md --replacement "[MASKED]"
```

## 安全設計
- 外部送信なし
- 認証情報なし
- 常駐化なし
- launchd登録なし
- 現行 `mask_slurs.py` は削除しない
- 判定パターンは `qa_check.py` の `SLUR_RE` を使い、二重管理しない
- 出力ファイルは一時ファイル経由で保存し、途中失敗時に壊れにくくする
- 既存出力ファイルの権限は維持する
- `--dry-run` は出力ファイルを書き込まない
- 置換文字は正規表現置換テンプレートではなくリテラルとして扱う
- 入力ファイル欠落、出力ディレクトリ欠落、`qa_check.py` 欠落、空の置換文字、`SLUR_RE` に当たる置換文字は終了コード2で止める

## 旧版との互換方針
- 標準入力から読み、標準出力へマスク済みテキストを出す基本動作は維持する
- `-o/--out` でファイルへ書く基本動作は維持する
- `qa_check.py` の `SLUR_RE` を単一ソースにする方針を維持する
- import API `mask(text) -> (masked_text, count)` を維持する
- 基本ケースでは旧版と標準出力が一致する
- `--dry-run`、`--replacement`、失敗時のfail-closeをv2で追加する

## 検証済み
- 標準入力から標準出力へマスクできる
- 許可文脈はマスクしない
- 基本ケースで旧版と標準出力一致
- ファイル出力できる
- 入力ファイルと出力ファイルが同じでも壊さず置換できる
- 既存出力ファイルの権限を維持する
- `--dry-run` は出力ファイルを作らない
- `--replacement` で置換文字を変更できる
- `--replacement` は `\1` などをリテラルとして扱う
- 空の置換文字は終了コード2で止まる
- `SLUR_RE` に当たる置換文字は終了コード2で止まる
- 入力ファイル欠落は終了コード2で止まる
- 出力ディレクトリ欠落は終了コード2で止まる
- `qa_check.py` 欠落は終了コード2で止まる
- 直接実行で `--help` が表示できる
- import API `mask(text)` が旧版と同じ形式で使える

## 差し替え条件
現行入口を差し替える場合は、次を満たしてから行う。

- 現行 `mask_slurs.py` を `mask_slurs_v1_legacy.py` として保存する
- テストの旧版比較先が `mask_slurs_v1_legacy.py` を見る状態になっていることを確認する
- `mask_slurs.py` と `mask_slurs_v2.py` の内容一致を確認する
- v2テストを再実行する
- 実行権限を確認する
- `/tmp` のコピーで旧版と新版の出力差分を確認する
- `creative-thread-gen/SKILL.md` の呼び出し説明を必要に応じて更新する
- 差し替え後の戻し方を記録する

## 止め方
オンデマンドCLIなので、呼ばなければ動かない。
現行未差し替えのため、通常運用はまだ `mask_slurs.py` を使う。

## 保守
保守担当/確認者: あおい（AI運用）
次回点検日: 2026-08-01

`qa_check.py` の `SLUR_RE` が変更されたら、このv2のテストも再実行する。
