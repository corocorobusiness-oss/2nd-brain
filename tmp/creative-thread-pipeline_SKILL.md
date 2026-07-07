---
name: creative-thread-pipeline
description: >-
  2ch歴史チャンネルの「創作スレ（オリジナル2chスレ）→ 解説者パート → YMM4取り込み用CSV」を
  ネタ確定後〜取り込み直前まで一気通貫で作るオーケストレーションスキル。生成は既存スキルを呼び、
  本スキルは「組み立て規約＋検品ゲート＋出荷物の生成」に徹する。転載を避けてオリジナルで台本を作りたいとき。
  「創作スレ台本」「オリジナルスレで台本」「スレ台本一気通貫」「転載なしで台本」「creative pipeline」
  でトリガーする。各STEPで必ずユーザー確認を取る（暴走防止）。
metadata:
  author: ikeda-yuma
  version: 1.0.1
  category: content-creation
---

# 創作スレ台本 一気通貫パイプライン（creative-thread-pipeline）

平将門の祟り回で確立した「創作スレ→YMM4台本」の全工程を、毎回再現できるスキルにしたもの。
youtube-pipeline（実スレscrape版）の**兄弟**＝下流（組み立て→検品→dic→出荷）は同一。
**本スキルは生成を再実装しない。オーケストレーション＋アセンブル＋出荷に徹する。**

正本の組み立て規約＝`refs/組み立て規約.md`。設計の全文＝`00_システム/20_Agent_Portable/specs/creative-thread-pipeline-設計書.md`。

## 立ち位置と原則
- ネタ確定後〜YMM4取り込み直前までの**創作スレ版フルパイプライン**。
- **各STEP後にユーザー確認**（提案→確認）。学習が溜まったSTEPだけ後で自動化を**提案**する（Phase2・勝手に自動化しない）。
- **役割分担**：返信マップ・解説位置・解説対象は **LLM（わたし）が本文を読んで判断→提案→確認**。
  話者ローテ・大/下・>>ラベル・解説挿入・句読点改行・CSV出力は **script が機械適用**（`scripts/assemble_csv.py`）。
  ※返信マップの regex 自動導出は実走で50%破綻＝**LLM判断タスク**（設計§14）。regex化しない。
- **スレ本文は read-only**。番号を振り直さない（欠番の不規則化は creative-thread-gen 側の責務）。

## パイプライン（STEP1→8・各STEP確認ゲート）

### STEP1 ネタ確定
- ⓪**brief.json があれば読む（連動・最優先）**：保存先に `brief.json`（neta-forge 出力・契約v1）があれば、まず `python3 ~/.claude/skills/neta-forge/scripts/validate_brief.py <brief.json>` を通す（FAIL/status=blocked なら着手しない）。PASS なら **theme/era/split(front=タイトルネタ・back=本筋)/thread_core_question/title_candidates/facts/gloss/gen_directives を brief から自動充填**し、STEP1 は「振り分けを確認するだけ」になる（人手の橋渡しゼロ）。契約＝`neta-forge/refs/brief-contract.md`。schema_version をチェックし未対応版なら停止。
  - **`brief.publish`（投稿日）/`brief.market`（市場）/`brief.trend`（検索需要）も拾う**：最終 STEP の メタ情報.md に「📅 推奨投稿日＝`publish.recommended_dows`／`time_jst`（conf付）」「🔥 市場＝`market`（流行タイトル型/ギャップ）」「🔍 検索＝`trend.demand_level`／切り口＝`trend.suggested_angles`」を転記し、ユーザーが公開タイミングまで分かる状態で渡す。タイトル決定時は `market.trending_title_patterns` と `trend.suggested_angles`（視聴者の実検索語＝暗殺/真実/死因 等）を参考にする（断定はしない・史実を曲げない）。
- brief が無いとき＝従来どおり：テーマ（人名/事件）＋前半後半の振り分けを確定。前半＝**タイトルネタ**（祟り・伝説など視聴動機）、後半＝生涯・本筋。ネタ未確定なら `neta-research`（→将来 neta-forge）を前段で（任意）。
- **保存先**＝`Projects/youtube/創作スレ下書き/YYYY-MM-DD_テーマ/`。中間生成物（スレmd・parts・manifest・brief.json）もここに置く。
- **SSDミラー**＝案件フォルダを作成・更新したら `python3 scripts/mirror_to_ssd.py <案件フォルダ>` で `/Volumes/SSD/YouTube/創作スレ下書き/YYYY-MM-DD_テーマ/` に追加コピーする。SSD側は複製であり、正本は引き続き `Projects/youtube`。このコピーは削除同期しない（SSD側だけにあるファイルは消さない）。SSD未接続・権限不足は警告のみで本体生成は止めない。
- **フォルダ監視式の追従**＝手動編集・追加も追従したい時は `python3 scripts/watch_drafts_ssd_mirror.py --daemon --interval 30` を使う。状態ファイルは `Projects/youtube/.ssd_mirror_state.json`（gitignore済み）。この監視も削除同期しない。launchd常駐ONは自動化ジョブ扱いなので、別途人間承認とWatchtower/台帳登録が必要。
- → ユーザーに振り分け方針を確認（brief 由来でも最終確認は残す＝暴走防止）。

