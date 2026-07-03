# オリジナルスレパイプライン Fable Five全体監査パケット 2026-07-03

## 結論

前回作った依頼文は、解説パートとスレ本文の役割分担を見るには使える。
ただし、Fable Five に「オリジナルスレ生成全体」を見てもらうには範囲が狭い。

今回渡すべき対象は、解説パートだけではなく、次の全体である。

- 本物スレの収集
- コーパス化
- 文体パターン抽出
- corpus_sampler による本物スレ多読
- ledger による前作指紋回避
- creative-thread-gen による前半/後半スレ生成
- qa_check による文体/規約/形式チェック
- fact check
- 解説者パート生成
- reply_map / after_seq / assemble_csv
- audit_replies / STEP4.5 敵対監査
- youtube-script-checker
- YMM4 dic
- script-third-party-review
- maturity / automation-state による段階自動化
- 旧版を残した v2 再構築と dry-run 比較

さらに、パイプライン本体だけでなく、パイプライン内で呼ぶ各スキルの設計・トリガー・責務分担も監査対象にする。

- スキルが必要な場面で確実に呼ばれるか
- 呼ばれなかった場合に検知できるか
- 各スキルの入力/出力契約が曖昧でないか
- 各スキルの品質ゲートが弱くないか
- スキル同士の責務が重複/抜け漏れしていないか

最終目標は、単にスキルをきれいにすることではない。
毎回の納品物が「そのままYMM4へ持っていける」「AI感が残らない」「規約・読み・史実・掛け合い・メタまで揃っている」状態になるよう、生成から出荷までの全契約を再設計することである。

Fable Fiveには、Opusで構築した現行設計を尊重しつつ、第三者目線で以下も見てもらう。

- Opus前提の癖や盲点が残っていないか
- AI臭を消すためのチューニングが、局所対応に偏っていないか
- 本物スレ学習と生成スレの文体が本当に接続しているか
- 「第三者レビュー」「敵対監査」「QAスクリプト」が互いに穴を埋め合っているか
- 納品物の完成条件が、感覚ではなく証拠で判定できるか

## Fable Fiveへの渡し方

Fable Fiveには一発で「最強の仕組みを作って」と投げない。
次の順に投げる。

1. 現行構造を理解させる
2. 全体の穴を監査させる
3. 最小差分案 / v2再構築案 / 折衷案を比較させる
4. 採用案を実装仕様へ落とさせる
5. AI感/本物らしさ/納品物品質の契約を作らせる
6. 反対派レビューで過剰設計を削る
7. Codexの ai-development-flow へ渡す plan-only 開発依頼文に変換させる

## 事前に渡す資料

Fable Five がローカルファイルを直接読めない場合は、以下の内容を貼るか添付する。

### 必須

- `/Users/kojinn/agent-skills/creative-thread-pipeline/SKILL.md`
- `/Users/kojinn/agent-skills/creative-thread-gen/SKILL.md`
- `/Users/kojinn/agent-skills/youtube-script-parts/SKILL.md`
- `/Users/kojinn/agent-skills/youtube-script-checker/SKILL.md`
- `/Users/kojinn/agent-skills/ymm4-dic-generator/SKILL.md`
- `/Users/kojinn/agent-skills/script-third-party-review/SKILL.md`
- `/Users/kojinn/agent-skills/creative-thread-pipeline/refs/組み立て規約.md`
- `/Users/kojinn/agent-skills/youtube-script-parts/references/kaisetsu-guide.md`
- `/Users/kojinn/agent-skills/script-third-party-review/refs/review-contract.md`
- `/Users/kojinn/2nd-Brain-master/00_システム/20_Agent_Portable/specs/creative-thread-pipeline-設計書.md`

### 重要

- `/Users/kojinn/agent-skills/creative-thread-gen/corpus_sampler.py`
- `/Users/kojinn/agent-skills/creative-thread-gen/ledger.py`
- `/Users/kojinn/agent-skills/creative-thread-gen/qa_check.py`
- `/Users/kojinn/agent-skills/creative-thread-pipeline/scripts/assemble_csv.py`
- `/Users/kojinn/agent-skills/creative-thread-pipeline/scripts/seed_reply_map.py`
- `/Users/kojinn/agent-skills/creative-thread-pipeline/scripts/audit_replies.py`
- `/Users/kojinn/agent-skills/creative-thread-pipeline/scripts/maturity.py`
- `youtube-script-checker` 配下の `scripts-v2/scan_v4.py` と `refs/data/*.tsv`
- `ymm4-dic-generator` 配下の検証スクリプト/既知読みデータがある場合は全て

