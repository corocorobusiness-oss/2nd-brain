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

## V2の基本方針

入口名は維持する。

```text
ai-development-flow = 最新安定版
ai-development-flow_v1_legacy = 旧版控え
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

## 差し替え手順案

実施前に人間承認が必要。

1. 現行状態を確認
2. V1をlegacy配下へコピー
3. 退避コピーの内容一致を確認
4. V2の `SKILL.md` と `agents/openai.yaml` を現行入口へ反映
5. Vault控えも同じ内容へ同期
6. dry-run 5ケースを実施
7. `SKILL_VISIBLE=YES` を確認
8. 5回試用ルールを開始
9. `01_プロジェクト/AI自動化/導入済み.md` に状態を追記
10. 必要なら `NOW.md` に「V2試用中」を追記

## 戻し方

V2で問題が出た場合:

1. 現行V2の `SKILL.md` と `agents/openai.yaml` を退避
2. legacy配下のV1を現行入口へ戻す
3. Vault控えもV1へ戻す
4. `SKILL_VISIBLE=YES` を確認
5. dry-runで旧挙動に戻ったことを確認
6. `導入済み.md` または改善ログに戻した理由を書く

戻し方が未検証のままV2を完成扱いにしない。

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
- 5回試用ログの記録フォーマットは未確定

## 現時点の判定

設計としてはGO。

ただし、実装・退避・差し替えは次ステップで、人間承認を取ってから行う。