### STEP1.5 v2/P3-A 解説先行設計（v2明示時のみ） → `/youtube-script-parts`
- **発動条件**：ユーザーが v2 / P3-A / 解説先行生成を明示し、brief-contract v1.1+ の `gloss_targets[].background_facts[]` が利用できる場合のみ。通常のv1運用ではこのSTEPをスキップし、従来どおりSTEP2→STEP3の順で進める。
- **目的**：スレ本文が解説対象を先に説明し切り、解説パートが言い直しになる事故を防ぐ。解説本文を先に作り、スレ生成側には「解説が扱う見出しリスト」だけを渡して、結論・背景・出典を言い切らせない。
- **入力**：`brief.facts` / `gen_directives.gloss_handling` / `gloss_targets[]` / `gloss_targets[].background_facts[]`。生成済みスレ本文・過去台本・採点quoteは渡さない。
- **生成物**：`parts_kaisetsu_v2_plan.md`（解説4本の `thread_guard_headline` / `body_without_bridge` / `claim_table` / `bridge_later方針`）。ガイドは `youtube-script-parts/references/kaisetsu-v2-guide.md` を使う。
- **スレ生成へ渡すもの**：`thread_guard_headline` の一覧だけ。`body_without_bridge` や `claim_table` は渡さない（スレ側が解説本文をなぞるのを防ぐ）。
- **P3-B時の追加生成物**：ユーザーが P3-B / guard packet を明示した場合だけ、`v2_guard_packet.json` も作る。中身は `label` / `aliases` / `thread_may_say` / `thread_should_not_say` / `danger_claim_keywords`。これは解説本文ではなく、スレ本文が説明し切ってはいけないclaimの予約表である。
- **P3-B時にスレ生成へ渡すもの**：`thread_guard_headline` に加えて `v2_guard_packet.json` を渡す。ただし `body_without_bridge` と `claim_table` の本文は渡さない。guard packet には禁止claimと許可断片だけを入れ、解説本文の言い回しをなぞらせない。
- **P6-fix時のnatural-demand test**：brief-contract v1.2 の `gloss_targets[].demand_type` と `thread_core_question.front/back` を確認する。`narrative_required`（スレ本筋を成立させるため説明必須）の語そのものは原則として解説対象にせず、`explainable_layer` の史料・制度・研究史・誤解整理など一段深い `meta_background` claim へずらす。M5初期判定が無い場合は STEP1.5 で人/LLMが確定し、`narrative_required` ばかりで解説対象が作れない時は停止してテーマ/解説対象を再設計する。
- **P6-fix2時の本筋重複テスト**：各解説候補について「この解説の `core_new_claim` は、対象スレの `thread_core_question` への答えになっているか？」を必ず確認する。YESなら、たとえ `hybrid` に見えても `narrative_required` に倒し、解説対象から外す。スレタイの問いはスレ本文が自然に結論まで議論してよく、解説は出典・制度・読み・後日談・別レイヤー背景など、問いの答えそのものではない層を担当する。
- **P6-fix3時の解説対象再選定**：`core_answer_risk=high` の候補は原則として解説対象にしない。`demand_type` は既存3値を維持し、`core_answer_risk` は補助フィールドとして扱う。解説対象に残す場合は、`core_new_claim` がスレ本筋の答えではなく、出典・制度・読み・後日談・別レイヤー背景にずれていることを記録する。
- **P6-fix5時の解説対象再選定**：`core_answer_risk=high`、タイトル/核心問いの答えそのもの、スレ本筋で自然に語られる語は解説対象から外す。残すのは制度史・史料・読み・後日談・周辺背景など、スレ本筋の答えではない横の背景だけ。解説対象が作れない場合は、生成に進まずテーマ/構成/候補を再設計する。
- **P6-fix時の追加生成物**：ユーザーが P6-fix / reserved_claims を明示した場合だけ、`reserved_claims.json` も作る。保存先は案件/evalサンドボックス（例 `eval/p6fix_trials/<theme>/reserved_claims.json`）であり、スキル正本や本番案件フォルダには置かない。中身は `claim_id` / `owner` / `demand_type` / `claim_text` / `verdict_essence` / `key_phrases` / `aliases` / `allowed_prelude` / `forbidden_zones` / `source_fact_ids` / `c2_type`。`allowed_prelude`（名前だけ・疑問・短い茶々・断片）は挿入前でも許可し、`forbidden_zones` は同密度の陳述・結論・背景説明だけを禁じる。
- **品質条件**：各解説に新規claimを2つ以上入れ、少なくとも1つはC2の②背景構造/③諸説整理/④出典史料にする。定義文「〜とは」はデフォルトにしない。
- **manifest指定**：v2先行解説で定義文以外の書き出しを使う場合のみ、manifest top-level に `"kaisetsu_opening_style": "freeform"` を明示する。未指定時は通常v1として「〜とは」型チェックを受ける。
- **橋渡し**：この時点では本文に入れない。スレ確定後、各解説につき1文だけ後付けする（採点表v1.3の橋渡し1claim枠に合わせる）。
- → `thread_guard_headline` 一覧と解説4本の役割を提示して確認。P3-B時は `v2_guard_packet.json` の要約（対象・禁止claim・許可断片）も提示して確認。P6-fix時は `reserved_claims.json` のclaim数、`demand_type`、`forbidden_zones`、`verdict_essence` を提示して確認。確認後にSTEP2へ進む。

