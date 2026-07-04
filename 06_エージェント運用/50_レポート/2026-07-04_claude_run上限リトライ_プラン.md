# claude_run.sh上限リトライ追加＋weekly-accountingハーネス化 プラン

作成日: 2026-07-04  
実行者: Codex  
状態: STEP A（プラン作成のみ・本番変更なし）

## 0. 結論

推奨は **「claude_run.shの上限検知を強化し、近いリセット時刻だけ最大1回リトライできる仕組みを入れる。ただし既定はリトライOFF、ジョブ別opt-in」**。

`weekly-accounting` は会計書込ジョブなので、今回は **claude_run.sh経由化してexit codeを温存するだけ** にする。リトライは入れない。理由は、Claudeがfreeeへ一部書込した後に上限・通信断・レポート失敗へ落ちた場合、「完全に何もしていない失敗」と機械的に区別できないため。`freee_registered_txns.json` とfreee側の同日同額チェックは重複防止として有効だが、リトライを自動許可できるほどの原子性はない。

STEP Aでは実装していない。`~/.claude/scripts/`、launchd、freee、Discord送信には触っていない。

## 1. 調査範囲

読み取り確認した主な対象:

| 対象 | 確認したこと |
|---|---|
| `/Users/kojinn/.claude/scripts/claude_run.sh` | 共通ハーネス。exit 2/3/4の分類、通知、tee経由でも`PIPESTATUS[0]`を拾う設計 |
| `/Users/kojinn/.claude/scripts/run_daily_knowledge_extract.sh` | `claude_run.sh --label daily-knowledge-extract` 経由 |
| `/Users/kojinn/.claude/scripts/run_knowledge_gardener.sh` | `claude_run.sh` を2段で呼ぶ。戻り値伝播に追加リスクあり |
| `/Users/kojinn/.claude/scripts/run_script_learning.sh` | Claude経路は`claude_run.sh`経由、Codex shadow経路あり |
| `/Users/kojinn/.claude/scripts/run_weekly_accounting.sh` | 生`claude -p ... | tee`でハーネス外 |
| `/Users/kojinn/.claude/scripts/weekly_accounting.md` | freee書込プロンプト、重複防止、失敗時ルール |
| `02_経営/帳簿/README.md` | freee正本、weekly-accountingだけがfreee書込、会計ジョブは自己修復しないルール |
| `00_システム/10_Agent/workflows.md` | freee書込時の台帳必読・不整合時停止ルール |
| `/Users/kojinn/.claude/scripts/limit_redrive.py` | redrive修理済みの上限検知パターン、attempts非消費の参考実装 |

## 2. 現状構造

### claude_run.sh

`claude_run.sh` はすでに「沈黙失敗を大声で失敗にする」土台を持っている。

- `claude -p` の標準出力・標準エラーを一時ファイルへ保存しつつ、`PIPESTATUS[0]`でClaude本体の終了コードを保持する。
- 上限系を検知するとDiscordレポートへ自己申告し、`exit 2`。
- 認証系を検知すると`exit 3`。
- 出力が空、または「承知しました」系だけなら`exit 4`。
- それ以外のClaude非ゼロは元の終了コードを返す。

不足しているのは以下。

1. 上限時のリトライがない。
2. テスト用にClaude本体・通知・時刻・sleepを差し替えるフックがない。
3. 現行の上限正規表現が、実ログで出ている `You've hit your session limit` / `You've hit your weekly limit` を確実には拾えない。

### 利用wrapper

| wrapper | 現状 | リトライ適性 |
|---|---|---|
| `run_daily_knowledge_extract.sh` | `claude_run.sh`経由。Vault知識ベース書込と#メモ投稿がある | 低リスクではない。純粋な上限出力だけなら近距離1回リトライ可 |
| `run_knowledge_gardener.sh` | `claude_run.sh`をKG/BIの2段で呼ぶ | 先に戻り値伝播の修正が必要。前段失敗を後段・最後の`exit 0`で隠す余地あり |
| `run_script_learning.sh` | Claude経路は`claude_run.sh`経由。Codex shadow分岐あり | Claude経路だけopt-in可。週次上限のように遠いリセットはリトライ不可 |
| `run_weekly_accounting.sh` | 生`claude -p ... | tee`。exit codeがteeに潰され得る | ハーネス化は必要。ただし自動リトライは禁止推奨 |

