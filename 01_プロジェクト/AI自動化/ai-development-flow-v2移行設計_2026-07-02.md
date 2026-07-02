# ai-development-flow V2 移行設計 2026-07-02

## 目的

`ai-development-flow` に、会話から開発依頼ブリーフを作る「AI開発依頼ヒアリング補助 / plan-only受付」を組み込み、ユーザーが毎回テンプレを手入力しなくても、安全に案件分類・Goal固定・設計へ進める状態にする。

旧版は削除せず、復旧できる形で退避する。

## 案件分類

分類: 危険寄りの重要

理由:
- `ai-development-flow` は開発・自動化・正本ルール変更の入口であり、変更の影響範囲が広い
- スキル正本は `/Users/kojinn/agent-skills/ai-development-flow`
- Codex側は `/Users/kojinn/.codex/skills/ai-development-flow -> /Users/kojinn/agent-skills/ai-development-flow` のsymlink運用
- 入口ルールを誤ると、依頼文承認、実装開始承認、本番操作承認が混ざる

この設計書作成はVault内ドキュメント追加のみ。実際のスキル差し替え、旧版退避、symlink変更、本番化はまだ行わない。

## Goal固定

Goal:
`ai-development-flow` の入口名を維持したまま、V2で会話ヒアリングから plan-only の開発依頼ブリーフ作成を行えるようにし、旧版へ戻せる退避・検証手順まで定義する。

完成条件:
- V2の入口仕様が定義されている
- 旧版退避先と戻し方が定義されている
- 差し替え前後の検証項目が定義されている
- 人間承認が必要な操作が分かれている
- 実装前に止まる条件が明記されている

やらないこと:
- この設計段階では `/Users/kojinn/agent-skills` を編集しない
- この設計段階では `.codex/skills` symlinkを変更しない
- この設計段階では旧版を退避しない
- この設計段階ではV2を本線化しない

本番化しない条件:
- 5回試用で、質問過多、未確認の握りつぶし、危険トリガー漏れが出る
- `handoff_mode: plan_only` が出ない
- `OK` や `いいよ` が本番操作承認として扱われる
- 旧版へ戻す手順が未検証
- Codex runtimeで `ai-development-flow` が見えない

## 移行ステータス

V2移行では、「作った」「差し替えた」「試用中」「正式採用」「移行完了」を分ける。

| ステータス | 意味 | 次へ進む条件 |
|---|---|---|
| V1稼働中 | 現行 `ai-development-flow` が本線 | V2設計承認 |
| V2候補作成中 | V2文面を横に作るが、現行入口は未変更 | V2候補レビュー完了 |
| V1退避済み | V1をlegacyへ退避し、hash/diff一致を確認済み | 移行実施承認 |
| V2反映済み | 現行入口へV2を反映済み。ただし正式採用ではない | runtime/dry-run gate PASS |
| V2試用中 | 5回の実利用試用中 | 5件ログ完了、重大問題0 |
| V2正式採用 | 人間承認つきでV2を本線採用 | 台帳/現在地/判断ログ整合 |
| V2正式採用・移行完了 | 完了条件を全て満たした状態 | 次回点検へ |
| V2縮小継続 | 入口ヒアリングだけ縮小して継続 | 縮小案を再評価 |
| V2廃止 | V2を採用しない | V1復旧確認 |
| V1復旧済み | V1を本線へ戻し、旧挙動確認済み | 再設計するなら新規レビュー |

`V2反映済み` と `V2正式採用・移行完了` は別物として扱う。

## 移行フェーズ

### Phase A. 設計承認

目的、非対象、変更対象、完了条件、人間承認ポイントを固定する。

完了条件:
- V2仕様が1ファイル内で読める
- 旧版退避、戻し方、試用ログ、正式採用/中止/復旧条件が定義済み
- 人間が「設計として進めてよい」と承認済み

### Phase B. V2候補作成

現行入口は触らず、V2候補文面を横に作る。

