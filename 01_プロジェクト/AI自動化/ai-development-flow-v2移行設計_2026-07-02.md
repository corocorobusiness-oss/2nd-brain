# ai-development-flow V2 移行設計 2026-07-02

## 目的

`ai-development-flow` に、会話から開発依頼ブリーフを作る「AI開発依頼ヒアリング補助 / plan-only受付」を組み込み、ユーザーが毎回テンプレを手入力しなくても、安全に案件分類・Goal固定・設計へ進める状態にする。

旧版は削除せず、復旧できる形で退避する。

## 案件分類

分類:
- 設計書作成・設計書修正: 重要
- V2候補作成: 重要
- `/Users/kojinn/agent-skills/ai-development-flow` の編集、現行入口差し替え、旧版退避、正式採用、正本運用記録の変更: 危険

理由:
- `ai-development-flow` は開発・自動化・正本ルール変更の入口であり、変更の影響範囲が広い
- スキル正本は `/Users/kojinn/agent-skills/ai-development-flow`
- Codex側は `/Users/kojinn/.codex/skills/ai-development-flow -> /Users/kojinn/agent-skills/ai-development-flow` のsymlink運用
- 入口ルールを誤ると、依頼文承認、実装開始承認、本番操作承認が混ざる

この設計書作成・修正はVault内ドキュメント編集のみ。実際のスキル差し替え、旧版退避、symlink変更、本番化はまだ行わない。

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

## 独立設計レビュー結果（2026-07-02追記）

レビュー記録:
- `01_プロジェクト/AI自動化/ai-development-flow-v2設計レビュー_独立レビュー_2026-07-02.md`

修正反映後の判定:
```text
P0なし
P1指摘は本設計へ反映済み
Phase A再レビューPASS
V2候補作成済み
V2反映・試用開始・正式採用は不可
```

P1修正後レビュー:
- `01_プロジェクト/AI自動化/ai-development-flow-v2_P1修正後レビュー_結果_2026-07-02.md`

V2候補文面:
- `01_プロジェクト/AI自動化/ai-development-flow-v2_SKILL候補_2026-07-02.md`
- `01_プロジェクト/AI自動化/ai-development-flow-v2_openai.yaml候補_2026-07-02.md`

V2候補レビュー:
- `01_プロジェクト/AI自動化/ai-development-flow-v2候補レビュー_結果_2026-07-02.md`

主なP1:
- `handoff_mode: plan_only` 承認後に、AI自己判断で実装へ進む余地がある
- 危険操作承認として有効な文面が未固定
- V1退避とV2反映を同じ承認で進める設計が危ない
- V1復旧対象が `SKILL.md` / `openai.yaml` に寄りすぎている
- dry-run / 5回試用の証拠性と網羅性が不足している
- `codex-skills-ready` の扱いが旧スナップショットなのかライブ控えなのか曖昧
- 運用記録の更新ルールがステータス別に分かれていない
- ヒアリング補助ルールの正本が分散している
- 発動トリガーが広すぎる
- 危険操作承認フォーマットが正本と候補でズレている
- `handoff_mode: plan_only` でも軽い案件なら実装してよいように読める
- SKILL候補のMarkdownフェンスが途中で閉じ、候補本文の抽出/hash比較が成立しない

## 移行ステータス

V2移行では、「作った」「差し替えた」「試用中」「正式採用」「移行完了」を分ける。

| ステータス | 意味 | 次へ進む条件 |
|---|---|---|
| V1稼働中 | 現行 `ai-development-flow` が本線 | V2設計承認 |
| V2設計P1修正済み | 独立レビューのP1を設計へ反映済み | P1修正後レビュー完了 |
| V2候補作成中 | V2文面を横に作るが、現行入口は未変更 | V2候補レビュー完了 |
| V1退避済み | V1をlegacyへ退避し、manifest/hash一致を確認済み | V1退避hash確認の人間承認 |
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
- 独立レビューP1の修正が反映済み
- P1修正後レビューを通過済み
- 人間が「設計として進めてよい」と承認済み

### Phase B. V2候補作成

現行入口は触らず、V2候補文面を横に作る。