## 3. 追加発見

### F1: 上限検知の現行パターンが実エラーに弱い

`claude_run.sh`の上限検知は `usage limit`、`plan limit`、`rate limit`、`too many requests`、`429`、`quota`、日本語の上限表現などを見ている。一方、実際に出ている代表例は次の形式。

- `You've hit your session limit · resets 1:10am (Asia/Tokyo)`
- `You've hit your weekly limit · resets Jul 4 at 9am (Asia/Tokyo)`

このため、リトライ以前に **上限分類そのものをredrive修理済みの`is_limit_output()`相当に寄せる** 必要がある。

### F2: knowledge-gardenerはハーネス経由でも失敗を隠す可能性がある

`run_knowledge_gardener.sh` は2段構成で、各段の戻り値を変数には入れているが、通常失敗・上限失敗を最終exitへそのまま反映しない経路がある。`claude_run.sh`側を強化しても、wrapper側が失敗を潰すなら穴が残る。

この案件の実装フェーズでは、少なくともsandboxで次を確認する。

- KG段が`exit 2`ならBI段へ進まない、または最終`exit 2`になること。
- BI段が`exit 2`なら最終`exit 2`になること。
- greeting-onlyの既存判定を壊さないこと。

### F3: weekly-accountingはハーネス外かつteeでexit codeを潰し得る

`run_weekly_accounting.sh`は生`claude -p`を`tee`へ渡している。`set -o pipefail`もなく、Claudeが上限・認証・通常失敗してもlaunchd上は成功扱いになる可能性がある。

これは「会計が1週飛ぶのに見えない」穴なので、ハーネス化の優先度は高い。

## 4. リトライ設計案の比較

| 案 | 内容 | 良い点 | 弱点 | 判定 |
|---|---|---|---|---|
| A. in-process有界sleep | 上限メッセージからリセット時刻を読めた時だけ、近距離ならsleepして最大1回再実行 | 変更点が少ない。launchd/plistを増やさない。redriveの「上限中はattemptsを燃やさない」に近い | 長時間sleepはlaunchdジョブを保持する。ジョブ別安全性が必要 | **推奨。ただしopt-in・近距離のみ** |
| B. 状態ファイル＋Watchtower/既存見張り引き取り | 上限時にpending stateを書き、別ジョブが後で回収 | 長時間sleepしない。監視しやすい | 新しい状態管理・回収経路・二重起動制御が必要。今回の修理範囲として大きい | 将来候補 |
| C. リトライせず検知のみ | 上限検知を強化し、大声で失敗にするだけ | 最も安全。会計ジョブ向き | d-k-eのような近距離セッション上限を自動回復できない | weekly-accountingには採用 |

## 5. 推奨設計

### 5.1 claude_run.sh

実装フェーズでは次の方針を推奨する。

1. 上限分類をredrive修理済み実装に寄せる。
   - 追加候補: `weekly limit`、`session limit`、`temporarily limiting`、`you've hit your weekly limit`、`you've hit your session limit`。
2. リセット時刻パーサを追加する。
   - `resets 1:10am (Asia/Tokyo)` のような同日/翌日候補。
   - `resets Jul 4 at 9am (Asia/Tokyo)` のような日付つき候補。
   - 解析不能ならリトライしない。
3. リトライは既定OFF。
   - `CLAUDE_RUN_RETRY_ON_LIMIT=1` のような明示opt-inがある時だけ有効。
4. リトライは最大1回。
5. リセットまでの待ち時間が閾値以内の時だけ待つ。
   - 推奨既定: `CLAUDE_RUN_RETRY_MAX_WAIT_SEC=7200`（2時間）。
   - 週次上限など数日先は即`exit 2`。