### STEP2 創作スレ生成 ×2  → `/creative-thread-gen`
- 前半・後半を**各1本ずつ**生成。出力＝「`番号: 本文`」形式（>>Nアンカー保持・欠番不規則はスキル側責務）。
- 📏**雑学モード専用のスレ本文尺ゲート（通常オリジナルスレには適用しない）**：
  - 発動条件は、案件が大カテゴリ雑学で `content_mode: "zatsugaku"` または `length_policy.profile: "zatsugaku"` を manifest/brief に持つ場合のみ。通常の人名・事件型オリジナルスレにはこの基準を掛けない。
  - 基準は **スレ①最低2,500字 / スレ②最低2,500字 / スレ合計最低5,000字**。対象はスレ本文のみで、冒頭・前置き・解説・締めのナレ文では水増ししない。
  - `creative-thread-gen/qa_check.py` の `本文字数: 2500 PASS` は「単体スレの最低QA」であって、雑学回の完成尺ではない。雑学回では各スレごとに2,500字を下限にする。
  - 生成後・増補後・manifest化前に `python3 scripts/check_zatsugaku_length.py <manifest.json>` を通す。FAILならSTEP4へ進まず、雑学レスを増補して再qaする。
- ⚡**生成プロンプト必須要素＝「尺設計図→中尺・長文ファースト」を必ず先に書かせる（2026-06-21崇徳実走の教訓・初稿字数FAILの主因）**：
  - サブエージェント/workflowにスレ生成を投げるときは、creative-thread-gen STEP2の「尺を出す機構」をプロンプトに**必ず引き継ぐ**：①**長文10本×130〜150字＋中尺14本×50〜90字を先に書き切って2,500字の床を確定**→②その後に短レス・淡々レスを挟んで質感を作る。
  - ❌「8〜9割は淡々・短レス」を**床確定より先に**強調しない（順序を逆にすると短レスばかりで字数不足＝初稿FAIL）。淡々の質感づくりは**長文の床ができた後**の工程。
  - 解説対象になりうる難読固有名は、スレ本文の中尺・長文レスに自然に登場させておく（STEP3で拾えるように）。
- **v2/P3-A時の追加条件**：STEP1.5で確定した `thread_guard_headline` 一覧だけを渡す。スレ本文は見出しの結論・背景・出典をまとめ切らず、断片・煽り・疑問・一点うんちくに留める。`body_without_bridge` と `claim_table` はスレ生成側に渡さない。
- **v2/P3-B時の追加条件**：`thread_guard_headline` と `v2_guard_packet.json` を creative-thread-gen に渡す。生成後は `qa_check.py --profile v2 --guard-packet <v2_guard_packet.json>` を通し、`v2 C4 guard` の `NEEDS_FIX` が出たら、該当レスから結論・背景・出典・因果の説明し切りを削り、疑問・煽り・一点断片へ戻して再qaする。WARNはC4先食い候補として目視し、説明し切りなら同じく直す。
- **v2/P3-C時の追加条件**：P3-B guard packetは維持したまま、`qa_check.py --profile v2 --guard-packet <v2_guard_packet.json> --lecture-rewrite-gate` も通す。`v2 lecture rewrite gate` の `NEEDS_FIX` が出たら、長文の条件列挙・一般化説明・結論整理を、質問・茶々・疑問・断片・住人反応へ崩して再qaする。WARNはB3講義臭候補として目視し、盲検B3で拾われそうなら同じく崩す。通常v1ではこのゲートを使わない。
- **v2/P6-fix時の追加条件**：P3-B guard と P3-C lecture rewrite gate を維持したまま、`qa_check.py --profile v2 --guard-packet <v2_guard_packet.json> --lecture-rewrite-gate --conclusion-cluster-gate` も通す。`v2 conclusion cluster` は単発語句ではなく、終盤ウィンドウや解説後ブロックで評価・総括・教訓化レスが束になっているかをcluster単位でWARN計測する。WARN cluster は、質問・茶々・疑問・断片・住人反応へ崩す候補として目視する。通常v1ではこのゲートを使わない。
- **v2/P6-fix3時の追加条件**：P6-fix2までの全v2ゲートを維持し、スレ本文は「問いを作る。答えを完成させない」役割に固定する。`qa_check.py --profile v2 --guard-packet <v2_guard_packet.json> --lecture-rewrite-gate --conclusion-cluster-gate --filler-repetition-gate` を通し、`v2 conclusion cluster` の `NEEDS_FIX` は必ず修正する。C6/解説後再説明は `qa_check.py` 単体では判定せず、STEP4.5の `check_claim_leak.py --manifest --csv` で全文検査する。
- **v2/P6-fix4時の追加条件**：P6-fix3を維持し、スレ終盤を「締めない」役割に固定する。終盤レスは結論・教訓・総括・余韻回収をせず、具体物・茶々・疑問・未解決感・次の問いだけにする。`v2 conclusion cluster` の `ending_role` / `ending_echo` / `viewer_takeaway` を含む `NEEDS_FIX` は、cluster全体を具体反応へ崩して再qaする。closing essenceとの重複やC6は `qa_check.py` ではなく、STEP4.5の `check_claim_leak.py --manifest --csv` で判定する。
- **v2/P6-fix5時の追加条件**：P6-fix4を維持し、終盤8レスに `thread_terminal_cap` をかける。終盤8レスでは88字以上の大レス、総括、教訓、余韻回収、評価保留を禁止し、具体物・茶々・疑問・未解決感・次の問いだけにする。`qa_check.py --profile v2 --guard-packet <v2_guard_packet.json> --lecture-rewrite-gate --conclusion-cluster-gate --terminal-cap-gate --filler-repetition-gate` を通し、`v2 terminal cap` の `NEEDS_FIX` は必ず修正する。
- 品質バー（→ 下記「品質バー」）：**ハードゲートはPASS必須**／WARN系AI癖は**非ブロック（出荷可）**／フル本物化は任意。
- ⚠️**拡張・リライトで本文を増やしたら必ず再qa**（崇徳実走で「呪い殺した」の禁止語が増量時に再混入した）。
- 同一FAILが再生成K回（暫定2〜3）で直らなければ打ち切り→ユーザーへエスカレ（無限ループ防止）。
- → 各スレの qa 結果（PASS/WARN）を提示して確認。