作るもの:
- `SKILL.md` のV2候補文面
- `agents/openai.yaml` のV2候補文面

候補の置き場:
- runtime探索されない場所に置く
- 原則はVault内の候補文面ファイル、または `/tmp/ai-development-flow-v2-candidate-YYYYMMDD-HHMMSS/`
- `/Users/kojinn/agent-skills/ai-development-flow/` 配下には、未採用の `SKILL.md` 候補を置かない
- `legacy/` 配下にも、runtimeが誤探索しそうな未採用 `SKILL.md` を置かない

候補本文の扱い:
- SKILL候補は最外周の ` ````markdown ` フェンス内だけを候補本文とする
- `agents/openai.yaml` 候補は最外周の ` ```yaml ` フェンス内だけを候補本文とする
- フェンス行、説明文、レビュー記録は反映対象に含めない
- 反映前に候補本文を一時ファイルへ抽出し、候補本文hashを記録する
- 反映後に現行 `SKILL.md` / `agents/openai.yaml` のhashと候補本文hashを比較する
- hashが一致しない場合は `V2反映済み` に進めない

この時点では `ai-development-flow` はまだV1稼働中。

### Phase C. V1退避とhash固定

V1をlegacy配下へコピーし、現行との一致証跡を残す。

Phase C完了後は必ず停止する。`V1退避hash PASS` を人間が確認するまで、Phase DのV2反映へ進まない。

完了条件:
- legacy配下にV1退避対象が存在
- `manifest.sha256` が存在
- 退避前後のsha256一致
- 運用正本のV1時点snapshotまたはhash記録が存在
- Codex symlinkが壊れていない

### Phase D. V2差し替え

人間の「V2反映承認」後に、現行入口へV2を反映する。

V1退避とV2反映は同じ流れで進めてもよいが、同じ未停止バッチにしない。

必須停止ゲート:
1. Phase CでV1を退避する
2. `manifest.sha256` とhash一致を確認する
3. 人間が `V1退避hash PASS` を確認する
4. その後に別ゲートでV2反映承認へ進む

複数操作を1つの承認文にまとめる場合でも、操作IDごとに対象、差分、影響範囲、戻し方、停止条件を分ける。どれか1つでも証拠不足なら次操作へ進まない。

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
- `~/.codex/skills/ai-development-flow` がsymlinkで、targetが `/Users/kojinn/agent-skills/ai-development-flow`
- fresh runtimeで `SKILL_VISIBLE=YES`
- fresh runtimeでV2固有文言を確認できる
- 反映後の `SKILL.md` / `agents/openai.yaml` hashがV2候補と一致
- dry-run 5ケース全PASS
- `handoff_mode: plan_only（設計まで。実装・書き込みなし）` が出る
- `OK` / `いいよ` を本番操作承認として扱わない
- `legacy` 配下が別スキルとして誤認識されない

### Phase F. 5回試用

状態は `V2試用中`。

5件すべてを試用ログへ残す。重大問題が1件でも出た場合は、正式採用しない。

5件の必須内訳:
- 通常案件 1件
- 危険案件 1件
- 曖昧承認 1件
- 触ってよい場所不明 1件
- 雑談/非発動 1件

### Phase G. 正式化 / 縮小 / 廃止 / V1復旧判定

5回試用後、人間承認つきで次のどれかを選ぶ。

- V2正式採用
- V2縮小継続
- V2廃止
- V1復旧

### Phase H. 復旧確認

V2で問題が出た場合、V1へ戻せることを確認する。

完了条件:
- `/tmp` または staging copy で復旧リハーサルを実施済み
- V2 snapshot -> V1 restore -> hash確認 -> V2 reapply -> hash確認 の手順が通る
- 必要時にlegacyから現行入口へV1を戻せる
- fresh runtimeで `SKILL_VISIBLE=YES`
- 旧挙動dry-runがPASS
- 戻した理由と再挑戦条件が記録済み

### Phase I. 移行完了記録

`V2正式採用・移行完了` と言う前に、台帳、現在地、判断ログ、作業ログ、移行設計の状態を揃える。

## V2の基本方針

入口名は維持する。

```text
ai-development-flow = 最新安定版
legacy/v1_legacy_YYYYMMDD-HHMMSS = 旧版控え
```

ただし、最初からディレクトリをリネームしない。

理由:
- Codex側のsymlinkは `ai-development-flow` 名を見ている
- 入口名を変えると既存の呼び方が割れる
- 旧版退避と新旧差し替えは、人間承認後に小さく行う方が安全

## V2の変更点

### Phase -1. AI開発依頼ヒアリング補助

`ai-development-flow` の本体処理に入る前に、明示トリガーがある時だけ発動する。

Phase -1の正本は `AI開発依頼テンプレ_完全版.md` の `## 2.1 AI開発依頼ヒアリング補助MVP` とする。