6. 「純粋な上限出力」だけリトライ対象にする。
   - 出力が短く、上限メッセージ以外の実作業進捗・ツール実行らしき文言がない場合のみ。
   - 判定が曖昧ならリトライしない。
7. 多重起動ガードとの整合。
   - 既存wrapper側にlockがない場合、in-process sleep中に次の同一ジョブが始まらない頻度設計か確認する。
   - d-k-eのように日次なら最大2時間sleepでも次回と重なりにくい。
   - 高頻度ジョブには使わない。

### 5.2 テスト用フック

sandboxで本物のClaude/freee/Discordを使わず検証するため、以下のフックを推奨する。

| 変数 | 既定 | 目的 |
|---|---|---|
| `CLAUDE_RUN_BIN` | 現行の`claude`探索結果 | fake claudeを差し込む |
| `CLAUDE_RUN_NOTIFY_CMD` | `discord_notify.sh` | 通知を/tmpログへ逃がす |
| `CLAUDE_RUN_RETRY_ON_LIMIT` | `0` | ジョブ別opt-in |
| `CLAUDE_RUN_RETRY_MAX_WAIT_SEC` | `7200` | 近距離判定 |
| `CLAUDE_RUN_TEST_NOW_EPOCH` | 未設定 | リセット時刻パースの固定テスト |
| `CLAUDE_RUN_SLEEP_BIN` または `CLAUDE_RUN_SLEEP_SCALE` | 通常`sleep` | テストで実sleepしない |

既定値は現行挙動と同じにする。環境変数を指定しない本番ジョブは、分類強化以外の挙動が変わらない状態から始める。

## 6. weekly-accountingの二重計上安全分析

### 現行プロンプト上の安全弁

`weekly_accounting.md`には次の安全弁がある。

- `freee_registered_txns.json`を読み、既登録IDは二重登録しない。
- 台帳が読めない/不整合なら登録しない。
- freeeに同日同額の取引がないかGETで確認してから登録する。
- 登録後に台帳へ追記する。
- 削除は禁止。
- Gmail/freeeエラーは報告対象。

これは重複防止として重要。ただし、自動リトライの安全性を完全には証明しない。

### 危険シナリオ

| シナリオ | 起きること | 自動リトライ可否 |
|---|---|---|
| Claudeが何も始める前に上限 | freee書込なし | 理論上は可。ただし外部から確実判定しにくい |
| freeeへ登録成功後、台帳追記前に失敗 | freeeには存在、台帳にはない | 同日同額GETで防げる可能性はあるが、完全ではない |
| 台帳追記後、Discord報告前に失敗 | 会計処理は済み、報告だけ欠落 | リトライすると再確認・再報告の挙動が読みにくい |
| 複数件中の途中で失敗 | 一部登録済み、一部未登録 | 人間確認なしの再実行はリスクが高い |
| freee APIの一時エラー/曖昧応答 | 登録成否が不明 | 自動リトライ禁止 |

### 推奨

`weekly-accounting` は **リトライOFF固定**。

やることは次に限定する。

1. `run_weekly_accounting.sh`を`claude_run.sh --label weekly-accounting`経由にする。
2. 生`claude -p ... | tee`を撤去し、exit codeを温存する。
3. allowedToolsは現行と同等に維持する。
4. 上限・認証・通常失敗は大声で失敗させる。
5. 自動再実行はしない。

将来リトライを許すなら、先に「書込前preflight」「処理開始/完了マーカー」「freee deal IDの確定記録」「台帳のatomic更新」「途中失敗時のreconcile専用モード」を設計する必要がある。

## 7. ジョブ別影響分析

