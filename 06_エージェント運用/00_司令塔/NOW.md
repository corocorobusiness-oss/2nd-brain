# NOW

最終更新: 2026-07-15

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

## YMM4動画編集AI社員（進行中）

- 開発方針を訂正。物理Windowsノートは移行可能な状態まで準備し、Level 1〜5の開発は現在のParallels Windowsで完成させる。物理ノート受入は後日実施し、現在の開発を止める条件にしない
- Windows移行bootstrap v1.1.0は7ファイル・161,126 bytesで凍結。manifest SHA-256 `8AA4A02CC25CA1B9BB9602F0332D174907AEF10E2A40EEC72347AEBDBDF71C58`。portable release v1.1.2は165ファイル・2,419,397 bytes、manifest SHA-256 `65BD5E00950C8833DBBEBC9E73F71181C7361F1FC70F6432C838841817D4CEFC`で検証済み
- Windowsノート移行用handoffの正本はSSD `/Volumes/SSD/YouTube/YMM4-AI-HANDOFF-20260714-v1.1.2`（Windows `X:\YouTube\YMM4-AI-HANDOFF-20260714-v1.1.2`）。328ファイル・3,551,386,472 bytes、transport SHA-256 `7346B2D8311490BE9092BF24D9F844D89D95D6225F4B0D4A2B953AA783EAF543`を全件検証済み。SSD検証後に本体の旧・新handoffを削除し約6.58GiBを回収、現行作業案件だけC:へ保持
- 現在PCのYMM4ローカルコピーは4,506ファイル・4,028,195,195 bytes、tree SHA-256 `4807D45CFB5613723746944340FB77BE89A8B3CE0D74E696B28CD690D52DCBE5`で一致し、machine gate PASS。Level 1は未完了
- Level 1のローカルrebaseは205/205参照、106/106素材、内部参照2/2でPASS。出力SHA-256 `C465C3A09BA4F1200C1F49855694FA5080B588D80021B1701CC929C587656F7B`
- 実YMM4辞書はまだWord 612件（有効605）で案件311件と不一致。Word 311・伏字0の候補ファイルはPASSしたが、候補を実辞書へ直接適用した扱いにはしない
- 残りは、呼び出し可能なComputer Use接続 → 伏字有効0 → 単語辞書リセット → 案件DICのみインポート → 実辞書PRE_VOICE → CSV/音声更新 → 別名保存 → 正解表2回一致 → 新規レンダー → golden比較
- 旧teacher由来の正解表は720差分でFAILし、fail-closedが正常に働いた。診断用self-baselineをLevel 2の正解表へ昇格しない
- Computer Useプラグインは有効で、2026-07-15に実行機能設定も有効化した。現在タスクは変更前のツール構成を保持しているためCodex Windowsアプリの再起動・タスク再読込待ち。GUI工程は未実行、YMM4プロセスは未起動。Level 1が完了するまでLevel 2を開始しない
- 人物素材は、じたんだの青系・胸上・透過PNG・横512px（サイト入力の縦0=比率維持、実出力512×641px）・同一デザイン5表情を基準に固定。人物パックmanifest SHA-256は `929CC2BA6A4D2E4CCE58338BF10F9FF112E2F45D63C47BFCA46ACFE97343134A`。有名人物は定番像を優先し、顔だけ/SVG/旧320px版/若年版を自動採用しない

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
