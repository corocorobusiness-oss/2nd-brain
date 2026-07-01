# daily-note-append CLI v2 独立レビューパケット 2026-07-01

## レビュー目的
`daily_note_append_v2.py` が、既存の `daily_note_append.py` を置き換える候補として安全かを確認する。

このレビューは、正式置換前の独立確認である。

## Goal固定
既存CLIを壊さず、同等以上の安全性を持つ `daily_note_append_v2.py` を横に作り、`/tmp` 検証だけで完成候補にする。

## レビュー対象ファイル
- `00_システム/20_Agent_Portable/scripts/daily_note_append.py`
- `00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py`
- `00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py`
- `00_システム/20_Agent_Portable/specs/daily-note-append-cli.md`
- `00_システム/20_Agent_Portable/specs/daily-note-append-cli-v2.md`

## 非対象
- 旧版 `daily_note_append.py` の削除
- 現行呼び出しの置換
- 本番日誌への実書き込み
- launchd / cron / 常駐化
- 外部送信
- 認証情報の利用

## 採点基準
以下の観点でレビューする。

1. 旧版と比較して仕様退行がないか
2. 日誌の見出し検出、追記位置、重複no-op、複数行入力が安全か
3. 見出しなし、空文字、日付不正、テンプレートなしでfail-closeするか
4. `--dry-run` が実ファイルを書き換えないか
5. `/tmp` 検証だけで本番日誌へ実書き込みしていないか
6. 置換候補として仕様書と実装が一致しているか
7. テストが重要な正常系・異常系を押さえているか
8. 追加で必要なテスト、WARN、置換前の条件があるか

## 要件・証拠

| 要件ID | 要件 | 証拠 | 状態 |
|---|---|---|---|
| REQ-001 | 旧版を消さずv2を横に作る | `daily_note_append.py` は残し、`daily_note_append_v2.py` を追加 | PASS |
| REQ-002 | 新規日誌をテンプレートから作成する | unittest 13件PASS内で確認 | PASS |
| REQ-003 | 現行見出しと旧見出しへ追記できる | unittest 13件PASS内で確認 | PASS |
| REQ-004 | 重複追記をno-opにする | unittest 13件PASS内で確認 | PASS |
| REQ-005 | 見出しなしはデフォルトで止まる | unittest 13件PASS内で確認 | PASS |
| REQ-006 | `--create-section` 付きなら見出しを作る | unittest 13件PASS内で確認 | PASS |
| REQ-007 | dry-runは書き込まない | unittest、かつ本番日誌dry-run前後SHA256一致 | PASS |
| REQ-008 | 空文字は止まる | unittest 13件PASS内で確認 | PASS |
| REQ-009 | 基本ケースで旧版と出力一致 | unittestのv1/v2 parityテストPASS | PASS |
| REQ-010 | 本番日誌コピーで旧版と出力一致し、本番実体を変えない | `/tmp` 影環境でv1/v2出力SHA256一致、本番日誌SHA256不変 | PASS |
| REQ-011 | 非ゼロ埋め日付を拒否する | `2026-7-1` は終了コード2、ファイル未作成 | PASS |
| REQ-012 | インデントされた `#` 行を旧版と同じ扱いにする | v1/v2 parityテストPASS | PASS |
| REQ-013 | 直接実行できる | `daily_note_append_v2.py --help` 終了コード0 | PASS |
| REQ-014 | テンプレート欠落時は新規日誌を作らない | unittest 13件PASS内で確認 | PASS |
| REQ-015 | `--allow-duplicate` の挙動を確認する | unittest 13件PASS内で確認 | PASS |

## 実行証拠

```text
python3 -m unittest "00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py"
結果: Ran 13 tests ... OK
```

```text
env PYTHONPYCACHEPREFIX=/tmp/codex-pycache python3 -m py_compile \
  "00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py" \
  "00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py"
結果: 終了コード0
```

```text
git diff --check -- \
  "00_システム/20_Agent_Portable/specs/daily-note-append-cli-v2.md" \
  "01_プロジェクト/AI自動化/AI開発フロー_初回運用レビュー_2026-07-01.md"
結果: 終了コード0
```

```text
python3 "00_システム/20_Agent_Portable/scripts/daily_note_append_v2.py" \
  --date 2026-07-01 --dry-run "v2 dry-run checksum test"
結果: 終了コード0 / status: dry-run
```

本番日誌 `05_日誌/2026-07-01.md` のSHA256:

```text
063157a1652ddaabb05a02d3a4dbc6bee2784cf723bab1129ef80ec1bd945d3a
```

影環境比較:

```text
対象: 本番日誌コピー
入力: shadow compare memo
v1_returncode: 0
v2_returncode: 0
v1/v2 output sha256:
fe55a39b9e12d9186f9d4de4002505d507d3e7d0216c4f7a5d160f15a7bb9d81
v1_v2_output_equal: true
本番日誌SHA256: 不変
```

WARN対応後の追加確認:

```text
python3 -m unittest "00_システム/20_Agent_Portable/scripts/test_daily_note_append_v2.py"
結果: Ran 13 tests ... OK

影環境比較:
入力: shadow compare memo after warn fix
v1_returncode: 0
v2_returncode: 0
v1/v2 output sha256:
91762fd20c95ef27aea5f180c1868a87719cc67c37bcb94891d7881db12d606f
v1_v2_output_equal: true
本番日誌SHA256: 063157a1652ddaabb05a02d3a4dbc6bee2784cf723bab1129ef80ec1bd945d3a

非ゼロ埋め日付:
入力日付: 2026-7-1
invalid_date_exit: 2
file_absent_check_exit: 0

直接実行:
daily_note_append_v2.py --help
direct_help_exit: 0
```

独立レビューWARNへの対応:

```text
WARN: 非ゼロ埋め日付が通る
対応: ^\d{4}-\d{2}-\d{2}$ で事前チェックし、2026-7-1 を終了コード2にした

WARN: v2に実行権限がない
対応: chmod +x し、直接実行 --help のテストを追加

WARN: インデントされた # 行を見出し扱いする仕様退行
対応: 見出し境界を旧版と同じ line.startswith("#") に戻し、v1/v2 parityテストを追加

不足テスト:
既存日誌dry-run、非ゼロ埋め日付、インデント#行、直接実行、テンプレート欠落、--allow-duplicate を追加
```

## 独立レビュー結果
- 1回目レビュー: WARN
- WARN対応: 完了
- 再レビュー: PASS
- 重大指摘: 0
- 完成判定: 完成可

## 既知のWARN / 未解決
- v2自体は完成可。
- 現行CLIは未置換。
- 置換する場合は別作業として人間確認後に行い、置換後に同じ13件テストと本番日誌コピー比較を再実行する。

## レビュー担当への依頼
上記ファイルと証拠をもとに、次を返す。

```text
判定: PASS / WARN / FAIL

重大指摘:
- 

仕様退行:
- 

不足テスト:
- 

置換前に必要な条件:
- 

完成判定:
完成可 / 完成候補のまま / 差し戻し
```
