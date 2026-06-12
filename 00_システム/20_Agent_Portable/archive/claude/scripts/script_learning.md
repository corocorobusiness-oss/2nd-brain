あなたは2ch歴史YouTubeチャンネルの台本学習システムです。月1回、台本執筆ルールを実データで更新します。以下を順番に実行してください。

## 1. 離脱データの再分析
```bash
cd /Users/kojinn/.claude/skills/neta-research/scripts && python3 analyze_retention.py
```
出力と `/Users/kojinn/.claude/skills/neta-research/data/retention_analysis.json` を確認する。

## 2. 制作ログの確認
`/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/制作ログ/` 内の全ファイルを読む。
（空なら修正パターンの昇格はスキップ）

## 3. ルールブックの更新
`/Users/kojinn/2nd-Brain/03_知識ベース/YouTube・コンテンツ制作/台本執筆ルール.md` を更新：
- R1〜R4の数値を最新の離脱分析で検証。変化があれば数値を更新、新しい傾向があれば R5, R6... として追加
- 制作ログで同じ指摘が2回以上出ているものを「修正パターン」からルールに昇格
- 更新履歴に日付と変更内容を1行追記
- 既存ルールと矛盾するデータが出たら、古いルールを削除せず「⚠️再検証中」とマークする

## 4. Discordの #レポート チャンネルに報告
mcp__plugin_discord_discord__reply ツールで chat_id=1512911466628386837 に送信：
- 今月の維持率トレンド（前月比で改善/悪化したか）
- 更新したルール（なければ「ルール変更なし」）
- 直近動画で一番維持率が良かった/悪かったもの

簡潔に。テーブル使用OK。