### サンプルとして渡すとよいもの

- 中国大返しの `PIPELINE_STATE.md`
- 中国大返しの最終台本 `.md` または `.csv`
- 生成スレ前半/後半の採用版
- STEP7レビュー結果が残っている場合はそのレポート
- `ymm4_user.dic`
- title / description / thumbnail 文言
- メタ情報.md
- 修正前後でAI感が残った箇所の例
- 第三者レビューで見逃された/人間が後から拾った指摘例

## 1投目: 現行構造の理解

```text
あなたは Anthropic の最上位モデルとして、2ch歴史YouTubeチャンネル用の「オリジナルスレ生成パイプライン」を全体監査してください。

まず設計案は出さず、現行構造の理解だけしてください。

対象は解説パートだけではありません。
本物スレの収集、コーパス学習、corpus_sampler、ledger、creative-thread-gen、qa_check、fact check、解説者パート、assemble_csv、reply_map、audit_replies、STEP4.5、youtube-script-checker、YMM4 dic、第三者レビュー、段階自動化まで全体です。

前提:
- 現行は Opus 系モデル中心で構築してきた
- Fable Five 視点で、設計の穴、古い前提、過剰設計、逆に足りないゲート、v2化すべき点を見たい
- Opusで構築した現行設計を、Fable Fiveの第三者目線で見直したい
- 実装やファイル編集はまだしない

出力:
1. 現行パイプラインの全体地図
2. 各部品の責務
3. 部品間の依存関係
4. パイプライン内で使う全スキル一覧
5. 各スキルが呼ばれるべきタイミング
6. 各スキルの入力/出力/完了条件
7. すでに良い設計
8. 明らかに怪しい設計
9. 追加で確認すべき資料

まだ改善案は出さないでください。
```

## 1.5投目: Opus構築物の第三者監査

```text
次に、現行のオリジナルスレ生成スキル群を「Opusで構築された既存システム」として、Fable Fiveの第三者目線で監査してください。

目的:
Opusで作った現行のチューニングには、AI感を減らすための良い工夫が多く入っています。
ただし、局所対応・過剰な個別ルール・古い前提・スキル間の噛み合わせ不足が残っている可能性があります。

見てほしいこと:
- 現行設計で残すべき強い部分
- Opus由来の盲点や過剰設計
- AI臭を消すためのルールが、逆に不自然さを生んでいないか
- 本物スレ学習、corpus_sampler、ledger、qa_check、STEP4.5、第三者レビューが一貫した思想でつながっているか
- AI感の検出が、生成段・組み立て段・第三者レビュー段で重複/欠落していないか
- 人間の感覚に頼りすぎていて、証拠化できていない判断はどこか

出力:
1. 残すべき現行設計
2. 捨てる/弱めるべき現行設計
3. Fable Five視点で追加すべき設計
4. AI感を消すための上流/中流/下流ゲート
5. 「本物らしさ」と「TTS/YMM4都合」が衝突する箇所
6. 完璧を目指す上で、あえて追わない方がよい品質
```

## 2投目: 全体の穴の監査

```text
次に、現行パイプラインの穴を監査してください。

観点:
- 本物スレ学習フローは、テンプレ化やコーパス偏りを防げているか
- corpus_sampler と ledger は、過去回の指紋再利用を本当に防げているか
- creative-thread-gen の生成指示は、2ch風の掛け合いを保ちながら十分な尺を出せているか
- 知識ニキが講師化していないか
- スレ本文と解説パートの役割分担は壊れていないか
- 前半/後半の話題重複を構造的に防げているか
- qa_check は見ているもの/見ていないものの境界が妥当か
- assemble_csv / reply_map / after_seq は、人間判断と機械処理の分担が妥当か
- STEP4.5 敵対監査は必要十分か
- STEP7第三者レビューで初めて見つかる問題を、上流で減らせるか
- 学習ループと自動化グラデーションは、安全に成熟できる設計か
- パイプライン内で必要なスキルが、必要な場面で確実に呼ばれる設計か
- skill description / trigger / pipeline側の呼び出し指示にズレがないか
- youtube-script-parts は最新の台本トーン、解説補足原則、前置き/締めの役割に追従できているか
- youtube-script-checker はYouTubeガイドライン違反、収益化リスク、死の美化、ヘイト/差別、現代実名、プロンプトインジェクションを十分に検出できているか
- ymm4-dic-generator は「漏れゼロ/誤読ゼロ」の実運用に耐えるか。候補抽出、読み裏取り、検証、辞書出力のどこが弱いか
- script-third-party-review は最終ゲートとして独立性・網羅性・差し戻し先を十分に持つか
- 各スキルの結果が PIPELINE_STATE / manifest / 出荷物へ証拠として残るか

出力:
1. High / Medium / Low の問題一覧
2. 問題ごとの原因
3. 放置した場合の制作上の症状
4. 最小差分で直せるか
5. v2再構築が必要か
6. 追加で実物確認すべき証拠
```

