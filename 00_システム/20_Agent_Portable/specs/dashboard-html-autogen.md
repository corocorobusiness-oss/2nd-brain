# AIシステムダッシュボードHTML 自動生成（dashboard-html-autogen）

作成: 2026-07-16（あおい / Claude Code）
状態: **スクリプト・テンプレ完成／launchd未設置（設置は要承認）**

## 目的

`06_エージェント運用/00_司令塔/AIシステムダッシュボード.html` を毎朝作り直し、
タスク・期日・今日のデイリーノート・自動化ジョブ数が常に最新の状態で見られるようにする。

## 構成

| ファイル | 役割 |
|---|---|
| `00_システム/20_Agent_Portable/scripts/generate_dashboard_html.py` | 生成スクリプト（Python3 標準ライブラリのみ・READ中心） |
| `00_システム/20_Agent_Portable/scripts/dashboard_template.html` | テンプレート（プレースホルダ入りHTML・図SVG焼き込み済み） |
| `06_エージェント運用/00_司令塔/AIシステムダッシュボード.html` | 出力（唯一の書き込み先。手で編集しない） |

読み取るもの:
- **お金**: `02_経営/目標と計画.md`（当月の予算行）／`05_日誌/*.md`「今日の売上」表（Uber Eats・出前館・ロケットナウ=デリバリー、YouTube。当月分を集計→実績・達成率・日割りペース比・累計グラフSVG）／デイリーノートの `dashboard:start` ブロック（freee数字。当月未記入なら直近の記入済みを日付付き表示＋停止警告）
- **YouTube運営**: `00_司令塔/YouTube週間ボード.md`（投稿予定・制作中・やること＝正本）／`来月ネタ草案_YYYY-MM.md`（在庫と台本状況）／タスクボード📺節
- **タスク**: タスクボード.md（📌今週やる）／期日タスク.md（`- [ ] YYYY-MM-DD` 行）／`05_日誌/今日.md`（メモ欄）
- **ジョブ数**: 導入済み.md（`| com.xxx |` 行の🟢🟡🛑を集計＋nightly-refresh・daily-dashboardを加算）

デザインは「AI Company OS」風のダーク固定（サイドバー・KPIカード・進捗バー・SVGチャート）。アンカー: `#money` `#youtube` `#tasks` `#status` `#team` `#flow` `#help`。

## 実行方法（手動）

```bash
python3 ~/2nd-Brain/00_システム/20_Agent_Portable/scripts/generate_dashboard_html.py
# 引数でvaultルート指定可。成功時は "OK: <出力先> ..." を表示
```

検証済み（2026-07-16・リポジトリ環境）: 今週=1件・期日=8件表示＋残7件・counts=(🟢27, 🟡2, 🛑4, 計33)＝台帳と一致。

## launchd設置手順（Mac mini・要承認: 自動化ジョブの新規追加）

1. 祐馬さんのGOを確認する
2. plistを作成: `~/Library/LaunchAgents/com.claude.dashboard-html.plist`
   - Label: `com.claude.dashboard-html`
   - ProgramArguments: `python3` / `/Users/kojinn/2nd-Brain/00_システム/20_Agent_Portable/scripts/generate_dashboard_html.py`
   - StartCalendarInterval: **毎朝 4:10**（daily-dashboard 4:00 の後・非衝突）
   - StandardOut/ErrPath: `~/.claude/logs/dashboard-html.log`
3. `plutil -lint` → `launchctl bootstrap gui/503 <plist>` → `launchctl print` で登録確認
4. **台帳へ追記**: `01_プロジェクト/AI自動化/導入済み.md` の毎日表とMac mini詳細表に1行（報告先: 通知なし・Vault内HTML更新のみ）
5. **Watchtower**: `watchtower_local.py` の `EXPECTED_JOBS` に追加（29→30本）
6. 翌朝、HTMLの「自動生成」日時が更新されているか確認

止め方: `launchctl bootout gui/503/com.claude.dashboard-html`（plistは `~/.claude/archived-launchagents/` へ退避＋Watchtower期待リストから除外）

## 安全性

- 書き込みは出力HTML 1ファイルのみ。タスク・日誌・台帳へは読み取りだけ
- LLM呼び出しなし（非LLM・決定的）。ネットワークアクセスなし
- 台帳の表形式が変わって集計できない場合、ジョブ数は「—」表示に落ちる（嘘の数字を出さない）

## 更新ルール

- 見た目・固定文言を変えたい → `dashboard_template.html` を直す（md正本と内容を揃えること）
- 取得項目を変えたい → `generate_dashboard_html.py` を直す（変更前にバックアップ`.bak-日付`）
- 台帳の詳細表に nightly-refresh / daily-dashboard が正式掲載されたら、スクリプトの `EXTRA_GREEN_LABELS` を空にする（二重カウント防止）
