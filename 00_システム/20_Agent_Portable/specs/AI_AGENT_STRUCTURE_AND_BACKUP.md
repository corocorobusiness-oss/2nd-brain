---
tags: [ストレージ, バックアップ, 設計, エージェント運用]
updated: 2026-06-24
status: 方針確定（実装は IMPLEMENTATION_STATUS.md を参照）
related: [IMPLEMENTATION_STATUS, CLAUDE_CODE_INSTRUCTIONS, agent-neutral-contract]
---

# AI中心ストレージ構成とバックアップ方針

3拠点（ローカルMac / 外付けSSD / Drive+GitHub）に散ったフォルダを、AIエージェント中心・シンプル・3-2-1バックアップで運用するための **方針と全体像** をまとめた正典。実行手順は [[CLAUDE_CODE_INSTRUCTIONS]]、進捗は [[IMPLEMENTATION_STATUS]] を参照。

---

## 1. 全体の憲法（これだけ覚えればAIも人も迷わない）

> **正本は常にローカル。** テキスト・コードは Mac内蔵、巨大メディア（動画）は外付けSSD。
> **Drive と GitHub はコピー専用**で、絶対に直接書き込まない。
> **AI（Claude / 将来Codex）は必ずローカルの正本を編集する。**

迷ったら「これはどのローカルフォルダの正本か？／コピーは2媒体＋オフサイトに渡るか？」だけ確認する。

**例外は2つだけ**（明示的に名指しして一貫性を保つ）:
1. 税の証憑（経費精算）— 電子帳簿保存法の事務処理規程上、当面 Drive が正本。
2. Googleネイティブ書類（`.gsheet` / `.gdoc`）— 実体がGoogleクラウド上にあるため Drive が正本。

---

## 2. 3拠点の役割

### ローカルMac（内蔵256GB・空き約84GB）
gitで守れる軽量正本の唯一の置き場＝AIの作業面。巨大メディアは絶対に置かない。
AIランタイム（`~/.claude` / `~/.codex`）と Windows VM（Parallels 33G）は**正本ではない**ので非バックアップ。

### 外付けSSD（931GB・空き447GB）
256GBに収まらない大容量メディア正本の唯一の置き場＋週次スナップショットの受け皿。
Windowsの編集機からは `map-ssd-N.bat` でSMB閲覧参照（編集はMac側）。

### Drive ＋ GitHub（オフサイト2経路）
複製専用。火事・盗難・ディスク全損に耐えるための層。**Driveには片方向ミラーでのみ書き込み、人もAIも直接編集しない**。

---

## 3. 各保存先のフォルダ構成案

### ローカルMac `~/`（現状維持＝触らない）
```
~/2nd-Brain-master/     # 知識の正本（Obsidian Vault本体・git）
~/Projects/youtube/     # YouTube制作の作業場・台本テキスト正本（git）
~/agent-skills/         # スキルの正本（git）
~/agent-adapters/       # AI入口の正本・bin/agent-run継ぎ目（git）
~/2nd-Brain            → 2nd-Brain-master へのsymlink（AIの入口）
~/.claude/skills       → agent-skills へのsymlink
~/.claude/CLAUDE.md    → agent-adapters/claude/CLAUDE.md へのsymlink
~/.claude  ~/.codex     # AIランタイム（キャッシュ・非バックアップ）
~/Parallels             # Windows VM（作業環境・非バックアップ）
```
symlink入口は「AIが正本に一意に辿り着く」ための要。**実体と間違えて編集・削除しない。**

### 外付けSSD `/Volumes/SSD/`（役割別の箱に整理）
```
02_完成/                # 完成動画227本＋プロジェクト（正本・395G）
YouTube/                # 編集素材・YMM4本体（正本・13G）
SSD：アプリケーション/   # 容量逃がしアプリ（Photoshop等）
Coin Quest/             # Roblox制作物（正本）
claude-backups/         # 週次スナップショットのSSDミラー（バックアップ層）
_削除待ち/              # 整理用の一時箱（月1で空にする）
map-ssd-N.bat           # Windows用SMBマウント（残す）
```
**整理対象**: `_backups`（8.4G・YMM4移行スナップショットの重複疑い）と空殻フォルダ（`_アーカイブ_重複_削除可`・`01_制作中`）は精査して削除。今後 `_old` / `_backups` のような曖昧な箱は新設しない。

### Drive（マイドライブ直下・コピー専用）
```
2nd-Brain/              # 知識の15分片方向ミラー（閲覧専用・書込禁止）
経費精算/               # 税の証憑（例外①・当面Drive正本）
売上証憑/               # 出前館PDF（穴→週次バックアップに接続予定）
_業務シート/ 外注ライター/ YouTube_2ch世界史/   # .gsheet/.gdoc（例外②・Google正本）
_削除待ち/              # 月1で空にする（常設ゴミ箱化を防ぐ）
```

