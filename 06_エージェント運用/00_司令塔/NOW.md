# NOW

最終更新: 2026-06-27

## 今の運用方針

- Claude Codeがメイン司令塔
- Codexは実行補助
- Obsidian / Second Brainが正本
- 重要な決定、ルール、学びは最後にSecond Brainへ戻す

## 今の最優先

1. 会計正本整理を完了する（freee正本 / 旧AI帳簿は参考凍結 / kicho記帳停止・監査専用化）
2. AI自動化ジョブを台帳で管理し、ゾンビ化を防ぐ
3. Second BrainをClaude Code / Codex共通の事業OSとして整える
4. YouTube制作フローを安定運用する

## AIが最初に見る場所

- **作業共有ログ（ツバキ×あおい必読・完了タスクは追記必須）: `06_エージェント運用/00_司令塔/作業ログ_ツバキとあおい.md`**
- ルール: `00_システム/10_Agent/rules.md`
- 手順: `00_システム/10_Agent/workflows.md`
- 目標: `00_システム/10_Agent/goals.md`
- 現在地: `00_システム/00_UserProfile/02_最新コンテキスト(Active_Context).md`
- 自動化台帳: `01_プロジェクト/AI自動化/導入済み.md`
- 実行キュー: `06_エージェント運用/20_実行キュー/今日やる.md`
- 確認待ち: `06_エージェント運用/10_Inbox/要確認.md`

## 今日の基本判断

- 迷ったら「祐馬さんの自由時間が増えるか」を最優先する
- 削除、外部投稿、会計確定、外部アカウント設定変更、自動化停止は確認してから行う
- 生ログや秘密情報は保存しない
- 作業成果物は正しい場所へ戻す

## 会計正本整理の現在地（2026-06-27）

- 会計正本はfreee。証憑正本はDrive/証憑保管側
- `freee_registered_txns.json` は金額正本ではなく、二重登録防止キー台帳
- 旧AI帳簿CSV・仕訳帳・収支管理は参考・凍結・非申告用
- 現行kichoはCSV・収支管理・日誌を書き換えるため、記帳係から外した。2026-06-27に `com.korokoro.kicho-weekly` はbootout＋disable済み
- 2026-06-27再確認: `launchctl print` では未ロード、`print-disabled` ではdisabled。通常実行の `kicho.py` は安全停止のみ
- 後継を作る場合は、freee明細・証憑・補助台帳の差分を見る読み取り専用監査レポートにする
- ✅2026-06-27夜（あおい/Claude Code環境）: `com.korokoro.kicho-weekly` のplistを `~/Library/LaunchAgents/` から `~/.claude/archived-launchagents/com.korokoro.kicho-weekly.plist.archived-20260627` へ退避（削除せず）。`watchtower_local.py` の `EXPECTED_JOBS` からも除外。編集前に `watchtower_local.py.bak-20260627-231245` をバックアップ
- `freee-uncleared-monitor` は2026-06-27にbootout＋disable済み。✅同日夜にplistも `~/.claude/archived-launchagents/com.claude.freee-uncleared-monitor.plist.archived-20260627` へ退避。再開するならplist復帰＋`launchctl enable`＋Watchtower期待リスト追加＋monthly-accounting(10:30)との時刻ずらし(10:45等)/統合が必要（停止整合は完了済み・残るのは再開可否の判断のみ）
- ✅2026-06-27夜（あおい）: Watchtower `EXPECTED_JOBS` 整合完了（計28本）。除外=`channel-lifecycle`(6/24退避済)/`kicho-weekly`、追加=`corpus-collect`/`thread-format-learning`/`demaecan-reminder`/`satellite-autocommit`。手動実行で会計関連の警告（kicho/channel-lifecycle/freee-uncleared/台帳外ジョブ）が全消え・追加4本は全[OK]を確認。独立エージェントでもクロスチェックPASS（実装者≠確認者）