### STEP3 解説対象＆挿入位置の選定 → 解説者パート生成  → `/youtube-script-parts`
- **v2/P3-A時**：STEP1.5の `parts_kaisetsu_v2_plan.md` を採用し、ここでは解説本文をゼロから作り直さない。スレ本文を読んで決めるのは、①各解説の `after_seq`、②1文だけの橋渡し、③C6を避けるための挿入位置調整に限る。
- **v2/P3-A時の挿入位置**：対象用語クラスタの末尾ではなく、対象トピックの最終出現後を第一候補にする。後続スレ・別スレ・締めナレで同じ密度の再説明が起きそうなら、C6リスクとして記録し、位置または後続本文を見直す。
- **v2/P3-A時の橋渡し**：各解説につき1文だけ追加。スレ直前の話題を受けるだけにし、新規情報や要約を詰め込まない。橋渡し2文目以降は禁止。
- **v2/P3-A時の確認**：解説ごとに `after_seq` / 橋渡し文 / C1-C2-C4-C6自己チェックを提示して確認。採点基準は台本採点表v1.3。
- **v2/P6-fix時のclosing/opening/bridge契約**：締めは `youtube-script-parts/references/closing-v2-guide.md` を使う。`reserved_claims.json` の `verdict_essence` をnegative constraintsとして渡し、締めでは情報の再説明・新規claim・解説claimの回収を禁止する。役割は感情の着地、余韻、次回誘導のみ。opening/bridgeも話題名の再掲は許容するが、claimの結論再掲はしない。
- **v2/P6-fix4時のclosing essence**：締めが担当する余韻・着地・次回誘導の `ending_essence` を `reserved_claims.json` または `terminal_policy` に記録する。スレ終盤・opening/bridgeが同じ essence を先に同密度で言った場合は、締めの役割先取りとして修正する。
- **v2/P6-fix5時のclosing claim再説明ゼロ**：締めは感情の着地・余韻・次回誘導のみ。解説claimの要約、別角度化、評価保留、総括講義を入れない。closingで解説claimが同密度に再説明される場合は、closing側を直す。
- スレ本文から**難読固有名トップN**を解説対象に抽出 →【提案→確認】（既定＝各スレ2本＝計4）。
- 各解説の**挿入位置**も【提案→確認】＝**対象用語クラスタが一段落した直後（次の話題へ移る前）**。初出直後ではない。
- 冒頭(5〜6セル)/前置き(1本・3〜4セル)/締め(5〜6セル)＋解説×N(各2〜4セル)を生成。
- 📏**ナレ文量の上限（2026-06-21崇徳検証の教訓・テンポ維持）**：解説は**1本あたり200字級（各2〜3セル）**に抑える＝用語の核だけ説明し、枝葉（経典名の全列挙等）は削る。**ナレ総量（冒頭+前置き+解説+締め）はスレ本文合計の25%目安**（将門21%が基準・崇徳は36%に肥大してテンポが重くなった＝悪例）。超えたら圧縮してから組む。
- 複数ドラフトが出たら**採用版を選び、どの解説をどの after_seq に紐付けるか**を【提案→確認】。
- → 採用版パスと after_seq 対応を確認して manifest へ。

