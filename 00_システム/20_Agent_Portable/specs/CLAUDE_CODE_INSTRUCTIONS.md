---
tags: [ストレージ, バックアップ, 手順書, Claude-Code]
updated: 2026-06-24
related: [AI_AGENT_STRUCTURE_AND_BACKUP, IMPLEMENTATION_STATUS]
caution: 証憑・金銭・削除に関わる。実行前に本文の安全原則を必ず読むこと
---

# Claude Code 実行手順（ストレージ構成の整備）

方針は [[AI_AGENT_STRUCTURE_AND_BACKUP]]、進捗は [[IMPLEMENTATION_STATUS]]。
このファイルは **今週の合意済み3変更（手順1〜3）のみ実行可**。手順4は判断待ちで**今は実行しない**。

---

## 0. 前提と安全原則（実行前に必読）

- **消す前に、別媒体にコピー済みであることを必ず確認する。** 削除は「隔離→確認→削除」の3段階。
- **Driveには直接書き込まない。`killall` / 再起動もしない**（EPERMはmacOSのTCCキャッシュが原因。リスナー再起動でのみ回復）。
- **symlinkを実体と間違えて編集・削除しない**（`~/2nd-Brain`・`~/.claude/skills`・`~/.claude/CLAUDE.md`）。
- **エラー・中断・スキップは隠さず正直に報告する。**
- **証憑・金銭に関わる破壊的操作は、実行前に祐馬へ確認する。**
- スクリプト編集は必ず `cp xxx xxx.bak-$(date +%Y%m%d)` でバックアップを取ってから。
- **行番号は変わっている可能性があるので、編集前に必ずファイルを読んで該当箇所を目視確認する。**

対象ファイル（実在パス）:
- `/Users/kojinn/.claude/scripts/vault-snapshot.sh`（週次スナップショット本体）
- `/Users/kojinn/.claude/scripts/run_vault_snapshot.sh`（snapshotのlaunchdラッパ）
- `/Volumes/SSD/_backups/`・`/Volumes/SSD/_アーカイブ_重複_削除可/`・`/Volumes/SSD/01_制作中/`
- `/Users/kojinn/agent-adapters/claude/CLAUDE.md`（入口CLAUDE.mdの実体）

---

## 手順1. 売上証憑を週次スナップショット対象に追加（唯一の穴を塞ぐ）

**やること**
1. `cp /Users/kojinn/.claude/scripts/vault-snapshot.sh{,.bak-20260624}`
2. `vault-snapshot.sh` を読み、`経費精算` が登場する3か所を特定する:
   - manifest対象（`"$DRIVE_ROOT/経費精算"` のあるリスト）
   - tar対象（`"経費精算"` を tar に渡すリスト）
   - 残存（dataless）検査の対象
3. それぞれに **`経費精算` と並べて `売上証憑` を追加**する（経費精算と全く同じ扱いにする）。
4. 手動で1回スナップショットを走らせる: `bash /Users/kojinn/.claude/scripts/run_vault_snapshot.sh`

**検証**
- `tar -tzf "$(ls -1t ~/claude-backups/vault-snapshot-*.tar.gz | head -1)" | grep -E '売上証憑|出前館'` で出前館PDFが含まれることを確認。
- 外付けSSD接続時、`/Volumes/SSD/claude-backups/` に最新tarが乗ったか確認。
- 経費精算が従来どおり含まれることも合わせて確認（デグレ防止）。

**やってはいけないこと**
- Drive側の `売上証憑/` を移動・改名・削除しない（読むだけ）。
- `経費精算` の既存行を消さない（追加のみ）。

---

## 手順2. 外付けSSDのゴミ精査（隔離→確認→削除）

**やること**
1. YMM4移行バックアップの重複確認:
   `diff -rq "/Volumes/SSD/_backups/ymm4_projects_backup_20260619" "/Volumes/SSD/_backups/ymm4_swap_20260619_final" | head -50`
   - 差分がほぼ無ければ**新しい1世代だけ残す**候補。差分があれば中身を祐馬に報告して判断を仰ぐ。
2. 空殻フォルダの確認:
   `ls -la "/Volumes/SSD/_アーカイブ_重複_削除可" "/Volumes/SSD/01_制作中"`
   - `.DS_Store` のみ＝空であることを確認。
3. 隔離: 削除候補を `/Volumes/SSD/_削除待ち/` へ `mv`（いきなり消さない）。
4. 中身が現行プロジェクト・正本と重複でないことを最終確認してから、`_削除待ち/` の中身を削除。

**検証**
- 削除前に `du -sh` で回収予定容量を記録。削除後に `df -h /Volumes/SSD` で空きが増えたか確認。
- 完成動画（`02_完成/`）・制作中ネタ（`YouTube/坂本龍馬…`・`平将門…`）には**一切触れていない**ことを確認。

**やってはいけないこと**
- `02_完成/` `YouTube/` `Coin Quest/` `claude-backups/` は触らない（正本・バックアップ層）。
- 「重複かもしれない」止まりのものを確認前に削除しない。

---

## 手順3. README作成とCLAUDE.md追記

**やること**
1. 各正本フォルダ直下に `README_正本.md` を作成（雛形）:
   ```
   # ここは「{役割}」の正本です
   - 正本はこのフォルダだけ。Drive/GitHub/外付けSSDにあるのは全てコピー。
   - バックアップ: ローカルgit(10分) → GitHub日次 → 週次tar → 外付けSSD
   - 詳細: 00_システム/20_Agent_Portable/specs/AI_AGENT_STRUCTURE_AND_BACKUP.md
   ```
   - `~/2nd-Brain-master`（役割=知識）/ `~/Projects/youtube`（作業・台本）/ `~/agent-skills`（スキル）/ `~/agent-adapters`（AI入口）の4か所。
2. `/Users/kojinn/agent-adapters/claude/CLAUDE.md` の「Vault の場所」付近に正本の見分けルールを1行追記:
   > 正本の見分け方: 実体がローカルにあり `.git` があるフォルダだけが正本。Drive配下と `.gsheet` ポインタは正本でない（例外＝税証憑・gsheet原生のみ）。

**検証**
- `~/agent-adapters` はsatellite-autocommitの対象なので、追記後10分以内にcommitされることを確認。
- READMEが各正本直下に存在することを `ls` で確認。

**やってはいけないこと**
- symlink（`~/.claude/CLAUDE.md`）側ではなく、実体（`agent-adapters/claude/CLAUDE.md`）を編集する。

---

## 手順4. 判断後に着手（今は実行しない）

以下は **オーナーの判断が前提**。判断が出るまで実行しない（[[IMPLEMENTATION_STATUS]] の🟡参照）。

- **動画2台目SSDミラー**（前提=2台目SSD購入の判断）: 2台目SSD接続時に `02_完成/` `YouTube/` を `rsync -a`（**--delete無し＝追加のみ**）でミラー→四半期に1回オフサイト物理搬送。
- **gsheet Takeout**（前提=守る対象シートの選定）: 指定された重要シートのみ `.xlsx/.docx` で書き出し→ `~/2nd-Brain-master/_証憑取込/gsheet-export/YYYY-MM/` に保存→git化。
- **Codex非依存化／agent-run配線**（前提=Codex移行の決定）: 週次snapshotを launchd直＋rsyncでDriveを読むよう改修（claude -p依存を切る）＋各スクリプトの `claude` 呼び出しを `agent-run` 経由に置換。

**いずれも実行前に祐馬へ確認。証憑・税務・お金に関わる変更（電帳法の正本移動等）は税理士確認の申し送りを忘れない。**
