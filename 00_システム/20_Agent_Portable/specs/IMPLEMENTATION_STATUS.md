---
tags: [ストレージ, バックアップ, 進捗, チェックリスト]
updated: 2026-06-24
related: [AI_AGENT_STRUCTURE_AND_BACKUP, CLAUDE_CODE_INSTRUCTIONS]
---

# ストレージ構成・バックアップ 実装状況

方針は [[AI_AGENT_STRUCTURE_AND_BACKUP]]、実行手順は [[CLAUDE_CODE_INSTRUCTIONS]]。
このファイルは「何が完了済みで、何が未完了か」のチェックリスト。

---

## ✅ 完了済み（現状で達成できていること）

- [x] **4正本のローカルgit＋GitHub日次push** — `~/2nd-Brain-master` `~/Projects/youtube` `~/agent-skills` `~/agent-adapters`（org=corocorobusiness-oss・全Private）
- [x] **知識Vaultの Drive 15分ミラー**（片方向・閲覧専用・md5一致を実機確認）
- [x] **週次スナップショット→外付けSSD**（日曜4:30・tar→`~/claude-backups`→SSD）
- [x] **税証憑（経費精算）の実3コピー** — Drive＋Mac内tar＋SSD内tar。**復元テスト 2026-06-16 にPASS（729件 sha256照合）**
- [x] **大容量メディアを外付けSSDへ退避済み** — 動画395G・素材13G・アプリ10G。256GB内蔵を圧迫していない
- [x] **agent-run 継ぎ目の存在** — `~/agent-adapters/bin/agent-run`（Claude↔Codex切替の唯一の差し替え点）

---

## 🔧 未完了・要対応（低リスク・今週着手OK）

- [ ] **売上証憑（出前館PDF）をバックアップ連鎖に接続** — 現状 Drive単独＝唯一の本当の穴。週次スナップショット対象に `売上証憑/` を1行追加で解消（手順1）
- [ ] **外付けSSDのゴミ精査** — `_backups`（8.4G・YMM4移行スナップショットの重複疑い）＋空殻フォルダ（`_アーカイブ_重複_削除可`・`01_制作中`）を精査→隔離→確認後に削除（手順2）
- [ ] **各正本に `README_正本.md`** — 「ここは何の正本か／正本はここだけ／コピーはどこ」を明記（手順3）
- [ ] **CLAUDE.md に正本の見分けルール1行追記** — 「実体がローカルにあり.gitがあるフォルダだけが正本。Drive配下と.gsheetポインタは正本でない＝税証憑・gsheet原生のみ例外」（手順3）
- [ ] **YouTube制作物の整理（1ネタ＝1か所で見えるように）** — 台本(Mac・複数フォルダに散在)と素材(SSD)が分離。改名はしない（.ymmpが壊れる）。①Mac側に素材へのsymlink玄関 ②`.codex`/`Downloads` 参照素材をネタフォルダへ集約しYMM4プロジェクトを自己完結化 ③今後はpipelineが生成画像をネタフォルダ直保存。詳細は [[AI_AGENT_STRUCTURE_AND_BACKUP]] §6

---

## 🟡 オーナー判断待ち（[No preference]＝下記の推奨をデフォルト採用）

- [ ] **動画395Gのオフサイト化** — 推奨：**2台目SSD（約1万円）へ週次ミラー＋四半期に物理搬送**。完成動画は更新頻度が低くこれで十分・最安。未実施（購入判断待ち）
- [ ] **Codex非依存化（週次snapshotのClaude依存切り）** — 推奨：**後回し**。当面Claude常駐前提。Codex移行を決めた時に launchd直＋rsync化＋スクリプトを `agent-run` 経由へ
- [ ] **.gsheet 542点のどれを守るか** — 推奨：**業務クリティカルな数点だけ** Google Takeout で実体化。全件は過剰。対象選定は祐馬
- [ ] **電帳法の税証憑正本＝Drive固定の扱い** — 推奨：**当面Drive正本のまま例外運用**（規程改定＋税務確認は急がない。既に実3コピーで復元PASS済み）

---

## ⛔ 既知の制約・残存リスク

- **週次スナップショットのClaude依存** — Drive を `claude -p` 経由で読む（macOSのTCC制約）。Claudeが落ちているとDrive層（経費精算・売上証憑）のバックアップが止まる。→ Codex非依存化で解消（判断待ち）
- **agent-run が未配線（建前と実体の乖離・2026-06-28 明記）** — 継ぎ目（`~/agent-adapters/bin/agent-run`）は存在するが、**agent-run 経由は一部のみ**（`run_vault_snapshot.sh` / `run_thread_format_learning.sh` / `vault-snapshot.sh` の3本程度）で、`run_weekly_accounting.sh` `run_monthly_accounting.sh` `run_daily_dashboard.sh` `run_knowledge_gardener.sh` `listener-watchdog.sh` など多数（約15〜44本）の launchd/cron スクリプトは `claude -p` を直叩きしている。さらに **agent-run の codex 分岐は未実装（`exit 64`）のため、Codex 切替は現時点では実行不可**。方針: **新規スクリプトは agent-run 経由を必須、既存は順次移行**。money系の置換後は確認ゲート（実装者≠確認者）を維持すること
- **動画メディアがSSD単独** — 物理故障で完成動画＋編集プロジェクトを失うリスク（判断待ち）
- **.gsheet/.gdoc がGoogleアカウント単独依存** — 凍結・誤削除に弱い（判断待ち）
- **⚠️ YMM4プロジェクトが掃除対象フォルダを参照** — `.ymmp` が素材を絶対パスで参照し、一部が `~/.codex/generated_images` `~/Downloads`（＝「掃除していいキャッシュ」と分類した場所）を指す。実例 `平将門の祟り.ymmp` は66素材中5個が該当。**`.codex`/`Downloads` を掃除すると再編集時に映像が壊れる**ため、掃除前チェックが必須（[[CLAUDE_CODE_INSTRUCTIONS]] の「掃除の鉄則」）

---

## 優先順位

1. **今週（低リスク・コスト0）**: 手順1（売上証憑）→ 手順2（SSDゴミ）→ 手順3（README＋ルール）
2. **中期（小コスト）**: 動画の2台目SSDミラー（媒体2の充足）／gsheet重要数点のTakeout
3. **大物（要判断・要工事）**: 動画オフサイト物理搬送の運用化／Codex非依存化（agent-run配線）／電帳法の正本移動