### STEP4 アセンブル【心臓部】 → `scripts/assemble_csv.py`
1. 確定した **reply_map（seq:seq）** と **inserts（after_seq）** を manifest(JSON) に書く（スキーマ＝`refs/組み立て規約.md`）。
   - **雑学モードだけ** manifest top-level に `"content_mode": "zatsugaku"` と `"length_policy": {"profile":"zatsugaku","min_thread1_chars":2500,"min_thread2_chars":2500,"min_total_thread_chars":5000}` を入れる。通常オリジナルスレでは入れない。
   - `assemble_csv.py` は上記フラグがある場合だけ、組み立て前にスレ本文尺ゲートを自動実行する。短ければ exit 2 で止まるため、通常案件の§4.8には影響しない。
   - ⑦**まず骨格を半自動生成**：`python3 scripts/seed_reply_map.py <thread.md>` で本文の明示`>>`をraw→seq変換して自動シード＋スレタイ反応候補を出す。これを土台に**暗黙の返信（相づち/反論→直近の実体レス）だけ**を §6.5/6.6 に従い本文を読んで足す（暗黙分はregex不可＝意味で判断）。
   - **v2/P4時の追加手順**：ユーザーが v2 / P4 / reply_map拡充を明示した場合だけ、seed後に `python3 scripts/suggest_reply_map_v2.py <thread.md> --reply-map '<現reply_map>'` を実行し、自然返信候補を列挙する。これは**候補出力のみ**で、manifestへ自動適用しない。採用は `refs/reply-map-v2-guide.md` と `refs/組み立て規約.md` のv2規約に従い、LLM/人が本文を読んで決める。採用対象は、スレタイ反応・直近疑問への返答・茶々・ツッコミ・短い反論・明確な相づちだけ。長文説明、話題の口火、対象が曖昧な「それ」、大/大直後で§7.2により抑制されるレス、C1/C4/C6/B3を悪化させるレスは採用しない。B2目標は30〜55%だが、数字合わせの偽アンカーは禁止。自然な天井が30%未満なら `reply_map_v2_review` に理由を残して進む。
   - `>>1`バースト（概ね seq2〜5）も明示。after_seq・reply_map はすべて **seq空間**（raw原番号は載せない）。
   - ⑤大判定の境界±5字(83〜92字)を明示確定したいときは `dai_override`（seq→true/false）を載せる（任意・未指定は§4.8が一覧で確認を促す）。
   - 通常v1の解説は manifest 未指定でよい。`scripts/assemble_csv.py` が `解説：...` ラベルの先頭セルに「とは」が含まれるかを§4.8で検査する。v2先行解説だけ `"kaisetsu_opening_style": "freeform"` を明示して除外する。
   - ⑧**話者は番号seqに対する5人固定ローテ**：`1=男性A / 2=女性B / 3=男性C / 4=女性D / 5=男性E / 6=男性A...`。`ids` による同一投稿者の話者据え置きは、YMM4上の同一話者連続・ローテ飛びを生むため廃止（2026-07-03）。同一人物の継続説明にしたい場合は、話者ラベルで逃がさず本文側で1レス/1セルにまとめる。
2. 実行：`python3 scripts/assemble_csv.py <manifest.json>`
   - 話者ローテ・大/下・>>・解説挿入・句読点改行を機械付与。**スレ本文は不改変**。
   - 出力＝`<base>_台本.csv`(utf-8-sig/句読点改行) ＋ `<base>_台本.md`(人間可読)。§4.8 PASS時は同じ案件フォルダをSSD側にも自動ミラー（`/Volumes/SSD/YouTube/創作スレ下書き/...`、削除同期なし）。`~/Desktop` への複製は標準では作らない（ユーザー明示時だけ一時コピー）。
   - **§4.8 受入チェックを自動実行**し、NGがあれば **exit 2**（"完成"と言わせない）。
   - after_seq が実在しなければ即エラー（無言スキップ禁止）。
3. → §4.8 の結果を提示して確認。特に：「抑制で消えた返信リンク一覧」／⑥**安価率**（組立CSV目安30〜55%・実績≈45%。帯域外なら reply_map が盛りすぎ/薄すぎ＝再調整）／⑤**大グレーゾーン未確認一覧**（必要なら dai_override で確定）／**下大ラベルなし**／**解説パート先頭=「とは」型**。
   - ⚠️ **§4.8 PASS＝出荷可ではない**。§4.8は構造整合のみ＝返信先が会話として噛み合うかは検査しない。**会話の正しさは STEP4.5（敵対監査・LLM）で担保**＝両方通って初めて出荷可。