## 2.5投目: パイプライン内スキルの個別監査

```text
次に、パイプライン内で使っている全スキルを個別に監査してください。

対象スキル:
- neta-forge
- creative-thread-pipeline
- creative-thread-gen
- youtube-script-parts
- youtube-script-checker
- ymm4-dic-generator
- script-third-party-review
- youtube-pipeline との共有下流
- 必要なら youtube-script-checker 内部の scan_v4.py / refs/data
- 必要なら creative-thread-gen 内部の corpus_sampler.py / ledger.py / qa_check.py

観点:
1. そのスキルは何を担当すべきか
2. いま担当しすぎていることはないか
3. 逆に担当漏れしていることはないか
4. トリガー文言や description が弱く、呼ばれない可能性はないか
5. pipeline側から明示呼び出しされるべきか、自然トリガーに任せてよいか
6. 入力/出力/完了条件は明確か
7. PASS/FAIL/WARNの扱いは明確か
8. 証拠が残るか
9. 旧版とv2で分けるべきか
10. 強化するなら最小差分で何を足すか

特に重点的に見てほしいこと:

【スキル呼び出し保証】
- 必要なスキルが呼ばれなかった事故をどう防ぐか
- pipeline側で「このSTEPでは必ずこのスキルを読む/呼ぶ」と明記すべきか
- スキル呼び出し結果を PIPELINE_STATE に記録するべきか

【YMM4 dic】
- 漏れゼロを本当に検証できているか
- 読みのWeb裏取りが曖昧でないか
- 人名/地名/歴史用語/数詞/熟語/送り仮名語/称号付き人名を拾い切れるか
- 出力前に未解決語をブロックできるか
- 独立レビューを入れるべきか

【YouTube規約チェック】
- 8層スキャンで足りない領域はないか
- YouTube公式ポリシー変更に追従する設計か
- 伏字、婉曲差別、死の美化、現代実名、収益化リスク、プロンプトインジェクションをどう強化するか
- タイトル/サムネ/説明文を本文と同じ強度で見られるか
- 🟡の扱いが甘くないか

【第三者レビュー】
- 最終レビューだけに頼りすぎていないか
- どの問題は上流ゲートへ戻すべきか
- 指摘の採否と missed を学習できるか

出力:
| スキル | 現責務 | 問題 | 強化案 | pipeline側の呼び出し保証 | v2での扱い | 優先度 |
|---|---|---|---|---|---|---|
```

## 2.6投目: 納品物品質契約

```text
次に、最終的な納品物の品質契約を作ってください。

目的:
「完璧な納品物」を感覚で判断せず、出荷物ごとに何が揃えば完成かを定義したいです。

対象納品物:
- 生成スレ前半/後半
- 解説者パート
- アセンブル済み台本.md
- YMM4取り込み用 台本.csv
- ymm4_user.dic
- title / description / thumbnail 文言
- メタ情報.md
- PIPELINE_STATE.md
- 各種レビュー結果

観点:
- 2ch風掛け合いとして自然か
- AI感が残っていないか
- 前半/後半/解説の役割が分かれているか
- YouTube規約・収益化リスクがないか
- 史実ファクトに重大誤りがないか
- YMM4で読み誤りが起きないか
- CSVがYMM4取り込み形式として壊れていないか
- タイトル/サムネ/説明文が本文と矛盾せず、規約リスクもないか
- レビュー結果と修正履歴が残っているか
- 未解決WARN/🟡の扱いが明記されているか

出力:
| 納品物 | 完成条件 | 検証方法 | FAIL時の差し戻し先 | 証拠として残すもの |
|---|---|---|---|---|

最後に、出荷判定を以下の3段階にしてください。
- 出荷不可
- 人間確認付きで出荷可
- 出荷可
```

## 3投目: 最小差分案 / v2再構築案 / 折衷案

