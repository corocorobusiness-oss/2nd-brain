# Codexメイン移行 script-learning dry-run

作成日: 2026-07-01
対象:
- `/Users/kojinn/.claude/scripts/run_script_learning.sh`
- `/Users/kojinn/.claude/scripts/script_learning.md`
- `/Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh`
- `00_システム/20_Agent_Portable/scripts/run_script_learning_codex_dryrun.sh`

## 結論

`script-learning` のCodex dry-run入口を追加し、軽量化後のdry-runはPASSした。

ただし、本番切替は未実施。既存の `run_script_learning.sh`、launchd、Discord投稿、ルールブック更新処理は変更していない。

## 案件分類

分類: **危険**

理由:
- launchd月次ジョブに関係する
- 既存プロンプトがルールブック更新とDiscord投稿を含む
- 台本執筆ルールという制作フロー正本に触れる

## Goal

`script-learning` を本番切替せず、Codexで安全にdry-runできる入口を作り、外部投稿・永続書込なしを証拠で確認する。

## 作ったもの

- `00_システム/20_Agent_Portable/scripts/run_script_learning_codex_dryrun.sh`
- `/Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh`

役割:
- wrapper側で `retention_analysis.json`、制作ログ、既存ルールブックを短く要約する
- 内側Codexには要約だけを渡す
- Codexにはファイル読取、tool call、shell実行、書込、Discord投稿を禁止する
- `RULEBOOK_PATCH` と `DISCORD_PROPOSAL` の構造化ブロックを検証する
- ルールブックと既存ログのmtimeが変わっていないことを確認する

## 既存ジョブの調査結果

既存 `run_script_learning.sh`:
- `claude_run.sh` 経由でClaudeを呼ぶ
- `--permission-mode auto`
- `--allowedTools "mcp__plugin_discord_discord__reply,Bash,Read,Write,Edit,Glob,Grep"`
- 成果物: `台本執筆ルール.md`
- 通知: Discord #レポート
- 成果物mtimeが変わらない場合は自己申告して exit 4

既存 `script_learning.md`:
- `analyze_retention.py` の実行
- `retention_analysis.json` の確認
- 制作ログ全読込
- ルールブック更新
- Discord #レポート投稿

既存ログ:
- `script_learning.log` と `script-learning-out.log` は `You've hit your weekly limit · resets Jul 4 at 9am (Asia/Tokyo)` のみ
- 直近のClaude実行は上限で失敗していた

## 実行した確認

### 構文・配置

```bash
bash -n 00_システム/20_Agent_Portable/scripts/run_script_learning_codex_dryrun.sh
```

結果: exit 0

```bash
install -m 755 /Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/run_script_learning_codex_dryrun.sh /Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh
```

結果: exit 0

```bash
bash -n /Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh
cmp -s 00_システム/20_Agent_Portable/scripts/run_script_learning_codex_dryrun.sh /Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh
```

結果: どちらも exit 0

### dry-run

```bash
/Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh
```

結果: exit 0

検証結果:
- `VALIDATION: OK RULEBOOK_PATCH chars=627`
- `VALIDATION: OK DISCORD_PROPOSAL chars=207 not posted`
- `VALIDATION: OK rulebook unchanged`
- `VALIDATION: OK legacy log unchanged`

Codex出力要旨:
- 維持率ルールは大枠維持
- 2026-06はn=2のため大改訂しない
- 制作ログ由来の再発防止ルールを追記候補にする
- ファイル変更・Discord投稿は未実行

## 修正ループ

### ループ1

失敗:
- 通常sandbox内でdry-run実行
- exit 1
- 内側Codexが `~/.codex/state_5.sqlite` に書けず初期化失敗

対応:
- 同じwrapperを通常権限で再実行

### ループ2

失敗:
- 通常権限では起動したが、内側Codexがファイル探索に時間を使い、必須マーカー返却前に長時間化
- 手動停止、exit 1

対応:
- wrapper側で必要データを事前要約
- Codexには要約だけを渡す
- `ADD_DIRS` 既定を空にし、内側Codexにファイル探索させない

### ループ3

結果:
- exit 0
- 構造化ブロック検証PASS
- ルールブック未更新
- 既存ログ未更新

