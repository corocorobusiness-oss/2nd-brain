# NOW

最終更新: 2026-07-02

## 今の運用方針

- Codexを日常のメイン入口へ移行中（フェーズ1）
- Claude Codeは補助・退避先
- Obsidian / Second Brainが正本
- `agent-run` と既存自動化ジョブは段階移行中。Codex切替完了とは扱わない
- Codexメイン・ベンダー非依存化の移行設計: `00_システム/20_Agent_Portable/specs/codex-main-vendor-neutral-migration.md`
- Codexカスタムスキルは `/Users/kojinn/.codex/skills/<skill> -> /Users/kojinn/agent-skills/<skill>` のsymlink運用へ移行済み（21件verify PASS、`.system` はCodex内蔵として保持）
- `script-learning` は手動Codex dry-run入口と通常Terminal wrapper gateがPASS。2026-08-02判定予定で1周期shadow中。launchd既定、Discord本番投稿、ルールブック自動更新は未変更
- 重要な決定、ルール、学びは最後にSecond Brainへ戻す
- 再構築案件は「Fable司令塔・Codex実行」型で進める（`00_システム/20_Agent_Portable/specs/fable-command-codex-execution.md`・2026-07-03採用）

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

## 会計正本整理（正本セクション・ここに集約）

> この件の進捗・判断事項はすべてここが正本。要確認.md など他所には重複を残さない（→各所から本セクションを参照）。

### 進捗サマリー（一目）

- ✅ kicho記帳停止＋後始末（plist退避・Watchtower整合）= 完了
- ✅ freee-uncleared-monitor の停止整合（bootout/disable/plist退避）= 完了
- ✅ `freee-uncleared-monitor` の**再開で決着（2026-06-28・P04）**。ブロック理由が無かったため再開。plist復帰＋時刻を10:45へ変更（monthly-accounting 10:30と非衝突）＋`launchctl enable`＋`bootstrap`ロード＋Watchtower `EXPECTED_JOBS`追加（計29本）。monitor本体はfreee READ（消込待ち集計）のみで書込なし。検証: plutil -lint OK / py_compile OK / Watchtowerジョブ判定で[OK]・野良警告ゼロ（詳細は末尾「決着メモ」）

### 現在地（2026-06-27）

- 会計正本はfreee。証憑正本はDrive/証憑保管側
- `freee_registered_txns.json` は金額正本ではなく、二重登録防止キー台帳
- 旧AI帳簿CSV・仕訳帳・収支管理は参考・凍結・非申告用
- 現行kichoはCSV・収支管理・日誌を書き換えるため、記帳係から外した。2026-06-27に `com.korokoro.kicho-weekly` はbootout＋disable済み
- 2026-06-27再確認: `launchctl print` では未ロード、`print-disabled` ではdisabled。通常実行の `kicho.py` は安全停止のみ
- 後継を作る場合は、freee明細・証憑・補助台帳の差分を見る読み取り専用監査レポートにする
- ✅2026-06-27夜（あおい/Claude Code環境）: `com.korokoro.kicho-weekly` のplistを `~/Library/LaunchAgents/` から `~/.claude/archived-launchagents/com.korokoro.kicho-weekly.plist.archived-20260627` へ退避（削除せず）。`watchtower_local.py` の `EXPECTED_JOBS` からも除外。編集前に `watchtower_local.py.bak-20260627-231245` をバックアップ
- `freee-uncleared-monitor` は2026-06-27にbootout＋disable済み。✅同日夜にplistも `~/.claude/archived-launchagents/com.claude.freee-uncleared-monitor.plist.archived-20260627` へ退避。再開するならplist復帰＋`launchctl enable`＋Watchtower期待リスト追加＋monthly-accounting(10:30)との時刻ずらし(10:45等)/統合が必要（停止整合は完了済み・残るのは再開可否の判断のみ）
- ✅2026-06-27夜（あおい）: Watchtower `EXPECTED_JOBS` 整合完了（計28本）。除外=`channel-lifecycle`(6/24退避済)/`kicho-weekly`、追加=`corpus-collect`/`thread-format-learning`/`demaecan-reminder`/`satellite-autocommit`。手動実行で会計関連の警告（kicho/channel-lifecycle/freee-uncleared/台帳外ジョブ）が全消え・追加4本は全[OK]を確認。独立エージェントでもクロスチェックPASS（実装者≠確認者）

### 残る判断事項（任意・急ぎでない / 要確認.md から集約・2026-06-28）

- ✅【決着メモ・2026-06-28 P04】`freee-uncleared-monitor` は**再開で決着**（上の判断保留を解消）。判断根拠: 止めた理由は会計正本整理に伴う一括停止整合であり、再開を妨げる積極的なブロック理由は無かった。実施: ①退避plist（`~/.claude/archived-launchagents/...archived-20260627`・元は残存）を `~/Library/LaunchAgents/` へcp復帰 ②実行時刻を10:30→**10:45**へ変更しmonthly-accounting(10:30)と非衝突化 ③`launchctl enable`＋`bootstrap`でロード（print-disabled=enabled / list登録 確認）④`watchtower_local.py` の `EXPECTED_JOBS` に追加（28→29本）。書込安全性: monitor本体はfreee `wallet_txns` GETとDiscord通知のみで取引書込なし。検証: plutil -lint OK / py_compile（monitor・watchtower）OK / `check_launchd_jobs()`単体で当該[OK]・台帳外ジョブ警告ゼロ・29項目全OK。次回発火は毎月1日10:45（#お金へ消込待ち集計を督促）
- 〔会計スコープ外・参考〕`~/.claude/redrive/queue/1520246027058282677.json` に 06-27 01:54 のDiscord依頼「タスク見せて」(#一般) が滞留。破棄するか今あらためて回答するかの判断を（会計案件ではないが要確認.md から退避時に同伴したため記録）