| ジョブ | 変更案 | 安全判定 |
|---|---|---|
| daily-knowledge-extract | `CLAUDE_RUN_RETRY_ON_LIMIT=1`をwrapperへopt-in候補。純粋な上限出力だけ近距離1回 | 条件付き可。Vault/Discord書込があるため、部分実行疑いならリトライしない |
| knowledge-gardener | まず戻り値伝播を直す。その後、各段にopt-inを検討 | 条件付き可。ただし2段構成なのでPhase 1では必ず専用テスト |
| script-learning | Claude経路だけopt-in候補。Codex shadow分岐は触らない | 条件付き可。週次上限は遠距離なのでリトライされない設計にする |
| weekly-accounting | `claude_run.sh --label weekly-accounting`へハーネス化。リトライOFF | ハーネス化は必要。リトライは禁止推奨 |

## 8. 実装フェーズ案

### Phase 1: sandbox実装とテスト（次のGO対象）

触ってよい場所を `/tmp/claude-run-retry-test/` のみに限定する。

1. 本番対象を/tmpへ複製。
   - `claude_run.sh`
   - `run_daily_knowledge_extract.sh`
   - `run_knowledge_gardener.sh`
   - `run_script_learning.sh`
   - `run_weekly_accounting.sh`
   - `weekly_accounting.md`（読み取り参照用）
2. fake claudeを作る。
   - 成功出力。
   - 通常失敗。
   - 認証失敗。
   - no-op/greeting-only。
   - 近距離session limit -> 2回目成功。
   - 遠距離weekly limit -> リトライなし。
   - リセット時刻なしlimit -> リトライなし。
   - 進捗出力を含むlimit -> リトライなし。
3. fake notifyを作る。
   - Discord送信せず、通知文を/tmpログへ保存。
4. fake sleepを使う。
   - 実際に1時間以上待たない。
5. weekly-accountingはfreeeツールを構造的に渡さない。
   - sandboxではallowedToolsを空またはfakeのみ。
   - リトライOFFでlimit時に1回だけ失敗することを確認。
6. knowledge-gardenerの戻り値伝播テストを追加。
   - KG段limitで最終exit 2。
   - BI段limitで最終exit 2。

テストケース:

| ID | ケース | 期待 |
|---|---|---|
| T1 | 通常成功 | rc=0、通知なし |
| T2 | 通常失敗 | 元rcを返す、リトライなし |
| T3 | 認証失敗 | rc=3、リトライなし |
| T4 | no-op/greeting-only | rc=4 |
| T5 | 近距離session limit + opt-in | fake sleep後に1回だけ再実行し、成功ならrc=0 |
| T6 | 遠距離weekly limit + opt-in | rc=2、リトライなし |
| T7 | limitだがreset不明 | rc=2、リトライなし |
| T8 | partial output + limit | rc=2、リトライなし |
| T9 | weekly-accounting limit | rc=2、リトライなし、freee呼び出しなし |
| T10 | knowledge-gardener KG段limit | 最終rc=2、BI段へ進まないか失敗を保持 |
| T11 | knowledge-gardener BI段limit | 最終rc=2 |

### Phase 2: 本番反映（Fable検証PASS後、別GO）

1. `.bak-20260704-claude-run-retry` を作成。
2. `claude_run.sh`へ分類強化・opt-inリトライ・テストフックを反映。
3. `run_weekly_accounting.sh`を`claude_run.sh --label weekly-accounting`経由に変更。リトライOFF。
4. 必要に応じて以下を反映。
   - `run_daily_knowledge_extract.sh`: 近距離上限1回リトライをopt-in。
   - `run_script_learning.sh`: Claude経路だけopt-in。
   - `run_knowledge_gardener.sh`: 戻り値伝播修正 + opt-inはFable検証後に判断。
5. `bash -n`で構文確認。
6. 実ジョブ実行・launchd操作・Discord送信・freee API呼び出しはしない。
7. `01_プロジェクト/AI自動化/導入済み.md` と作業ログを更新。

### Phase 3: 自然実行観察

