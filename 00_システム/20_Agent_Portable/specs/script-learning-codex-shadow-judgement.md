# script-learning Codex shadow判定手順

作成日: 2026-07-02
判定予定日: 2026-08-02
対象ジョブ: `com.claude.script-learning`
関連:
- `codex-main-vendor-neutral-migration.md`
- `06_エージェント運用/50_レポート/2026-07-01_Codexメイン移行_script-learning_dryrun.md`
- `01_プロジェクト/AI自動化/並走台帳.md`

## 目的

`script-learning` を、既定Claude実行からCodex実行へ進めてよいかを、1月次サイクルの実証結果で判定する。

この手順は本番切替ではない。判定日に証拠をそろえ、Codexデフォルト化のGo/No-Goを決めるためのもの。

## 案件分類

分類: **危険**

理由:
- launchd月次ジョブに関係する
- Discord投稿に関係する
- 台本執筆ルールという制作フロー正本に関係する
- Codex/Claudeの実行経路差し替えに関係する

## 判定日の前提

判定日は `2026-08-02`。

判定対象の1サイクル:
- 旧系統: `2026-08-01 11:00` の既定Claude月次実行
- 新系統: 通常Terminalから手動実行するCodex dry-run

## 絶対にやらないこと

判定前に次をしない。

- launchd plistへ `SCRIPT_LEARNING_AGENT_VENDOR=codex` を追加しない
- Codexを既定実行にしない
- Discord本番投稿をしない
- ルールブックを自動更新しない
- Claude本番経路を停止、削除、置換しない
- `SCRIPT_LEARNING_CODEX_DRYRUN` overrideを使わない
- `SCRIPT_LEARNING_CODEX_WORKDIR` / `SCRIPT_LEARNING_CODEX_ADD_DIRS` を使わない
- sandboxを `read-only` 以外にしない

## 判定日に集める証拠

### 1. 旧系統Claudeの実行結果

確認対象:

```text
/Users/kojinn/.claude/scripts/script-learning-out.log
/Users/kojinn/.claude/scripts/script-learning-error.log
/Users/kojinn/.claude/scripts/script_learning.log
```

確認すること:
- `2026-08-01 11:00` 付近に実行痕跡がある
- exit codeまたは失敗痕跡が分かる
- 上限、認証、プロンプト未読込、挨拶だけ、空出力で終わっていない
- Discord #レポート投稿の有無が説明できる
- ルールブック更新の有無が説明できる

生ログをSecond Brainに貼らない。保存するのはマスク済み要約だけ。

### 2. 新系統Codex dry-run

通常Terminalで実行する。

```bash
SCRIPT_LEARNING_AGENT_VENDOR=codex /Users/kojinn/.claude/scripts/run_script_learning.sh
```

または、検証ゲート込みで実行する。

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/verify_script_learning_codex_terminal.sh
```

確認すること:
- exit 0
- `SCRIPT_LEARNING_AGENT_VENDOR=codex -> dry-run only` が出る
- `VALIDATION: OK summary secret scan clean`
- `VALIDATION: OK sandbox locked read-only`
- `VALIDATION: OK add_dirs empty`
- `VALIDATION: OK RULEBOOK_PATCH ...`
- `VALIDATION: OK DISCORD_PROPOSAL ... not posted`
- `VALIDATION: OK rulebook unchanged`
- `VALIDATION: OK rulebook hash unchanged`
- `VALIDATION: OK legacy log unchanged`
- `VALIDATION: OK legacy log hash unchanged`
- terminal gate最終行が `PASS script-learning wrapper Codex dry-run gate`

### 3. 本番不変確認

比較対象:

```text
/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md
/Users/kojinn/.claude/scripts/script_learning.log
```

確認すること:
- Codex dry-run後にルールブックのmtime/hashが変わっていない
- Discordへ本番投稿していない
- legacy logを更新していない
- Vault正本に秘密情報、生ログ、トークン、Cookieを保存していない

## 比較観点

| 観点 | Claude既定実行 | Codex dry-run | 判定 |
|---|---|---|---|
| 実行可否 |  |  | 未確認 |
| exit code |  |  | 未確認 |
| 上限/認証エラー |  |  | 未確認 |
| 出力形式 |  |  | 未確認 |
| ルールブック更新案の質 |  |  | 未確認 |
| Discord投稿案の質 |  |  | 未確認 |
| 外部投稿なし |  |  | 未確認 |
| 永続書込なし |  |  | 未確認 |
| mtime/hash不変 |  |  | 未確認 |
| secret scan |  |  | 未確認 |
| rollback手順 |  |  | 未確認 |

## Go条件

次をすべて満たした場合だけ、Codexデフォルト化の設計ステップへ進める。

- 通常Terminal gateがexit 0
- Codex dry-runが構造化出力を返す
- Discord本番投稿が発生していない
- ルールブック、legacy log、関係ファイルのmtime/hashが不変
- secret scanがPASS
- sandboxが `read-only`
- `SCRIPT_LEARNING_CODEX_ADD_DIRS` が空
- 旧系統Claudeとの出力差分が説明できる
- 未説明WARNがない
- 未確認REQがない
- 本番切替差分とrollback手順が書ける
- 独立レビューで重大指摘0
- 祐馬さんが本番切替を明示承認する

## No-Go条件

次が1つでもあれば本番切替へ進まない。

- 通常Terminal gateがFAIL
- Codex dry-runがexit 0でない
- 自然文だけで構造化ブロックがない
- `RULEBOOK_PATCH` または `DISCORD_PROPOSAL` が検証できない
- Discord投稿、永続書込、削除、会計書込が発生した
- ルールブックまたはlegacy logのmtime/hashが変わった
- secret scanがFAIL
- sandboxが `read-only` 以外
- 追加dirが残っている
- Codexが生ログ、秘密情報、Cookie、トークン、認証済みURLを扱った疑いがある
- Claude専用フラグをCodexへ渡す必要が残っている
- rollback手順がない
- 独立レビューで重大指摘が残る
- 祐馬さんの明示承認がない

## 判定後に更新する場所

Go / No-Go のどちらでも更新する。

- `06_エージェント運用/50_レポート/2026-07-01_Codexメイン移行_script-learning_dryrun.md`
- `01_プロジェクト/AI自動化/並走台帳.md`
- `01_プロジェクト/AI自動化/導入済み.md`
- `06_エージェント運用/00_司令塔/NOW.md`
- `06_エージェント運用/00_司令塔/期日タスク.md`
- 必要なら `06_エージェント運用/00_司令塔/作業ログ_ツバキとあおい.md`

## 判定メモ雛形

```text
## 2026-08-02 script-learning Codex shadow判定

判定者:
実行環境:

旧系統Claude:
- 実行日時:
- exit/status:
- 出力要約:
- 投稿/更新:
- 問題:

新系統Codex dry-run:
- 実行コマンド:
- exit/status:
- safety validations:
- RULEBOOK_PATCH要約:
- DISCORD_PROPOSAL要約:
- 投稿/更新:
- 問題:

比較:
- 出力品質:
- 安全性:
- 運用性:
- 残WARN:

独立レビュー:
- 実施有無:
- 指摘:
- 重大指摘0か:

判定:
- Go / No-Go / 継続shadow:
- 理由:
- 次アクション:
- 人間承認:
```