## 5視点レビュー

### 1. アーキテクト

PASS。既存本番wrapperを触らず、dry-run入口を横に作ったため差し替えリスクが小さい。

### 2. SRE

PASS。launchd未変更、本番ジョブ未変更、mtime検証あり。dry-run失敗もfail-closeしている。

### 3. セキュリティ

PASS。Discord投稿なし、外部送信なし、秘密情報保存なし。証拠は要約のみ。

### 4. QA

PASS WITH NOTE。構文、配置一致、dry-run exit 0、構造化出力、非更新確認は揃った。ただし本番切替判定には別途、人間承認とshadow運用が必要。

### 5. プロダクト運用

PASS。Claude上限で止まっていた月次学習について、Codex側で提案だけ作れることを確認できた。

## 本番化しない条件

以下が残っているため、まだ本番切替しない。

- `run_script_learning.sh` 本体はClaude固定のまま
- Codexでルールブック更新を自動適用する設計は未作成
- Discord投稿の本番送信は未承認
- launchd定期実行のvendor切替は未承認
- 1周期のshadow運用は未実施

## 次の一手

次は `run_script_learning.sh` 本体をいきなり差し替えない。

推奨:
1. `SCRIPT_LEARNING_AGENT_VENDOR=codex` の任意切替を本番wrapperに追加する設計を作る
2. Codex時はAIにWrite/Edit/Discordを渡さず、構造化出力だけにする
3. ルールブック更新とDiscord投稿はwrapper側の決定的処理にする
4. 人間承認後に、手動本番相当実行を1回だけ行う
5. 1周期shadow後にlaunchdデフォルト切替を検討する

## Step2: 本番wrapperへ手動Codex dry-run分岐を追加

実施日: 2026-07-02

変更:
- `00_システム/20_Agent_Portable/scripts/run_script_learning.sh` を管理コピーとして追加
- `/Users/kojinn/.claude/scripts/run_script_learning.sh` へ同内容を反映
- 反映前に `/Users/kojinn/.claude/scripts/run_script_learning.sh.bak-20260702-codex-dispatch` を作成

追加した挙動:
- 既定: `SCRIPT_LEARNING_AGENT_VENDOR` 未指定なら従来通り `claude`
- 手動: `SCRIPT_LEARNING_AGENT_VENDOR=codex` の時だけ `/Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh` へ `exec`
- `codex` は本番更新ではなくdry-run only
- 未知のvendor値はexit 64で停止

本番影響:
- launchd plistは未変更
- `SCRIPT_LEARNING_AGENT_VENDOR` はplistに未指定
- そのため定期実行の既定挙動はClaudeのまま
- ルールブック自動更新、Discord本番投稿、Codexデフォルト切替は未実施

確認:

```bash
bash -n 00_システム/20_Agent_Portable/scripts/run_script_learning.sh
```

結果: exit 0

```bash
SCRIPT_LEARNING_AGENT_VENDOR=codex SCRIPT_LEARNING_CODEX_DRYRUN=/usr/bin/true 00_システム/20_Agent_Portable/scripts/run_script_learning.sh
```

結果: exit 0

出力:

```text
run_script_learning: SCRIPT_LEARNING_AGENT_VENDOR=codex -> dry-run only (/usr/bin/true)
```

```bash
bash -n /Users/kojinn/.claude/scripts/run_script_learning.sh
cmp -s 00_システム/20_Agent_Portable/scripts/run_script_learning.sh /Users/kojinn/.claude/scripts/run_script_learning.sh
SCRIPT_LEARNING_AGENT_VENDOR=codex SCRIPT_LEARNING_CODEX_DRYRUN=/usr/bin/true /Users/kojinn/.claude/scripts/run_script_learning.sh
```

結果: すべて exit 0

ロールバック:

```bash
install -m 755 /Users/kojinn/.claude/scripts/run_script_learning.sh.bak-20260702-codex-dispatch /Users/kojinn/.claude/scripts/run_script_learning.sh
```

判定:
- 手動Codex dry-run分岐の追加は完了
- 本番切替は未実施
- 次に進むなら、`SCRIPT_LEARNING_AGENT_VENDOR=codex /Users/kojinn/.claude/scripts/run_script_learning.sh` の手動dry-runを1回実行して、実際のdry-run wrapperまで通ることを確認する