### STEP4.5 敵対的"本物らしさ"監査【必須・機械ゲートの穴を埋める】
- **⓪まず返信取りこぼしの機械監査（必須・最初に実行）**：`python3 scripts/audit_replies.py <manifest.json>` で「アンマップだが直近の別投稿者への本物の反応かもしれない」候補を [高/中/低] で炙り出す（同一投稿者の継続は ids で機械除外）。[高]を中心に**それ/草/ツッコミ/相槌/反論で対象が一意な本物の反応だけ** reply_map に足す（§6.5）。話題の口火・一般論・対象が曖昧・同一投稿者の継続は足さない。**数字合わせで本物を削らない＝安価率55%超でも本物優先**。§4.8(構造)・FAR_GAP(離れた返信)では拾えない「削られた隣接反応」をここで毎回潰す。
- **v2/P4時**：STEP4で作った `reply_map_v2_review` をここでも再確認する。採用した候補が、解説予定claimの先食い（C4）、解説後の同密度反復（C6）、講義臭レス化（B3）、解説本文との語彙一致（C1）を増やしていないかを本文意味で見る。§4.8 PASS後も、会話として不自然なアンカーは外す。
- **v2/P6-fix時**：`python3 scripts/check_claim_leak.py --reserved <reserved_claims.json> --artifact front:<front_thread.md> --artifact back:<back_thread.md> --artifact opening:<parts_opening.md> --artifact bridge:<parts_bridge.md> --artifact closing:<parts_closing.md> --out-json <claim_leak_candidates.json> --out-md <claim_leak_candidates.md>` を実行し、全文アーティファクトのclaim漏れ候補を列挙する。機械ショートリストは高再現・低精度でよく、LLM/人が `same_density=true/false` を付ける。`same_density=true` が closing／解説後の同一スレ／other_thread に残る場合は NEEDS_FIX。解説前C4先食いは既存C4 guardを一次判定にし、leak gateはアセンブル前後の全文バックストップと証跡に使う。E軸として候補数、NEEDS_FIX数、conclusion cluster WARN数、再走回数、手修正回数を記録する。
- **v2/P6-fix3時**：アセンブル後に `python3 scripts/check_claim_leak.py --reserved <reserved_claims.json> --manifest <manifest.json> --csv <assembled.csv> --cooldown-window 12 --artifact opening:<parts_opening.md> --artifact bridge:<parts_bridge.md> --artifact closing:<parts_closing.md> --out-json <claim_leak_candidates.json> --out-md <claim_leak_candidates.md>` を実行する。manifestの `after_seq` とCSVのスレ番号から、解説後8〜12レスを `post_explain_cooldown_zone` として切り出す。`same_density=true` が `post_explain_cooldown_zone` / `closing` / `other_thread` に残る場合は NEEDS_FIX。話題名だけ・茶々・軽い驚きは許容し、解説claimの要旨・背景・評価軸の再説明だけを修正する。
- **v2/P6-fix4時**：上記に加えて `reserved_claims.json` の `ending_essence` / `terminal_policy.forbidden_ending_essence` を使う。`thread_terminal_ending_role_zone` または `narr_ending_role_zone` で `same_density=true` が残る場合は NEEDS_FIX。closing自身は `closing_essence_owner` として許容し、スレ終盤・opening/bridgeが締めの余韻や視点変更を先取りした場合だけ直す。
- ultracode 5レンズ並列LLM監査＝①なんJ語感 ②アンカー整合 ③講義臭 ④AI臭残留 ⑤規約。
- **必ず捕捉する must_fix**（機械化しにくい content）：
  - **講義臭＝ナレVO化**（元号+西暦キャプション+終止形現在で長文開始）→ 掲示板口調へ。
  - **構成を知っている住人セリフ**（「具体例は次スレで見る」「ここでは止めとく」など）→ 編集者/台本進行の声なので、直前レスへの在スレ反応へ。
  - **二重主語の文法よれ**（「将門は…討伐軍が苦戦しとった」）→ 述語一本化。
  - **文末専用表現の文頭使用**（「知らんけど」を文頭に）→ 文末へ。
  - **返信アンカーが会話の流れと噛み合うか**（§6.6 後方ジャンプ＝①66型）。
  - **現代の実在個人の実名**（→ STEP5カテゴリ7だが、ここでも拾ったら匿名化）。
- must_fix を出したら該当レスを修正 → **再qaでPASS維持を確認** → 差分提示 → 確認。
- 偽陽性（サイズ交絡・辞書バイアス・スクレイプ崩れ）は棄却。

### STEP5 規約3段階チェック → `/youtube-script-checker`
- 8層スキャン＋LLM文脈＋ファクトチェック。
- **近代政治色**（GHQ/米軍/進駐軍/特定政党 等）検出→**歴史一般化**で修正（戦後の区画整理/重機/国家事業/お役所）。
- **現代の実在個人**はカテゴリ7で🔴→**匿名化**（例：実在芸人の実名+負の逸話→「売れる前の若手芸人」）。
- → 🔴は出荷不可。修正して再チェック。

### STEP6 読み仮名dic → `/ymm4-dic-generator`
- 最新スキル（**v3.1 漢字温存チャンク方式・2026-07-07実機PASS**）で毎回書き換え。**漏れ/誤読ゼロ**を機械確認（`validate_dic.py` PASS＋全チャンクレビューTSV）。出力＝案件フォルダ直下の `ymm4_user.dic` を正本にし、案件フォルダのSSDミラーで `/Volumes/SSD/YouTube/創作スレ下書き/YYYY-MM-DD_テーマ/ymm4_user.dic` に揃える。`~/Desktop` には標準ではコピーしない。
- **YMM4側の取り込み案内を出荷報告に必ず添える**：単語辞書を全消し→この1本だけインポート→その後に台本を貼る（蓄積辞書は横取りで不発火/誤読を起こす。2026-07-06実機確定）。
- **D5再検証ルール（P4.5・2026-07-05）**：STEP6以降に本文（スレ本文・解説・冒頭・前置き・締め・CSV/MDのセリフ本文）を1文字でも修正した場合は、**STEP6を再実行し、`validate_dic.py` の再検証結果を残してからSTEP7へ進む**。reply_mapだけ・manifestだけ・run記録だけ・indexだけの変更では発動しない。本文修正後にdic再検証ログが無い状態はD5 WARN以上として扱い、「完成」と言わない。