| 観察対象 | 最速/次回 | 見ること |
|---|---|---|
| daily-knowledge-extract | 毎日23:30 | 上限がなければ通常成功。近距離上限時は1回だけ待つ |
| knowledge-gardener | 定期実行日に観察 | 2段の戻り値が隠れない |
| script-learning | 次回月次/定期 | Codex shadow分岐を壊していない |
| weekly-accounting | 月曜9:05 | 失敗時exitが隠れない。会計二重登録なし |

weekly-accountingの自然実行は、実装週に適用するか、次週から適用するかを本番GO時に選ぶ。月曜直前に反映するより、前日までにFable検証を完了しておく方が安全。

## 9. rollback

Phase 2で本番反映する場合の戻し方:

1. 対象ファイルを`.bak-20260704-claude-run-retry`から復元。
2. `bash -n`で構文確認。
3. launchdは操作しない。次回自然実行から旧挙動へ戻る。
4. `導入済み.md`にrollback実施を追記。
5. 作業ログに復元対象と理由を記録。

rollback対象候補:

- `/Users/kojinn/.claude/scripts/claude_run.sh`
- `/Users/kojinn/.claude/scripts/run_weekly_accounting.sh`
- `/Users/kojinn/.claude/scripts/run_daily_knowledge_extract.sh`
- `/Users/kojinn/.claude/scripts/run_knowledge_gardener.sh`
- `/Users/kojinn/.claude/scripts/run_script_learning.sh`

## 10. 台帳・Watchtower影響

| 項目 | 影響 |
|---|---|
| `導入済み.md` | 本番反映時に必須更新。`weekly-accountingはリトライOFF`を明記 |
| Watchtower | STEP Aでは変更不要。将来、`claude_run`のexit 2頻発やretry待機を検知したくなったら別案件 |
| launchd plist | 今回は変更不要 |
| freee | STEP A/Phase 1では呼び出し禁止。Phase 2も実行禁止。自然実行観察のみ |
| Discord | STEP A/Phase 1では実送信禁止。Phase 2も手動送信なし。自然実行時の既存通知のみ |

## 11. 完了条件

この案件全体の完了条件:

1. `claude_run.sh`が実際の `session limit` / `weekly limit` を上限として分類できる。
2. 近距離リセットだけ、opt-inジョブで最大1回リトライできる。
3. 遠距離・解析不能・部分実行疑いはリトライせず、大声で失敗する。
4. `weekly-accounting`は`claude_run.sh`経由になり、exit codeが隠れない。
5. `weekly-accounting`に自動リトライが入っていない。
6. `knowledge-gardener`の戻り値伝播穴がsandboxで検証され、必要なら修正されている。
7. `.bak`、rollback、台帳、作業ログが揃っている。
8. Fable独立検証がPASSしている。

## 12. 次に出すべきGO文面

```text
Phase 1 実装承認（claude_run上限リトライ＋weekly-accountingハーネス化・/tmp複製限定）:
対象範囲: /tmp/claude-run-retry-test/ 内でのsandbox実装とfake claude/fake notifyによるdry-runテストまで。
含める内容:
- claude_run.shの上限検知強化（session limit / weekly limit含む）
- job別opt-inの近距離リセット最大1回リトライ
- CLAUDE_RUN_BIN / CLAUDE_RUN_NOTIFY_CMD / 時刻固定 / fake sleep等のテストフック
- weekly-accountingはclaude_run経由化案のみ。リトライOFFを維持
- knowledge-gardenerの戻り値伝播テスト

触ってよい場所: /tmp/claude-run-retry-test/ のみ
触ってはいけない場所:
- 本番 ~/.claude/scripts/
- launchd
- freee API
- Discord実送信
- Google Drive/証憑/会計ファイルの本番書込

検証方法:
T1〜T11のfakeテスト全PASS。
本番対象ファイルのmtime/size不変を確認。

戻し方:
/tmp/claude-run-retry-test/ を削除するだけ。
```

## 13. STEP Aの未実施リスト

未実施:

- 実装
- 本番スクリプト変更
- launchd操作
- Claude/agent-runの実行
- freee API呼び出し
- Discord送信
- ファイル削除/移動

STEP Aの成果物は本プランのみ。