## Step3: 本番wrapper経由の手動Codex dry-run確認

実施日: 2026-07-02

目的:
- `run_script_learning.sh` に追加した `SCRIPT_LEARNING_AGENT_VENDOR=codex` 分岐が、実際のdry-run wrapperへ届くか確認する
- ルールブック更新とDiscord投稿が起きないことを再確認する

### 1回目: 本番wrapper経由

```bash
SCRIPT_LEARNING_AGENT_VENDOR=codex /Users/kojinn/.claude/scripts/run_script_learning.sh
```

結果: exit 1

確認できたこと:
- 本番wrapperの分岐自体は発火した
- 出力に `SCRIPT_LEARNING_AGENT_VENDOR=codex -> dry-run only` が出た
- `run_script_learning_codex_dryrun.sh` へ到達した

失敗理由:
- このCodexセッションのsandbox内では、内側Codexが `/Users/kojinn/.codex/state_5.sqlite` を開けず初期化失敗
- エラー要旨: `attempt to write a readonly database` / `failed to initialize in-process app-server client`

判断:
- wrapper分岐の配線確認はPASS
- ただし、この環境からの「wrapper経由の実Codex dry-run完走」はWARN

### 2回目: 承認済みdry-run入口の直実行

```bash
/Users/kojinn/.claude/scripts/run_script_learning_codex_dryrun.sh
```

結果: exit 0

検証結果:
- `VALIDATION: OK RULEBOOK_PATCH chars=519`
- `VALIDATION: OK DISCORD_PROPOSAL chars=230 not posted`
- `VALIDATION: OK rulebook unchanged`
- `VALIDATION: OK legacy log unchanged`

Codex出力要旨:
- R1〜R4は据え置き
- 2026-06のQ4は41.6%で前月比+4.1ptだがn=2のため新ルール化しない
- 制作ログ由来の追加候補として、タイトル回収、解説者ゴールデンサンプル準拠、導線レス作法、数値裏取り、列挙系A1書式統一を提案

### Step3判定

PASS:
- 本番wrapperの `codex` 分岐はdry-run入口へ到達する
- dry-run入口そのものは完走する
- ルールブック未更新
- Discord投稿なし
- 既存ログ未更新

WARN:
- このCodexセッションから `SCRIPT_LEARNING_AGENT_VENDOR=codex /Users/kojinn/.claude/scripts/run_script_learning.sh` をそのまま完走させると、内側Codexの状態DB初期化で失敗する

次の本番化前ゲート:
- 通常Terminalまたはlaunchd相当の外側環境で、同じwrapper経由コマンドがexit 0になること
- その場合も `rulebook unchanged` / `not posted` を確認してから次へ進む

## Step4: 外側Terminal検証用ヘルパー

実施日: 2026-07-02

追加:
- `00_システム/20_Agent_Portable/scripts/verify_script_learning_codex_terminal.sh`

目的:
- 通常Terminalで `SCRIPT_LEARNING_AGENT_VENDOR=codex /Users/kojinn/.claude/scripts/run_script_learning.sh` を実行する時、目視ではなく機械判定でPASS/FAILを見る
- `RULEBOOK_PATCH` / `DISCORD_PROPOSAL` / `not posted` / `rulebook unchanged` / `legacy log unchanged` をまとめて検査する

このCodex環境内では、内側Codexの状態DB初期化で失敗する既知制約があるため、ここでは通常Terminal実走の完了証拠はまだ取らない。

通常Terminalで実行するコマンド:

```bash
/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/scripts/verify_script_learning_codex_terminal.sh
```

PASS条件:
- `command_exit=0`
- `OK wrapper reached dry-run branch`
- `OK rulebook patch block validated`
- `OK discord proposal block validated`
- `OK discord proposal not posted`
- `OK rulebook mtime unchanged`
- `OK legacy log mtime unchanged`
- 最後に `PASS script-learning wrapper Codex dry-run gate`

このPASSが出るまでは、Codexデフォルト化、Discord本番投稿、ルールブック自動更新、launchd切替へ進まない。