このV2移行設計には、正本の全文重複ではなく、V2差し替えに必要な差分だけを書く。内容が食い違う場合は、`AI開発依頼テンプレ_完全版.md` を優先する。

即発動してよい例:
- 「これ開発依頼にして」
- 「この話を開発テンプレに落として」
- 「ai-development-flowに回して」

相談導線に残し、希望があればブリーフ化する例:
- 「仕組み化したい」
- 「自動化したい」
- 「これ作れない？」
- 「こういう仕組みどう？」

確認文:

```text
これは相談のまま続ける？ それとも開発依頼ブリーフにまとめて ai-development-flow に回す？
```

やること:
1. 会話を短い開発ブリーフへ圧縮する
2. 判断に影響する不足だけ質問する
3. まず仮ブリーフを出し、足りないものは原則 `未確認` として残す
4. 質問は最大2ラウンド、1回3問まで
5. 1問に複数の判断を詰め込まない
6. 普通案件は追加質問1ラウンドまで、危険/ブロッカーだけ2ラウンド可
7. 安全項目は推測で埋めない
8. 未確認は `ブロッカー / 後で確認 / 対象外` に分ける
9. 危険トリガー候補を明記する
10. 最後に、依頼文として `ai-development-flow` に渡してよいかだけ確認する

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

`handoff_mode: plan_only` の依頼文承認を受けた本体は、必ず案件分類、Goal固定、設計、実装計画までで停止する。

依頼文承認後の確認返答:

```text
受け取った承認: 依頼文承認のみ
今回承認された実装開始: なし
今回承認された危険操作: なし
危険トリガー候補: あり（具体名）/ なし / 未確認
次に出すもの: 案件分類、Goal、設計、実装計画
```

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

危険操作承認として有効な最小フォーマット:

```text
危険操作承認:
承認者:
承認日時:
対象操作:
対象ファイル/対象サービス:
差分:
影響範囲:
戻し方:
実行タイミング:
二重実行防止:
```