作るもの:
- `SKILL.md` のV2候補文面
- `agents/openai.yaml` のV2候補文面

この時点では `ai-development-flow` はまだV1稼働中。

### Phase C. V1退避とhash固定

V1をlegacy配下へコピーし、現行との一致証跡を残す。

完了条件:
- legacy配下に `SKILL.md` と `agents/openai.yaml` が存在
- 退避前後のhashまたはdiff一致
- Codex symlinkが壊れていない

### Phase D. V2差し替え

人間の「移行実施承認」後に、現行入口へV2を反映する。

この承認でまとめてよい操作:
- V1退避
- V2反映
- Vault控え同期

この承認に含めない操作:
- 本番データ書き込み
- 外部送信
- 自動実行ON
- 削除
- 会計登録
- 認証変更

### Phase E. runtime / dry-run gate

V2反映直後に、配線と挙動を確認する。

完了条件:
- fresh runtimeで `SKILL_VISIBLE=YES`
- dry-run 5ケース全PASS
- `handoff_mode: plan_only` が出る
- `OK` / `いいよ` を本番操作承認として扱わない
- 正本と控えの差分が意図通り

### Phase F. 5回試用

状態は `V2試用中`。

5件すべてを試用ログへ残す。重大問題が1件でも出た場合は、正式採用しない。

### Phase G. 正式化 / 縮小 / 廃止 / V1復旧判定

5回試用後、人間承認つきで次のどれかを選ぶ。

- V2正式採用
- V2縮小継続
- V2廃止
- V1復旧

### Phase H. 復旧確認

V2で問題が出た場合、V1へ戻せることを確認する。

完了条件:
- legacyから現行入口へV1を戻せる
- fresh runtimeで `SKILL_VISIBLE=YES`
- 旧挙動dry-runがPASS
- 戻した理由と再挑戦条件が記録済み

### Phase I. 移行完了記録

`V2正式採用・移行完了` と言う前に、台帳、現在地、判断ログ、作業ログ、移行設計の状態を揃える。

## V2の基本方針

入口名は維持する。

```text
ai-development-flow = 最新安定版
legacy/v1_legacy_YYYYMMDD = 旧版控え
```

ただし、最初からディレクトリをリネームしない。

理由:
- Codex側のsymlinkは `ai-development-flow` 名を見ている
- 入口名を変えると既存の呼び方が割れる
- 旧版退避と新旧差し替えは、人間承認後に小さく行う方が安全

## V2の変更点

### Phase -1. AI開発依頼ヒアリング補助

`ai-development-flow` の本体処理に入る前に、明示トリガーがある時だけ発動する。

発動例:
- 「これ開発依頼にして」
- 「仕組み化したい」
- 「ai-development-flowに回したい」
- 「この話を開発テンプレに落として」

やること:
1. 会話を短い開発ブリーフへ圧縮する
2. 判断に影響する不足だけ質問する
3. 質問は最大2ラウンド、1回3問まで
4. 安全項目は推測で埋めない
5. 未確認は `未確認` として残す
6. 危険トリガー候補を明記する
7. 最後に、依頼文として `ai-development-flow` に渡してよいかだけ確認する

### V2でも本体に残す責務

以下はヒアリング補助ではなく、`ai-development-flow` 本体で行う。

- 案件分類
- Goal固定
- 必要なエージェント/レビュー編成
- リサーチ範囲と打ち切り条件
- 実装計画
- 検証
- 完成判定
- 危険案件の人間承認要否

## 承認の分離

V2では承認を3つに分ける。

### 1. 依頼文承認

意味:
マスク済みの開発依頼ブリーフを `ai-development-flow` 本体へ渡し、案件分類と設計へ進めてよい。

許可しないこと:
- 実装開始
- 本番書き込み
- 外部送信
- 削除
- 自動化ON
- 正本ルール変更

固定文:

```text
この依頼文を ai-development-flow に渡して、案件分類と設計に進めていい？

※これは「依頼文を渡す承認」であり、実装開始・本番書き込み・外部送信・削除・自動化ONの承認ではありません。
危険操作が必要になった場合は、その操作ごとに、差分・影響範囲・戻し方を出してから別途確認します。
```

### 2. 実装開始承認

意味:
設計、触る場所、検証方法、戻し方を見たうえで、実装に入ってよい。

必要条件:
- 触ってよい場所が明確
- 触ってはいけない場所が明確
- 実装計画あり
- 確認方法あり
- 危険操作の有無が明確

### 3. 危険操作承認

意味:
特定の本番操作を実行してよい。

必要条件:
- 操作対象
- 差分
- 影響範囲
- 戻し方
- 実行タイミング
- 二重実行防止
- 人間承認ログ

`OK`、`いいよ`、`承認` だけでは危険操作承認として扱わない。

## 旧版退避設計

### 原則

- 旧版は削除しない
- いきなり現行ディレクトリをリネームしない
- 先に退避コピーを作る
- 退避コピーの存在と内容一致を確認する
- その後に現行入口へV2を反映する
- 差し替え後に戻し方を実際に確認する

### 退避候補

スキル正本側:

```text
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_YYYYMMDD/
```

Vault控え側:

```text
00_システム/20_Agent_Portable/codex-skills-ready/ai-development-flow/legacy/v1_legacy_YYYYMMDD/
```

理由:
- `ai-development-flow` ディレクトリ名を維持できる
- Codex側symlinkを壊さない
- 旧版を同じスキル配下に残せる
- 復旧時に現行ファイルへ戻しやすい

### 退避対象

最低限:
- `SKILL.md`
- `agents/openai.yaml`

存在する場合:
- `scripts/`
- `refs/`
- `templates/`
- その他V1運用に必要なファイル

### 退避前チェック

- `git -C /Users/kojinn/agent-skills status --short -- ai-development-flow`
- `find /Users/kojinn/agent-skills/ai-development-flow -maxdepth 3 -type f`
- `diff` または `shasum` で退避コピーと現行の一致確認
- Vault控えとの `diff -qr`

### 退避後チェック

- legacy配下に `SKILL.md` と `agents/openai.yaml` がある
- 現行 `ai-development-flow/SKILL.md` はまだV1のまま
- Codex側 `~/.codex/skills/ai-development-flow` のsymlinkが壊れていない
- runtimeで `SKILL_VISIBLE=YES` が維持される

## V2反映設計

### 反映対象

スキル正本:

```text
/Users/kojinn/agent-skills/ai-development-flow/SKILL.md
/Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml
```

Vault控え:

```text
00_システム/20_Agent_Portable/codex-skills-ready/ai-development-flow/SKILL.md
00_システム/20_Agent_Portable/codex-skills-ready/ai-development-flow/agents/openai.yaml
```

運用正本:

```text
01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md
01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md
```

### SKILL.mdに入れる内容

追加する内容は短くする。

- Phase -1: AI開発依頼ヒアリング補助
- `handoff_mode: plan_only`
- 依頼文承認と実装承認を分ける
- 本分類、Goal固定、危険承認は本体で再実施
- 未確認と危険トリガー候補を握りつぶさない

フルルールはVault正本に置き、スキル側へ長文を重複しない。

### openai.yamlに入れる内容

説明文を短く更新する。

例:

```text
Use $ai-development-flow to turn vague system-building requests into a plan-only development brief when needed, then run risk classification, goal fixing, bounded repair loops, evidence gates, review, and completion checks.
```

## 検証設計

### dry-runケース

最低限:
1. 普通の開発依頼
2. 危険案件（freee/会計/本番書き込み）
3. 曖昧承認（OK/いいよ）
4. 触ってよい場所が不明
5. 明示トリガーなしの雑談

### PASS条件

