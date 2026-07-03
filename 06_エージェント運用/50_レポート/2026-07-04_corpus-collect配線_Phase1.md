# corpus-collect配線 Phase 1 レポート

作成日: 2026-07-04
実行者: Codex
対象: `run_corpus_collect.sh` の `/tmp` 複製に対する dry-run/no-post入口 + agent-run通知レッグ検証

## 判定

**未完成 / 要確認。**

`/tmp` 複製への実装と、NO_POST / mock agent-run の砂場テストはPASS。
ただし、完了条件3つ目の「本物の agent-run を `--allowedTools ""` で1回だけ疎通確認」が、Claude未ログインでFAILした。

```text
Not logged in · Please run /login
```

これは本番スクリプトの不具合ではなく、このCodex実行環境から見えるClaude runtimeのログイン状態が不足しているため。
完了条件「テスト3種PASS」は満たしていないので、Phase 2本番反映には進めない。

## 案件分類

- 分類: 危険案件のPhase 1
- 理由: 本線は自動化ジョブ、外部投稿、Claude/agent-run実行経路に関わるため
- 今回の承認範囲: `/tmp/agent-run-corpus-test/` のみの実装・検証 + 本レポート保存
- 危険操作承認: なし

## Goal

`corpus-collect` の最後の通知レッグを `AGENT_VENDOR=claude agent-run` 経由にできるかを、Discord投稿不能・本番不変の状態で証拠化する。

## やったこと

`/tmp/agent-run-corpus-test/run_corpus_collect.sh` にだけ、次を実装した。

- `CORPUS_COLLECT_AGENT_VENDOR` 追加（既定 `claude`）
- `CORPUS_COLLECT_AGENT_RUN` 追加（既定 `/Users/kojinn/agent-adapters/bin/agent-run`）
- `CORPUS_COLLECT_DRY_RUN` 追加
- `CORPUS_COLLECT_NO_POST` 追加
- `CORPUS_COLLECT_ALLOWED_TOOLS` 追加（空文字を許容）
- `CORPUS_COLLECT_CORPUS` / `SCRAPER` / `MASKER` / `DISCOVER` / `LOG` / `LOCK` の環境変数化
- `DRY_RUN=1` では `CORPUS` が `/tmp/agent-run-corpus-test/` 配下でない場合に停止
- `NO_POST=1` では `agent-run` を呼ばず、MSGだけをログとstdoutに出す
- 通常経路では `AGENT_VENDOR="$CORPUS_COLLECT_AGENT_VENDOR" "$AGENT_RUN" ...` を呼ぶ

## 触った場所

- `/tmp/agent-run-corpus-test/run_corpus_collect.sh`
- `/tmp/agent-run-corpus-test/bin/scraper_ok.py`
- `/tmp/agent-run-corpus-test/bin/masker_passthrough.py`
- `/tmp/agent-run-corpus-test/bin/discover_dummy.py`
- `/tmp/agent-run-corpus-test/bin/agent-run-mock`
- `/tmp/agent-run-corpus-test/run_phase1_tests.sh`
- `06_エージェント運用/50_レポート/2026-07-04_corpus-collect配線_Phase1.md`

## やっていないこと

- 本番 `~/.claude/scripts/run_corpus_collect.sh` の編集
- `~/Projects/youtube/スレコーパス` への書き込み
- launchd操作
- Discord投稿
- 本番wrapper反映
- Phase 2 / Phase 3

## テスト結果

| ID | 内容 | コマンド/対象 | 結果 | 判定 |
|---|---|---|---|---|
| T1 | tmp複製スクリプト構文チェック | `bash -n /tmp/agent-run-corpus-test/run_corpus_collect.sh` | rc=0 | PASS |
| T2 | テストランナー構文チェック | `bash -n /tmp/agent-run-corpus-test/run_phase1_tests.sh` | rc=0 | PASS |
| T3 | NO_POST=1で投稿せずMSGを出す | `/tmp/agent-run-corpus-test/run_phase1_tests.sh` | `PASS no-post` | PASS |
| T4 | mock agent-runが `AGENT_VENDOR=claude` とDiscord reply tool引数を受ける | `/tmp/agent-run-corpus-test/run_phase1_tests.sh` | `PASS mock-agent-run` | PASS |
| T5 | 本物のagent-runを `--allowedTools ""` で1回だけ疎通確認 | `AGENT_VENDOR=claude /Users/kojinn/agent-adapters/bin/agent-run ... --allowedTools ''` | rc=1 / `Not logged in · Please run /login` | FAIL |

T3/T4の出力:

```text
PASS no-post
PASS mock-agent-run
ALL TMP TESTS PASS
```

## 本番不変確認

本番スクリプトは編集していない。確認時点の代表値:

```text
/Users/kojinn/.claude/scripts/run_corpus_collect.sh 1782642191 11003
/Users/kojinn/agent-adapters/bin/agent-run 1782889840 6377
```

参考として、本番コーパスの代表ファイルはメタデータ確認のみ行った（内容読み取り・書き込みなし）:

```text
/Users/kojinn/Projects/youtube/スレコーパス/_収集キュー.txt 1782648051 2091
/Users/kojinn/Projects/youtube/スレコーパス/_収集済みURL.txt 1782648051 503
```

## 秘密情報・個人情報

- トークン、Cookie、認証情報は出力・保存していない
- Discord APIや投稿ツールは呼んでいない
- 実agent-run疎通は `--allowedTools ""` で実施し、失敗はログイン不足で停止

## 未解決

### BLOCKER

Codex実行環境から見えるClaude runtimeが未ログイン。
そのため、本物のagent-run疎通テストが未完了。

### 次に必要な判断

FableまたはClaude側のログイン済み環境で、同じ疎通確認を1回だけ再実行するか判断する。

再実行候補:

```text
AGENT_VENDOR=claude /Users/kojinn/agent-adapters/bin/agent-run \
  -p '疎通確認です。外部ツールは使わず、AGENT_RUN_SMOKE_OK と1行だけ返してください。' \
  --permission-mode auto \
  --allowedTools ''
```

期待結果:

```text
AGENT_RUN_SMOKE_OK
```

## 完成判定

未完成。

理由:

- `NO_POST` と mock agent-run の砂場テストはPASS
- しかし、ブリーフの完了条件である「テスト3種PASS」のうち、本物agent-run疎通がFAIL
- Phase 2本番wrapper反映へ進む証拠がまだ足りない