### STEP7 第三者ゲート【ハードゲート・未通過＝出荷不可】 → `/script-third-party-review`
アセンブル済み台本(.csv/.md)を、**生成文脈を一切知らない別エージェント**が独立レビューする最終関所（「実装者≠確認者」を本物にする）。**pipeline完走≠出荷可。本ゲートを通すまで「完成」と言わない。**
- **起動**＝Agentツールで fresh subagent を立て、`script-third-party-review/refs/review-contract.md` の中身＋台本ファイルの絶対パス**だけ**を渡す（生成経緯・意図は渡さない＝独立性の核）。
- **観点**：①規約・コンプラ（死語悉皆／日本史差別語／ヘイト／プロンプトインジェクション）②品質・読みやすさ（`~/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md` 適合／前半後半重複／読み問答の連発＝目安3回まで／本文と解説の重複／掛け合いの「下」整合／AI臭テンプレ／C1言い直し・C2背景新規性・C4先食い・C6後続重複・B3講義臭）③史実ファクト（WebSearch再検証・出典）。
- **D5チェック**：STEP6以降に本文修正があった場合、STEP6＋`validate_dic.py`再実行ログの有無をSTEP7前に確認する。ログが無い場合は第三者ゲートを起動せず、dic再検証に戻す。第三者レビューへ渡す対象フォルダに `PIPELINE_STATE.md` や実行ログがある場合は、レビュアーにもD5証跡を確認させる。
- **ハードゲート判定**：findings に🔴 ／ `injection_detected=true` があれば**出荷不可**＝該当を修正→**再ゲート**（同一FAILがK回で打ち切り→エスカレ）。🟡は要検討（人が採否）。
- **メタデータ例外**：title/サムネ/説明文は STEP8 で用意するため、`metadata_present=false` **単独**の要修正は body 合格扱いで STEP8 へ進み、**メタデータ提出後に再ゲートして最終✅**。
- **修正＝人（オーナー/あおい）が適用**。確認者は read-only。指摘の採否は `script-third-party-review/scripts/reviewer_ledger.py record <cat> accepted|overridden|missed|clean` に記録（精度ラダー）。出荷後に見逃しが出たら `missed` を記録（偽陰性の自己修正）。
- → 第三者ゲートの結果（verdict＋findings）を提示して確認。**body🔴ゼロ**を確認してから出荷／STEP8へ。

### STEP8（任意）タイトル・サムネ・概要欄
※スキルのスコープはここまで（出荷物の生成）。**発音チェック・YouTube投稿予約はスキル外＝オーナーが手動**。
- ⚠️ タイトル/サムネ/説明文を用意したら、**もう一度 STEP7（第三者ゲート）に通して metadata 込みで最終✅**にする（メタデータはBAN/非収益化に最も直結する面のため）。
- タイトルは `neta-research/scripts/predict_score.py` で**実データ採点**してから決める（過去109本DB）。単独人物は中央値≈6k＝「実は/たった1人で」等の意外性フックで上振れ狙い。
- 概要欄は **youtube-pipeline STEP6 の実データ準拠テンプレ**に従う（短く150〜250字・**解説者の声/である体**・AI広告語禁止・冒頭ナレと地続き）。
- **見本＝平将門のメタ情報**：`Projects/youtube/創作スレ下書き/2026-06-17_平将門の祟り_メタ情報.md`（タイトル/サムネ/概要欄の確定例）。

## 品質バー（3段の合格ライン）
- **ハードゲート＝PASS必須**：字数／禁止語(死/殺す/アホ/バカ/クソ/カス 等。※歴史文脈の裸の「死」はqa許容)／
  SLUR・ヘイト／規約🔴／時代タグFAIL／ASCII`"`／**第三者ゲート(STEP7)の body🔴・`injection_detected`**。**1つでも引っかかれば出荷不可・自動承認しない**。
  - 雑学モード（`content_mode: zatsugaku`）では、上記に加えて **スレ①2,500字以上 / スレ②2,500字以上 / スレ合計5,000字以上** をハードゲートにする。通常オリジナルスレは既存の字数ルールのまま。
- **WARN系AI癖＝非ブロック（出荷可）**：SCAF密度／感情温度／壁化／9f密度／単一語尾過集中／ナレ接着頭／長文独り語り 等。
  デフォルトWARNのまま出荷可（毎回フル平準化はしない）。※WARN非ブロック出荷は実績まだ薄い暫定運用＝初回は事後評価する。
- **フル本物化（選択肢C）＝任意STEP**：長文を淡々・ぶつ切りに総リライトしWARNも全消し。看板回だけ・重いので毎回はやらない。
- 「本物らしさの天井」（評価締めの同一ビート反復/時系列一本道/死にレス少なめ）は**意図的に追わない**。