---

## 4. データ別 正本→コピー→3-2-1

| データ種別 | 正本の場所 | コピー経路 | 3-2-1 |
|---|---|---|---|
| 知識（2nd-Brain 20M） | Mac `~/2nd-Brain-master` | git10分→GitHub日次→週次tar→SSD ＋Drive15分閲覧ミラー | ◎ 達成 |
| 作業・台本（5.8M） | Mac `~/Projects/youtube` | git10分→GitHub日次→週次tar→SSD | ◎ 達成 |
| スキル（2.2M） | Mac `~/agent-skills` | git10分→GitHub日次→週次tar→SSD | ◎ 達成 |
| AI入口（244K） | Mac `~/agent-adapters` | git10分→GitHub日次→週次tar→SSD | ◎ 達成 |
| AIランタイム（.claude/.codex） | Mac（キャッシュ） | バックアップしない（再生成可能） | 対象外でOK |
| 動画メディア（02_完成 395G ほか） | 外付けSSD | **現状SSD単独** → §6で二重化 | ✗ 要判断 |
| 税証憑（経費精算 16M） | Drive 経費精算/ | Drive＋Mac内tar＋SSD内tar（6/16復元PASS 729件） | ◎ 達成 |
| 売上証憑（出前館PDF 32K） | Drive 売上証憑/ | **現状Drive単独＝唯一の本当の穴** → §6で即解消 | ✗ → 即◎ |
| クラウド表計算（.gsheet 542点） | Google | 実体コピー無し（ローカルは223Bポインタ） | ✗ 要判断 |
| Windows VM（Parallels 33G） | Mac内蔵 | 再構築可・非バックアップ | 対象外でOK |

---

## 5. バックアップ連鎖（実装済み）

```
ローカルgit（10分毎 auto-commit）
   → GitHub private（org=corocorobusiness-oss・日次push）
   → Driveミラー（15分・片方向・閲覧専用）
   → 週次スナップショット（日曜4:30・tar→~/claude-backups）
   → 外付けSSD（マウント時 ssd-backup）
```
- 軽量4正本は実質4コピー（ローカル＋GitHub＋SSD tar＋Drive閲覧ミラー）で **3-2-1達成済み**。
- ⚠️ 週次スナップショットは Drive を `claude -p` 経由で読む（macOSのTCC制約）＝**Claude常駐に依存**。これがエージェント非依存化の最後の宿題（§6）。

---

## 6. 既知の穴と方針

| 穴 | 現状 | 方針（推奨） |
|---|---|---|
| 売上証憑（出前館PDF） | Drive単独・どのバックアップにも無い | **週次スナップショットの対象に1行追加**。最小手数で唯一の穴が消える（今週・低リスク） |
| 動画メディア 395G | 外付けSSD 1台のみ | **2台目SSDへ週次ミラーで媒体2を即充足＋四半期に物理搬送でオフサイト1**。完成動画は更新頻度が低くこれで十分・最安 |
| .gsheet/.gdoc 542点 | Googleアカウント単独依存 | **業務クリティカルな数点だけ**月次/四半期 Google Takeout で `.xlsx/.docx` 化→ `~/2nd-Brain-master/_証憑取込/gsheet-export/` に落としgit化。全件は過剰 |
| 週次snapshotのClaude依存 | `claude -p` 経由でDrive読み | Codex移行を決めた時に launchd直＋rsync化＋スクリプトを `agent-run` 経由へ（当面は後回し） |

---

## 7. 運用ルール（憲法を守るための日々の約束）

1. **正本はローカル・Driveは閲覧専用ミラー**。Driveに直接書き込まない。Drive不調（EPERM）時も `killall` / 再起動はしない（TCCキャッシュが原因、リスナー再起動でのみ回復）。
2. **新規フォルダの命名は「役割が一語でわかる」を唯一の規約**。深い階層・略語・曖昧な箱（`_old` 等）を新設しない。
3. **`_削除待ち` は月1で空にする**（常設ゴミ箱化を防ぐ）。
4. **消す前に、別媒体にコピー済みであることを必ず確認**（可逆性の担保）。
5. **symlink入口（`~/2nd-Brain`・`~/.claude/skills`・`~/.claude/CLAUDE.md`）は実体と間違えて編集・削除しない。**
6. 各正本フォルダ直下に `README_正本.md`（ここは何の正本か／正本はここだけ／コピーはどこ）を置く。