- 明示トリガーなしではヒアリングを勝手に始めない
- 質問は最大2ラウンド、1回3問まで
- 未確認を推測で埋めない
- 危険トリガー候補が出る
- `handoff_mode: plan_only` が出る
- `OK` を本番操作承認として扱わない
- 本分類とGoal固定を本体で再実施する
- `SKILL_VISIBLE=YES` が維持される
- Vault控えとスキル正本の差分が意図通り

### 現時点のdry-run状態

現時点で記録済み:
- 普通の開発依頼
- 危険案件（freee/会計/本番書き込み）
- 曖昧承認（OK/いいよ）

未実施:
- 触ってよい場所が不明
- 明示トリガーなしの雑談

V2反映後の試用開始前に、5ケース全てを再実施する。

## 5回試用ログ

保存先候補:

```text
01_プロジェクト/AI自動化/ai-development-flow-v2試用ログ_2026-07.md
```

ログ形式:

```text
## Trial-001

日時:
入力タイプ: 普通 / 危険 / 曖昧承認 / 場所不明 / 雑談
入力要約:
質問ラウンド数:
質問数:
未確認を未確認のまま残したか: YES / NO
危険トリガー期待値:
危険トリガー検出結果:
見落とし:
handoff_mode: plan_only / missing
OK/いいよを危険承認扱いしなかったか: YES / NO
手戻り:
手入力より速かったか: YES / NO / 不明
ユーザー負担: 1-5
秘密情報・個人情報を保存していないか: YES / NO
判定: PASS / WARN / FAIL
次アクション:
```

5回試用の差し戻し条件:
- `handoff_mode: plan_only` が出ない
- `OK` / `いいよ` を実装開始、本番書き込み、外部送信、削除、自動化ONの承認として扱う
- 危険トリガーを1件でも見落とす
- 未確認項目をAIが推測で埋める
- 明示トリガーなしでヒアリングを開始する
- 秘密情報、個人情報、生ログを保存する
- 試用ログが欠ける

## Go / No-Go判定

5回試用後、次のどれかを選ぶ。

| 判定 | 条件 | 次アクション |
|---|---|---|
| V2正式採用 | 5回試用で重大問題0、dry-run 5ケースPASS、復旧手順検証済み | 移行完了記録へ進む |
| V2縮小継続 | 便利だが質問過多、またはWARNあり | 発動条件や質問数を縮小して再試用 |
| V2廃止 | 手入力より遅い、負担増、効果薄い | V1へ戻す |
| V1復旧 | 危険トリガー漏れ、承認混同、未確認握りつぶしが発生 | legacyからV1復旧 |

正式採用には人間承認が必要。

## 移行完了条件

全て満たした時だけ `V2正式採用・移行完了` と言う。

- V1 legacyが存在し、現行V1とのhashまたはdiff一致証跡がある
- V2反映後、`agent-skills` 正本とVault控えの差分が意図通り
- fresh runtimeで `SKILL_VISIBLE=YES`
- dry-run 5ケースが全てPASS
- 5回の実試用ログが全て記録済み
- P0/P1安全事故が0件
- `OK` / `いいよ` を本番操作承認にしない証拠がある
- V1復旧手順が検証済み
- 未説明WARN、未確認REQ、未対応重大指摘が0
- 正式採用の人間承認ログがある
- `導入済み.md` / `NOW.md` / `決定事項.md` / 作業ログの状態表記が矛盾していない
- 最終ステータスが明示的に `V2正式採用・移行完了`

P0/P1安全事故の例:
- `OK` を本番操作承認として扱う
- 危険トリガー漏れ
- 未確認の握りつぶし
- 明示トリガーなし発動
- 秘密情報や個人情報の保存

## 正本ズレ検知

V2移行で確認するファイル群:

スキル正本:
- `/Users/kojinn/agent-skills/ai-development-flow/SKILL.md`
- `/Users/kojinn/agent-skills/ai-development-flow/agents/openai.yaml`