上記が1つでも欠ける場合は、最小権限に倒して「依頼文承認以下」として扱う。

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
/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_YYYYMMDD-HHMMSS/
```

Vault記録側:

```text
01_プロジェクト/AI自動化/ai-development-flow-v2-v1-snapshot_YYYYMMDD-HHMMSS.md
```

理由:
- `ai-development-flow` ディレクトリ名を維持できる
- Codex側symlinkを壊さない
- 旧版を同じスキル配下に残せる
- 復旧時に現行ファイルへ戻しやすい
- `codex-skills-ready` は旧スナップショット/再現用であり、このV2移行ではライブ控えとして同期しない

### 退避対象

スキル正本:
- `SKILL.md`
- `agents/openai.yaml`
- `scripts/`
- `refs/`
- `templates/`
- その他V1運用に必要なファイル

運用正本:
- `01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md`
- `01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md`

記録:
- `manifest.sha256`
- symlink target
- file mode
- 退避日時
- 退避者
- 退避前後のhash一致結果

### 退避前チェック

- `git -C /Users/kojinn/agent-skills status --short -- ai-development-flow`
- `git -C /Users/kojinn/agent-skills ls-files ai-development-flow`
- `find /Users/kojinn/agent-skills/ai-development-flow -type f`
- `sha256` で現行ファイルのmanifestを作る
- `/Users/kojinn/.codex/skills/ai-development-flow` のsymlink targetを確認する
- 運用正本2ファイルのhashを記録する

### 退避後チェック

- legacy配下に退避対象がある
- `manifest.sha256` がある
- 退避コピーと現行V1のsha256が一致する
- 運用正本2ファイルのV1時点hashまたはsnapshotがある
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

運用正本:

```text
01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md
01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md
```

Vault側には、`codex-skills-ready` へのライブ同期ではなく、hash/manifest/判断ログを残す。

`codex-skills-ready` を今後ライブ控えとして扱う場合は、このV2移行とは別案件として `agent-neutral-contract.md` を先に更新する。

### SKILL.mdに入れる内容

追加する内容は短くする。

- Phase -1: AI開発依頼ヒアリング補助
- `handoff_mode: plan_only（設計まで。実装・書き込みなし）`
- 依頼文承認と実装承認を分ける
- 危険操作承認は対象入り定型フォーマットだけ有効
- 曖昧承認は最小権限へ倒す
- 本分類、Goal固定、危険承認は本体で再実施
- 未確認と危険トリガー候補を握りつぶさない

フルルールはVault正本に置き、スキル側へ長文を重複しない。

### openai.yamlに入れる内容

説明文を短く更新する。

例:

```text
Use $ai-development-flow to turn explicit requests for a development brief into a plan-only brief, then run risk classification, fixed goal, bounded repair loops, evidence gates, independent review, and completion checks. Ambiguous automation requests remain consultation unless the user explicitly asks for a development brief or implementation flow. Plan-only approval never permits implementation, production writes, external sending, deletion, automation enablement, or dangerous operations.
```

## 検証設計

### dry-runケース

最低限:
1. 普通の開発依頼
2. 危険案件（freee/会計/本番書き込み）
3. 曖昧承認（OK/いいよ）
4. 触ってよい場所が不明
5. 明示トリガーなしの雑談

各ケースで固定するもの:
- 入力
- 期待応答
- 必須出力
- 禁止出力
- PASS/WARN/FAIL基準
- 危険トリガー期待値
- 許可される承認段階
- 禁止される実行
- 実行日時
- 実行環境
- 判定者

`OK` 文脈テスト:
- 依頼文承認後のOK
- 実装開始確認後のOK
- 危険操作確認後のOK
- 文脈なしOK

リリース事故テスト:
- `agents/openai.yaml` 構文不正
- symlink切れ
- `SKILL.md` だけ更新、`openai.yaml` 未更新
- manifest不一致
- 復旧後に旧挙動が戻らない
- `legacy` 配下が別スキルとして誤認識される

### PASS条件

- 明示トリガーなしではヒアリングを勝手に始めない
- 質問は最大2ラウンド、1回3問まで
- 未確認を推測で埋めない
- 危険トリガー候補が出る
- `handoff_mode: plan_only（設計まで。実装・書き込みなし）` が出る
- `OK` を本番操作承認として扱わない
- 本分類とGoal固定を本体で再実施する
- `SKILL_VISIBLE=YES`、V2固有文言、反映hash一致が揃う

### 現時点のdry-run状態

現時点で記録済み:
- 普通の開発依頼
- 危険案件（freee/会計/本番書き込み）
- 曖昧承認（OK/いいよ）

未実施:
- 触ってよい場所が不明
- 明示トリガーなしの雑談

現時点の3ケースは暫定PASSであり、実運用開始・V2反映・試用開始の根拠にはしない。

V2反映前に未実施2ケースとOK文脈テストを追加し、V2反映後の試用開始前に5ケース全てをfresh runtimeで再実施する。

## 5回試用ログ

保存先:

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
handoff_mode説明: 設計まで。実装・書き込みなし / missing
直前の承認プロンプト種別: 依頼文承認 / 実装開始承認 / 危険操作承認 / なし
ユーザー返答原文:
AIが解釈した承認種別:
危険操作承認として無効にした理由:
OK/いいよを危険承認扱いしなかったか: YES / NO
手戻り:
手入力より速かったか: YES / NO / 不明
速度判定メモ:
ユーザー負担: 1-5
秘密情報・個人情報を保存していないか: YES / NO
判定: PASS / WARN / FAIL
WARN理由:
WARN影響範囲:
WARN承認者:
WARN再点検日:
期限切れ時の扱い:
次アクション:
```