## 出荷物（保存先 = `Projects/youtube/創作スレ下書き/YYYY-MM-DD_テーマ/`）
- `_台本.csv`（YMM4取り込み・utf-8-sig・句読点改行）＝**唯一の出荷フォーマット**
- `_台本.md`（人間可読・構成見出し付き）
- 案件フォルダ直下の `ymm4_user.dic`（STEP6）
- `/Volumes/SSD/YouTube/創作スレ下書き/YYYY-MM-DD_テーマ/` への案件フォルダ複製（SSDがある時のみ・削除同期なし）
- `~/Desktop` へのCSV/dic複製は標準出荷物ではない。ユーザーが明示した時だけ一時コピーする
- ※**xlsx は作らない**（オーナー決定2026-06-20）。目視は show_widget の会話ビューアを**単発依頼で**出す。

## 学習と自動化グラデーション（Phase2・2026-06-21実装）
判断ルールは `learning-log.md` に prose で（値は汎化しない）。STEP別の成熟度は **`scripts/maturity.py`＋`automation-state.json`** で機械管理する。

**鉄則（絶対）**：①**勝手に自動化しない＝提案だけ**（flipはユーザーが「自動化していい」と言った後のみ）。②**🔴/FAIL/qa NEEDS-FIX のハードゲートは永久にauto不可**（STEP5規約・STEP7第三者ゲートは hard_gate＝ロック）。③**auto中に修正が入ったら即manual降格**（自動が早すぎたサイン）。④autoは「ユーザー確認をスキップ」するだけで、機械ゲート（qa・§4.8・規約🔴）は必ず実行する。

**運用フロー**：
1. **セッション開始時**に `python3 scripts/maturity.py status` を見る。mode=auto のSTEPは確認スキップで進めてよい（ハードゲートは実行）。manual は従来どおり提案→確認。
2. **各STEP完了時**に結果を記録：ユーザーが提案をそのまま承認＝`record <STEP> approved`／修正が入った＝`record <STEP> modified "理由"`。modifiedは連続をリセット。
3. K回（既定3）連続approvedになったSTEPは record時に「💡自動化を提案できる」と出る→**ユーザーに『このSTEP自動化していい？』と確認**→OKなら `flip <STEP> auto`。
4. 自動化が進みやすい順＝STEP4アセンブル ＞ STEP6 dic ＞ STEP3解説選定（判断が安定しやすい順）。**STEP5規約・STEP7第三者ゲートは永久にmanual**（必ず実行＝出荷の関所）。
- creative-thread-genの学習ループ（収集→学習→**承認**→検証付き適用・実装者≠確認者）と同一哲学。金/出荷に関わる所の検証ゲートは残す（rules.md準拠）。

## エッジケース
- 解説対象が0本/多すぎ/スレに出てこない → 代替提案（用語追加 or 本数調整 or スキップ）。
- after_seq 実在しない → 即エラー（§4.8で本数発火を機械検証）。
- ハードゲートが直らない → creative-thread-gen に差し戻し、K回で打ち切り→エスカレ。
- 本文の広域修正（頭リライト/フル本物化）後 → **大/下再判定→反転レスの返信マップ再判断→差分再qa**を1セットで。
- 再実行：中間生成物（スレmd・manifest）を保存し再利用。出力は上書き。

## v2/P6-fix6 thread-first / post-hoc sidecar selection（追加・v2専用）

P6-fix6を明示して実行する場合だけ、解説対象を先に固定しない。先に前半・後半スレ本文を生成し、その後に「スレ本文がまだ説明していない横の背景 claim」だけを解説対象として選ぶ。

1. STEP2では `gloss_targets` を固定の解説予定語として扱わない。スレ本文は本筋を自然に進めるが、講義調・締め調・終盤総括は禁止する。解説claimを守るためのguard packetはこの段階では未確定なので、P6-fix5までのスレ単体ゲート（lecture / conclusion / terminal cap / filler）を優先する。
2. STEP2完了後、`select_sidecar_claims_v2.py` で brief の `sidecar_candidate_pool` / `gloss_targets` / `background_facts` と完成スレを照合し、候補claimを列挙する。候補抽出は自動採用ではない。
3. STEP3前に `check_claim_leak.py --c1-precheck` で候補claimごとの言い直し率・語彙一致・本筋重複を確認する。`lexical_match=true`、`core_answer_risk=high`、`demand_type=narrative_required`、またはスレ本文が要旨を言い切っているclaimは解説対象から外す。
4. `C1_precheck` を通ったsidecar claimが4本確保できない場合は停止する。足りないまま本筋語を解説化して数合わせしない。
5. 選ばれたsidecar claimだけを `youtube-script-parts` のv2解説生成に渡し、`reserved_claims.json` に保存する。以後のclaim leak / closing / C6検査は従来どおりreserved_claimsを正とする。

この追加はv2/P6-fix6明示時のみ有効。通常のv1運用、既存STEP、既存ハードゲートは削除・置換しない。
