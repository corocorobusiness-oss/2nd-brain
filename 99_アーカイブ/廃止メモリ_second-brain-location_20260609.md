<!-- アーカイブ理由: 2026-06-13のローカル正本化により内容が古くなった死にメモ。元は ~/.claude/.../memory/reference_second_brain_location.md。
正しい現行構成は 2nd-Brain-master/CLAUDE.md（ローカル正本＋Drive閲覧専用ミラー）および memory/reference_launchd_drive_traps.md を参照。
2026-06-14 gardener検出→祐馬さん承認のうえ、本アーカイブへ退避後にメモリ本体を削除。 -->

# 【廃止】second-brain-location（2026-06-09時点の旧構成メモ）

> ⚠️ この内容は古い。2026-06-13に2nd-Brainはローカル(`/Users/kojinn/2nd-Brain-master`)を正本化し、Google Driveは15分毎の片方向ミラー（閲覧専用）に変更された。下記の「Drive実体＋symlink」構成はもう使っていない。記録目的でのみ保持。

---

2026-06-09に2nd-BrainをGoogle Driveへ移行（シンボリックリンク方式）。

**構成:**
- 実体: `/Users/kojinn/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/2nd-Brain/`（Google Drive＝どのPCからも同期）
- リンク: `/Users/kojinn/2nd-Brain` → 上記（シンボリックリンク）
- → 既存の全自動化・CLAUDE.md・スクリプトはパス`/Users/kojinn/2nd-Brain`のまま動く（書き換え不要）
- バックアップ: `~/2nd-Brain-backup-20260609`（移行前のローカルコピー）

**メモリはローカル維持:** `~/.claude/projects/-Users-kojinn/memory/`（Driveに入れない＝競合・破損防止）

**⚠️ 注意（Google Drive特有のリスク）:**
- 複数端末で同時編集すると競合コピー（ファイル(1)(2)）が出る恐れ → 同時編集を避ける
- AIの自動書き込み（毎晩の知識昇華・週次整理）とDrive同期が衝突しうる → 異常があれば確認
- 別PCで使う時はそのPCでも同じシンボリックリンク設定が必要（Driveパスは端末で変わる）
- より安全なのはObsidian Sync（提案したが今回はGoogle Drive採用）