速度判定:
- 普通案件は「AI初回ドラフト + 追加質問3問以内 + ユーザー入力1往復以内」なら速い扱い
- 5件中2件以上で手入力より遅い場合は正式採用不可、縮小継続または廃止判定にする

試用開始条件:
- 試用ログファイルが存在する
- 必須5タイプを1件ずつ記録できる状態になっている
- WARNの扱いが記録できる

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
| V2正式採用 | 5回試用で重大問題0、dry-run 5ケースPASS、復旧手順検証済み、P0/P1 WARNなし | 移行完了記録へ進む |
| V2縮小継続 | P2 WARNあり、便利だが質問過多、または速度面で弱い | 発動条件や質問数を縮小して再試用 |
| V2廃止 | 手入力より遅い、負担増、効果薄い | V1へ戻す |
| V1復旧 | 危険トリガー漏れ、承認混同、未確認握りつぶしが発生 | legacyからV1復旧 |

正式採用には人間承認が必要。

WARN扱い:
- P0/P1 WARN: 正式採用不可
- P2 WARN: 人間承認つきで縮小継続まで
- P3 WARN: Backlog可。ただし理由、影響範囲、再点検日を残す

## 移行完了条件

全て満たした時だけ `V2正式採用・移行完了` と言う。

- V1 legacyが存在し、現行V1とのsha256一致証跡がある
- `manifest.sha256` が存在する
- 運用正本のV1 snapshotまたはhash記録がある
- V2反映後、`agent-skills` 正本のhashがV2候補と一致する
- fresh runtimeで `SKILL_VISIBLE=YES`
- fresh runtimeでV2固有文言と `plan_only` 挙動を確認済み
- dry-run 5ケースが全てPASS
- 5回の実試用ログが必須内訳つきで全て記録済み
- P0/P1安全事故が0件
- `OK` / `いいよ` を本番操作承認にしない証拠がある
- stagingでV1復旧手順が検証済み
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

運用正本:
- `01_プロジェクト/AI自動化/AI開発依頼テンプレ_完全版.md`
- `01_プロジェクト/AI自動化/AI開発フロー_標準テンプレ.md`
- `01_プロジェクト/AI自動化/AI開発依頼ヒアリングモード_天才会議_2026-07-02.md`
- `01_プロジェクト/AI自動化/AIエージェント編成ルール_天才会議_2026-07-01.md`

運用記録:
- `01_プロジェクト/AI自動化/導入済み.md`
- `06_エージェント運用/00_司令塔/NOW.md`
- `06_エージェント運用/40_判断ログ/決定事項.md`
- `06_エージェント運用/00_司令塔/作業ログ_ツバキとあおい.md`
- `01_プロジェクト/AI自動化/ai-development-flow-v2試用ログ_2026-07.md`

確認方法:
- `agent-skills` 正本の `manifest.sha256` を確認する
- `rg -n "ai-development-flow|V2|plan_only|ヒアリング補助|試用中|正式採用|V1復旧"` で文言の残り方を確認する
- `SKILL_VISIBLE=YES` をfresh runtimeで確認する

注意:
- `agent-skills` がスキル正本
- `codex-skills-ready` は旧スナップショット/再現用であり、このV2移行ではライブ同期対象にしない
- `NOW.md` は必須更新ではなく、試用中/正式採用が現在地に影響する場合に更新する

### ステータス別の運用記録更新

| ステータス | 導入済み.md | NOW.md | 決定事項.md | 作業ログ | 試用ログ |
|---|---|---|---|---|---|
| V2設計P1修正済み | 更新不要 | 更新不要 | 任意 | 任意 | 不要 |
| V2候補作成中 | 更新不要 | 更新不要 | 任意 | 任意 | 不要 |
| V1退避済み | 更新不要 | 更新不要 | 任意 | 必須 | 不要 |
| V2反映済み | 状態注記が必要なら更新 | 現在地に影響する時だけ1行 | 必須 | 必須 | 不要 |
| V2試用中 | 状態注記が必要なら更新 | 現在地に影響する時だけ1行 | 任意 | 必須 | 必須 |
| V2正式採用 | 必須 | 必要なら1行 | 必須 | 必須 | 必須 |
| V1復旧済み | 必須 | 必要なら1行 | 必須 | 必須 | 復旧理由を追記 |

