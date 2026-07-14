# 設計書：click-learning-loop（サムネ・タイトルのクリック学習＝提案P1）

- 状態: **実装済み（vault側・2026-07-14）**。Mac側残作業は§9
- 発端: [[チャンネル改善システム_提案_2026-07-14]] P1（最優先・売上直結）
- 兄弟仕様: `script-fix-metrics-設計書.md`（同じ思想＝記録→答え合わせ→昇格。あちらは台本品質、こちらはクリック）
- 根拠: R3「再生数の差は維持率ではなくネタとクリック（サムネ・タイトル）で決まる」— なのにクリック側だけ学習ループが無かった

## 1. 何を作るか（3層）

```
[勝ちパターン]                      [記録]                         [答え合わせ]
サムネ・タイトル勝ちパターン.md      click_ledger.py                fetch_click_stats.py（Mac・API自動）
  T系=タイトル / S系=サムネ           publish/ab/stats/touch          → CTR・初動を自動追記
  仮説→2勝で確定へ昇格               → eval/click_ledger.jsonl      click_report.py
                                     （追記のみ）                    → サムネ・タイトル効き.md
```

## 2. 決定的な事実（2026-07-14 WebSearchで確認）

**YouTube Analytics API v2 に 2026-01-15 付でサムネ指標が正式追加された**：
`videoThumbnailImpressions`（サムネ表示回数）／`videoThumbnailImpressionsClickRate`（CTR）／`endScreenElementClicks` 等。
→ CTR収集は**完全自動化できる**（従来はStudio画面のみだった）。認証は既存の `~/.config/youtube-revenue/token_2ch.json`（subscriber_signal.py と同一パターン）を流用。
→ フェイルソフト設計: metric名がAPIに拒否された場合は `views,averageViewPercentage` のみで動き、CTR列を「手動転記待ち」と明示警告する（黙って欠測にしない）。

## 3. データ設計（click_ledger.jsonl・追記のみ・1行=1イベント）

| type | いつ | 主フィールド |
|---|---|---|
| `publish` | 公開時に1行（必須） | folder / theme / title / title_type(自動分類) / kirikuchi[] / thumb{badge,headline,sub} / ab_variants[] / pred |
| `ab_result` | Test & Compare終了時 | winner / detail |
| `stats` | fetch実行ごと（自動）or 手動 | video_id / window(d1-7/cum) / views / thumb_impressions / thumb_ctr / avg_view_pct / source(api/manual) |
| `touch` | タイトル/サムネ差し替え時 | kind(retitle/rethumb) / from / to |

- 保存先: `~/Projects/youtube/eval/click_ledger.jsonl`（fix_metricsと同じ場所・satellite-autocommit対象）
- title_type の自動分類は neta-forge `subscriber_signal.py` の `classify_title` と同一regex（型の定義がM11とズレない）
- video_id は publish 時に不要。fetcher が `channel_videos.json` とタイトル照合して自動解決する
- 差し替え（touch）を分けて記録するのは、P2（公開後72時間ウォッチャー）を将来乗せたときに「差し替え前後のCTR比較」がそのまま出せるようにするため

## 4. ルールブック（サムネ・タイトル勝ちパターン.md）

- 場所: `03_知識ベース/YouTube・コンテンツ制作/`（台本執筆ルールの姉妹ファイル）
- ID体系: `T01..`（タイトル）/ `S01..`（サムネ）。**状態タグ＝仮説/確定**を持つ（scriptルールと違い、クリックルールは実測CTRで検証してから確定にする）
- **昇格条件: 同じ型/切り口がチャンネル中央値CTR超えで2勝**（click_reportが昇格候補を提案→祐馬さん承認→確定へ）
- 初期シードは既存データからの仮説（M11型ランキング・M10切り口・出荷3本のサムネ構造）＝ゼロからではなく今の暗黙知を明文化してスタート
- 制作時は brief→STEP7 でこのファイルを読み、タイトル・サムネ3案を作る

## 5. 運用ループ（週次・当面オンデマンド）

1. **公開時**: `click_ledger.py publish ...` で1行（サムネ2〜3案で **Test & Compare を必須開始**）
2. **週1（Mac）**: `fetch_click_stats.py` → 公開3日以降の動画のCTR/初動をAPIで自動追記 → `click_report.py` → [[サムネ・タイトル効き]]再生成
3. **A/B終了時**: `click_ledger.py ab --winner ...` で勝者記録
4. **月1**: レポートの昇格候補を見て、勝ちパターンを仮説→確定へ（祐馬さん承認制・自動書き換えなし）
5. 安定したら neta-retrain（月曜9:10）への統合を**別途提案**（launchdは当面増やさない）

## 6. KPI（この仕組みの答え合わせ）

- **北極星: 公開7日CTR（videoThumbnailImpressionsClickRate）の移動中央値が上がり続ける**
- 補助1: 初動再生の pred比（ネタ予測と合わせてクリックが足を引っ張ってないか分解できる）
- 補助2: A/Bテスト実施率（新規動画の何%でTest & Compareを回せたか）
- 補助3: 確定ルール数（仮説→確定への昇格数）

## 7. 役割分担

| 作業 | 担当 |
|---|---|
| タイトル型分類・JSONL追記・API取得・集計 | script（決定的処理） |
| サムネ案づくり・切り口選定・昇格候補の解釈 | LLM（勝ちパターンを読んで提案） |
| Test & Compare設定・勝者判断・ルール昇格承認 | 祐馬さん（Studio操作は手動） |

## 8. エッジケース

| ケース | 挙動 |
|---|---|
| APIがサムネ指標を返さない | フォールバックで views のみ取得し「CTR手動転記待ち」を警告表示 |
| タイトル照合でvideo_idが見つからない | 該当行をスキップして「未解決」として必ず表示（黙らない） |
| 公開3日未満 | Analytics遅延（3日）を考慮しスキップ（対象外と明示） |
| 記録漏れ | report が channel_videos.json と突合して未記録の公開を表示 |
| JSONL破損 | 壊れた行スキップ＋警告（fix_metricsと同じ） |

## 9. 実装ログと残作業

### 完了（2026-07-14・vault側＋ミラー経由）

- ✅ ルールブック初期版（T01〜T05・S01〜S04・AB運用ルール・仮説シード）
- ✅ `click_ledger.py`（publish/ab/stats/touch・追記のみ・fail-close）— テスト済み
- ✅ `click_report.py`（6セクション・read-only）— テスト済み
- ✅ `fetch_click_stats.py`（API自動取得・フェイルソフト）— **ロジックのみ実装。実APIはこの環境から叩けないため Mac側で `--dry-run` 必須**
- ✅ 出荷済み3本（中国大返し・秀長・晴明）の publish 遡り記録（実タイトル・実サムネ文言＝各案件フォルダの title.txt / thumbnail.txt から転記）
- ✅ creative-thread-pipeline SKILL.md（正本＋vault控え）のSTEP7へ記録手順を追記

### Mac側残作業

1. 3ブランチマージ＋pull（script-fix-metricsと同じ）
2. **`fetch_click_stats.py --dry-run` で新metric（videoThumbnailImpressions系）が通るか初回検証**（通らなければフォールバック動作を確認）
3. 次の新規公開からサムネ2〜3案で Test & Compare 開始＋publish記録
4. 週1で fetch → report → 効きページ確認（軌道に乗ったら週次スコアカード/P3へ統合）

---
更新履歴
- 2026-07-14 v1 設計＋実装（あおい）