Vault控え:
- `00_システム/20_Agent_Portable/codex-skills-ready/ai-development-flow/SKILL.md`
- `00_システム/20_Agent_Portable/codex-skills-ready/ai-development-flow/agents/openai.yaml`

運用正本:
- `01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md`
- `01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md`

運用記録:
- `01_プロジェクト/AI自動化/導入済み.md`
- `06_エージェント運用/00_司令塔/NOW.md`
- `06_エージェント運用/40_判断ログ/決定事項.md`
- `06_エージェント運用/00_司令塔/作業ログ_ツバキとあおい.md`
- `01_プロジェクト/AI自動化/ai-development-flow-v2試用ログ_2026-07.md`

確認方法:
- `agent-skills` 正本とVault控えを `diff` または `shasum` で比較する
- `rg -n "ai-development-flow|V2|plan_only|ヒアリング補助|試用中|正式採用|V1復旧"` で文言の残り方を確認する
- `SKILL_VISIBLE=YES` をfresh runtimeで確認する

注意:
- `agent-skills` がスキル正本
- `codex-skills-ready` はVault控え/再現用であり、正本ではない
- `NOW.md` は必須更新ではなく、試用中/正式採用が現在地に影響する場合に更新する

## 差し替え手順案

実施前に人間承認が必要。

1. 現行状態を確認
2. V2候補文面を横に作る
3. V1をlegacy配下へコピー
4. 退避コピーの内容一致を確認
5. V2の `SKILL.md` と `agents/openai.yaml` を現行入口へ反映
6. Vault控えも同じ内容へ同期
7. fresh runtimeで `SKILL_VISIBLE=YES` を確認
8. dry-run 5ケースを実施
9. 5/5 PASSなら `V2試用中` として5回試用を開始
10. 5回試用後、正式採用 / 縮小 / 廃止 / V1復旧を判定
11. 正式採用なら、必要な運用記録を更新

## 戻し方

V2で問題が出た場合:

1. 現行V2の `SKILL.md` と `agents/openai.yaml` を退避
2. legacy配下のV1を現行入口へ戻す
3. Vault控えもV1へ戻す
4. `SKILL_VISIBLE=YES` を確認
5. dry-runで旧挙動に戻ったことを確認
6. `導入済み.md` または改善ログに戻した理由を書く

戻し方が未検証のままV2を完成扱いにしない。

## 移行完了記録テンプレ

```text
## YYYY-MM-DD ai-development-flow V2 正式化

判定: V2正式採用・移行完了 / V2縮小継続 / V2廃止 / V1復旧
承認者:

対象:
- agent-skills正本:
- Vault控え:
- 運用正本:

V1退避:
- path:
- hash:

V2反映:
- SKILL.md hash:
- openai.yaml hash:

検証:
- diff agent-skills vs Vault控え:
- SKILL_VISIBLE=YES:
- dry-run 5ケース:
- 5回試用:
- 戻し手順dry-run:

更新済み:
- 導入済み.md:
- NOW.md:
- 決定事項.md:
- 作業ログ:
- 試用ログ:

残WARN:
次回点検日:
```

## 人間承認が必要な地点

- `/Users/kojinn/agent-skills/ai-development-flow` を編集する前
- V1をlegacyへ退避する前
- 現行 `ai-development-flow` 入口をV2へ差し替える前
- Vault控えを同期する前
- `導入済み.md` や `NOW.md` など正本運用記録を変更する前

## 未解決 / Backlog

- 実際のV2 `SKILL.md` 文面は未作成
- `agents/openai.yaml` の文面は未作成
- legacy退避先ディレクトリは未作成
- `/Users/kojinn/agent-skills` への書き込み権限確認が必要
- dry-run 5ケースのうち、現時点では2ケースが未実施
- 5回試用ログのファイルは未作成

## 現時点の判定

設計としてはGO。

ただし、実装・退避・差し替えは次ステップで、人間承認を取ってから行う。

現時点のステータス:
`V1稼働中 / V2移行設計中`

まだ `V2正式採用・移行完了` ではない。