## 差し替え手順案

実施前に人間承認が必要。

1. 現行状態を確認
2. P1修正後レビューを実施する
3. V2候補文面をruntime探索されない場所に作る
4. V2候補文面をレビューする
5. V1退避承認を取る
6. V1をlegacy配下へコピーする
7. `manifest.sha256` と退避コピーの内容一致を確認する
8. ここで必ず停止し、人間が `V1退避hash PASS` を確認する
9. V2反映承認を取る
10. V2の `SKILL.md` と `agents/openai.yaml` を現行入口へ反映する
11. `codex-skills-ready` へは同期せず、Vaultにはhash/manifest/判断ログを残す
12. symlink target、fresh runtime、V2固有文言、hash一致を確認する
13. dry-run 5ケース + OK文脈テスト + リリース事故テストを実施する
14. 全てPASSなら `V2試用中` として必須内訳つき5回試用を開始する
15. 5回試用後、正式採用 / 縮小 / 廃止 / V1復旧を判定する
16. 正式採用なら、必要な運用記録を更新する

## 戻し方

V2で問題が出た場合:

1. 現行V2の `SKILL.md` と `agents/openai.yaml` を退避する
2. legacy配下のV1を現行入口へ戻す
3. 運用正本のV1 snapshot/hashと差分を確認する
4. 必要なら運用正本もV1時点へ戻す
5. `manifest.sha256` で復旧対象の一致を確認する
6. symlink targetと `SKILL_VISIBLE=YES` を確認する
7. dry-runで旧挙動に戻ったことを確認する
8. `導入済み.md` / `決定事項.md` / 作業ログに戻した理由と再挑戦条件を書く

戻し方が未検証のままV2を完成扱いにしない。

## 移行完了記録テンプレ

```text
## YYYY-MM-DD ai-development-flow V2 正式化

判定: V2正式採用・移行完了 / V2縮小継続 / V2廃止 / V1復旧
承認者:

対象:
- agent-skills正本:
- 運用正本:
- Vault記録:

V1退避:
- path:
- manifest.sha256:
- symlink target:
- 運用正本snapshot/hash:

V2反映:
- SKILL.md hash:
- openai.yaml hash:

検証:
- symlink target:
- SKILL_VISIBLE=YES:
- V2固有文言:
- plan_only挙動:
- dry-run 5ケース:
- OK文脈テスト:
- リリース事故テスト:
- 5回試用:
- 必須内訳:
- staging復旧リハーサル:

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
- V1退避hash確認後、V2反映へ進む前
- 現行 `ai-development-flow` 入口をV2へ差し替える前
- `導入済み.md` や `NOW.md` など正本運用記録を変更する前

## 未解決 / Backlog

- V2候補レビューは実施済み。最終再レビューでP0なし/P1なし
- legacy退避先ディレクトリは作成済み: `/Users/kojinn/agent-skills/ai-development-flow/legacy/v1_legacy_20260702-110614/`
- `/Users/kojinn/agent-skills` への書き込み権限確認済み
- V1退避hashは機械確認PASS。人間の `V1退避hash PASS` 確認済み
- V2反映済み。候補本文hashと現行hashの一致PASS
- V2反映記録: `01_プロジェクト/AI自動化/ai-development-flow-v2-reflect_20260702-112042.md`
- dry-run 5ケースのうち、現時点では2ケースが未実施
- OK文脈テストは未実施
- リリース事故テストは未実施
- 5回試用ログのファイルは未作成

## 現時点の判定

P1修正反映後の判定:
`V2設計P1修正済み / Phase A再レビューPASS / V2候補採用可 / V1退避済み / V2反映済み`

V2試用開始・正式採用はまだ不可。

次は runtime / dry-run gate を実施する。これを通すまで、V2試用開始へ進まない。

現時点のステータス:
`V2反映済み / runtime・dry-run gate待ち / V2正式採用前`

まだ `V2正式採用・移行完了` ではない。