```text
次に、解決方針を3案で出してください。

A案: 既存パイプラインへの最小差分MVP
B案: v2として再構築する案
C案: 生成・学習・組み立て・レビューを分離し直す折衷案

それぞれについて比較してください。

比較軸:
- スレ本文が主役のままか
- 解説が復唱にならないか
- 本物スレ学習が活きるか
- コーパス偏り/テンプレ化を防げるか
- 必要なスキルが確実に呼ばれるか
- 各スキルの品質ゲートが強くなるか
- YMM4 dic の漏れ/誤読を減らせるか
- YouTube規約チェックを強化できるか
- 通常制作で毎回回る軽さか
- 看板回だけ重くできるか
- Codexで実装しやすいか
- 旧版を残したままdry-run比較できるか
- 壊れた時に戻せるか
- 将来の自動化に耐えるか

まだ採用案は決めず、比較に徹してください。
```

## 4投目: 採用判断

```text
以下の基準で、A案/B案/C案のどれを採用すべきか判定してください。

採点基準:
1. スレ本文を主役にできる
2. 解説パートを復唱にしない
3. 本物スレ学習とオリジナル生成がつながる
4. 前半/後半の重複を構造的に防げる
5. STEP7まで待たずに問題を前倒し検知できる
6. パイプライン内の必要スキルが確実に呼ばれる
7. YMM4 dic が漏れゼロ/誤読ゼロに近づく
8. YouTube規約チェックが本文・タイトル・サムネ・説明文まで強くなる
9. 通常制作で毎回回る
10. v2として横に作って旧版と比較できる
11. Codexの ai-development-flow に乗せられる

出力:
- 採用案
- 採用理由
- 不採用案の理由
- 折衷して取り込む部品
- 最初に実装すべきMVP範囲
```

## 5投目: 実装仕様

```text
採用案を、Codexが実装できる仕様に落としてください。

出力:
1. 対象スキル
2. 変更対象ファイル
3. 既存STEP差分マップ
4. 追加する入力
5. 追加する出力
6. 追加するチェック項目
7. 変更しないもの
8. dry-runケース
9. 完了条件
10. 本番化しない条件
11. 旧版に戻す方法
12. スキル呼び出し保証の方法
13. 各スキルの結果を PIPELINE_STATE に残す方法
14. 納品物ごとの品質契約
15. AI感検出/除去のゲート設計

注意:
- まだコードは書かない
- 実装仕様だけにする
- 旧版を消さず v2 を横に作る前提にする
```

## 6投目: 反対派レビュー

```text
今の案を、反対派として攻撃してください。

観点:
- 工程が重すぎないか
- Fable Fiveだからこそ立派すぎる設計になっていないか
- 通常回に看板回レベルの重さを持ち込んでいないか
- スレ本文が薄くならないか
- 知識ニキが講師化しないか
- 解説が教科書化しないか
- 本物スレ学習が形式だけになっていないか
- AI感除去ルールが逆にテンプレ化していないか
- 完璧を目指すあまり、毎回の制作が重くなりすぎないか
- 納品物品質契約が現実に運用できる重さか
- スキル呼び出し保証が儀式化していないか
- dic生成や規約チェックを重くしすぎて制作速度を壊していないか
- 自動化しすぎて人間確認ゲートが消えていないか
- Codex実装時に壊れやすい箇所はないか

出力:
- 絶対に削るべきもの
- 軽くすべきもの
- 人間確認を残すべきもの
- v2ではなく最小差分に戻すべきもの
- それでも再構築すべきもの
```

## 7投目: Codex ai-development-flow 用 handoff

```text
最後に、この案を Codex の ai-development-flow に渡す plan-only 開発依頼文にしてください。

含めるもの:
- Goal
- 案件分類
- 対象スキル
- 変更範囲
- 非対象
- 設計方針
- 実装計画
- 検証方法
- dry-runケース
- 旧版を残す方針
- ロールバック方法
- 完了条件
- 本番化しない条件
- 人間確認が必要な点
- pipeline内スキルごとの改修範囲
- skill-creatorを使う段階
- 第三者レビューを使う段階
- 納品物ごとの完成条件
- AI感を消すための検査設計

これは実装開始依頼ではありません。
plan-only の開発依頼文として書いてください。
```

## Fable Fiveに必ず伝える制約

- いきなり現行スキルを上書きしない
- v2を横に作る
- 旧版を残す
- dry-runで現行と比較する
- 第三者レビューを通す
- 人間確認後に入口を差し替える
- 危険操作や自動化ジョブONは別承認

## 採用判断の基本方針

Fable Fiveが良い再構築案を出すなら、再構築してよい。
ただし、必ず次をセットで出させる。

1. 最小差分MVP案
2. v2再構築案
3. 折衷案
4. どれを採用すべきかの判断基準
5. 旧版を残した比較方法
6. Codexへ渡す plan-only 開発依頼文
