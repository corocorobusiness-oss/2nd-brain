# Codexメイン移行 Step5 Claude自動化棚卸し

作成日: 2026-07-01

## 結論

LaunchAgentsとして存在する自動化29件を確認した。現時点では、自動化の停止・起動・削除・書き換えは行っていない。

分類結果は以下。

| 分類 | 件数 | 意味 |
|---|---:|---|
| `CLAUDE_P_DIRECT` | 8 | スクリプト内で `claude -p` を直接呼ぶ |
| `CLAUDE_HARNESS` | 3 | `claude_run.sh` 経由でClaudeを呼ぶ |
| `AGENT_RUN_CLAUDE` | 2 | `agent-run` だが `AGENT_VENDOR=claude` 固定 |
| `CLAUDE_CHANNELS` | 1 | `claude --channels` を使う |
| `CLAUDE_CHANNELS_DEPENDENT` | 1 | Channelsリスナーを監視・再起動する |
| `NO_AI_CLI` | 14 | ラベル名は `com.claude.*` でもAI CLIは呼ばない |

つまり、Codexメイン化で実際に移行対象になるのは15件。残り14件は名前にClaudeが入っているだけで、急いで触る必要はない。

## 起動状態メモ

`launchctl list` 上では、今回確認した `com.claude.*` / `com.korokoro.*` のロード中ジョブは確認できなかった。

一方で `launchctl print-disabled` では以下が有効扱いで見えていた。

- `com.claude.freee-uncleared-monitor`
- `com.claude.thread-format-learning`
- `com.claude.vault-autocommit`
- `com.claude.vault-mirror`

そのため、実際に止める・切り替える前には、対象ラベルごとに `launchctl print` で再確認する。

## Claude依存ジョブ

| ラベル | 分類 | 危険度 | 方針 |
|---|---|---|---|
| `com.claude.corpus-collect` | `CLAUDE_P_DIRECT` | 中 | 本体は決定的処理。Claude依存は報告文生成・通知寄りなので候補 |
| `com.claude.daily-dashboard` | `CLAUDE_P_DIRECT` | 中 | 候補。ただしGmail等の外部情報を読むため先に手動dry-run |
| `com.claude.daily-knowledge-extract` | `CLAUDE_HARNESS` | 中 | 候補。既に安全wrapper経由なので後回しでもよい |
| `com.claude.discord-monitor` | `CLAUDE_CHANNELS` | 高 | 触らない。Claude Channels依存が強い |
| `com.claude.gmail-cleanup` | `CLAUDE_P_DIRECT` | 高 | 触らない。Gmail操作系 |
| `com.claude.knowledge-gardener` | `CLAUDE_HARNESS` | 中 | 候補。既に安全wrapper経由なので後回しでもよい |
| `com.claude.listener-watchdog` | `CLAUDE_CHANNELS_DEPENDENT` | 高 | 触らない。Channels監視系 |
| `com.claude.monthly-accounting` | `CLAUDE_P_DIRECT` | 高 | 触らない。会計系 |
| `com.claude.script-learning` | `CLAUDE_HARNESS` | 中 | 候補。出力先と差分を確認してから |
| `com.claude.thread-format-learning` | `AGENT_RUN_CLAUDE` | 中 | 最初の小さいパイロット候補 |
| `com.claude.trash-cleanup` | `CLAUDE_P_DIRECT` | 高 | 触らない。削除系 |
| `com.claude.uber-earnings` | `CLAUDE_P_DIRECT` | 中 | 候補。ただし外部データ依存のため後回し |
| `com.claude.uber-weekly-plan` | `CLAUDE_P_DIRECT` | 中 | 候補。ただし外部データ依存のため後回し |
| `com.claude.vault-snapshot` | `AGENT_RUN_CLAUDE` | 高 | 触らない。TCC / Full Disk Access回避のためClaude固定 |
| `com.claude.weekly-accounting` | `CLAUDE_P_DIRECT` | 高 | 触らない。会計系 |

## すぐ触らないもの

以下はAI CLIを呼ばないため、Codex移行の本筋ではない。ラベル名変更は将来できるが、launchd変更になるので今は不要。

- `com.claude.demaecan-reminder`
- `com.claude.freee-uncleared-monitor`
- `com.claude.monthly-backup`
- `com.claude.neta-retrain`
- `com.claude.neta-slate-reminder`
- `com.claude.nightly-refresh`
- `com.claude.restore-drill`
- `com.claude.satellite-autocommit`
- `com.claude.ssd-backup`
- `com.claude.vault-autocommit`
- `com.claude.vault-mirror`
- `com.claude.weekly-stocktake`
- `com.claude.youtube-revenue`
- `com.korokoro.yuma-watchtower`

## 次の一手

最初のパイロットは `com.claude.thread-format-learning` がよい。

理由:

- すでに `agent-run` 経由なので、Claude直叩きより差し替え面が小さい
- `AGENT_VENDOR=claude` 固定を外すだけではなく、Codex非対応のClaude専用フラグを整理できる
- まず手動dry-runで、launchdは触らずに出力だけ確認できる

ただし、いきなり定期実行へ切り替えない。次は手動でCodex dry-runし、出力フォーマット・書き込み先・通知有無を確認してから、スクリプト更新に進む。

## Step6メモ: Codex dry-runの確認結果

2026-07-01にCodex Desktop内から `agent-run` の `AGENT_VENDOR=codex` で読み取りdry-runを試した。

結果:

- `agent-run` からCodex CLI自体は起動できた
- `AGENT_RUN_CODEX_WORKDIR=/Users/kojinn/2nd-Brain-master` では、YouTube作業場側の参照ができずNG
- `AGENT_RUN_CODEX_WORKDIR=/Users/kojinn/Projects/youtube` でも、読み取り確認はNG
- `codex exec --ignore-user-config` でもNG
- 明示的にローカルshell確認を指示したところ、内側Codexのsandbox適用で `sandbox-exec: sandbox_apply: Operation not permitted` が出た

解釈:

これは `thread-format-learning` の候補選定が間違いというより、**Codex Desktop内からさらにCodex CLIを起動する入れ子sandbox問題**の可能性が高い。launchdや通常Terminalから直接 `agent-run` を起動した場合とは条件が違う。

次に進むなら、いきなりlaunchdへ入れない。通常Terminalまたはlaunchd相当の外側環境で、書き込み・Discord投稿なしのdry-run専用入口を作ってから確認する。

## Step7メモ: dry-run入口の追加

2026-07-01に、`thread-format-learning` を本番切替せず検証するためのdry-run入口を追加した。

追加・変更:

- `/Users/kojinn/.claude/scripts/run_thread_format_learning_codex_dryrun.sh`
  - Codexで `thread-format-learning.md` を実行する検証専用入口
  - ウォッチリスト更新なし
  - Discord投稿なし
  - 永続ログ追記なし
  - `WATCHLIST_UPDATE` / `DISCORD_PROPOSAL` の構造だけ検証
- `/Users/kojinn/agent-adapters/bin/agent-run`
  - Codex分岐で `AGENT_RUN_CODEX_ADD_DIRS` / `--add-dir` をサポート
  - Codex成功時は起動ログを混ぜず、最後の回答だけを標準出力へ返す

確認済み:

- `bash -n /Users/kojinn/agent-adapters/bin/agent-run`
- `bash -n /Users/kojinn/.claude/scripts/run_thread_format_learning_codex_dryrun.sh`
- `AGENT_VENDOR=codex /Users/kojinn/agent-adapters/bin/agent-run -p 'Reply exactly: CLEAN_OK'` が `CLEAN_OK` のみ返す
- `AGENT_VENDOR=codex AGENT_RUN_CODEX_ADD_DIRS=/Users/kojinn/Projects/youtube /Users/kojinn/agent-adapters/bin/agent-run -p 'Reply exactly: ADD_DIR_OK'` が `ADD_DIR_OK` のみ返す

未実施:

- ~~`run_thread_format_learning_codex_dryrun.sh` の本番相当dry-run実行~~ → 実施済み。結果は下記。

理由:

Codex Desktop内から内側Codex CLIを起動すると入れ子sandbox問題が出るため、この検証は通常Terminalまたはlaunchd相当の外側環境で行う。

## Step8メモ: dry-run実行結果

2026-07-01に `run_thread_format_learning_codex_dryrun.sh` を実行した。

結果:

- exit code: `2`
- ウォッチリスト更新: なし
- Discord投稿: なし
- 永続ログ追記: なし
- `WATCHLIST_UPDATE`: 出力なし
- `DISCORD_PROPOSAL`: 出力なし

Codexの出力要旨:

- 必須Readができなかったためfail-close
- 正本・ウォッチリスト・コーパスを検証できていない状態でマーカーを出すと危険なので停止
- ローカル読取の実行環境で `sandbox-exec: sandbox_apply: Operation not permitted`

wrapper検証:

- `WATCHLIST_UPDATE` が無いため `VALIDATION: FAIL WATCHLIST_UPDATE block missing`
- `DISCORD_PROPOSAL` が無いため `VALIDATION: OK DISCORD_PROPOSAL absent, no post would be made`

判断:

これは本番移行NG。だが、失敗時に誤った監視リスト更新やDiscord投稿をしなかったため、dry-run入口の安全ガードは有効。

次に進む条件:

- Codexが必須ファイルを読める外側環境で再dry-runする
- `WATCHLIST_UPDATE` が正常に出る
- wrapper検証が `VALIDATION: OK WATCHLIST_UPDATE` になる
- Discord提案が出てもdry-runでは投稿されないことを再確認する
