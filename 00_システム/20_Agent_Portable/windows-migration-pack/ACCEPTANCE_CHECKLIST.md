# Windowsノート移行 合格チェックリスト

必須項目がすべてPASSするまで「移行完了」と書かない。

## 1. Windows本体

- [ ] Phase 0 preflightのoverall_statusがPASS
- [ ] Windows 11
- [ ] 内蔵SSD空き50GB以上。100GB以上を推奨
- [ ] 作業場所がNTFSのローカル固定ドライブ
- [ ] 制作中のスリープを回避できる
- [ ] BitLocker回復キーを安全な場所に保管

## 2. 基本ツール

- [ ] Codex / ChatGPT Windowsアプリへ再ログイン
- [ ] Obsidianが起動
- [ ] Git for Windowsが起動
- [ ] PowerShellが起動
- [ ] Python、Node、ffmpegの必要版を確認
- [ ] 必要な場合だけWSL2を導入

## 3. Gitとデータ

- [ ] Mac側で4リポジトリのlocal HEADとorigin/main一致を証明
- [ ] 2nd-Brain-masterをclone
- [ ] Projects/youtubeをclone
- [ ] agent-skillsをclone
- [ ] agent-adaptersをclone
- [ ] 4つともclean
- [ ] 4つともWindows local HEADとorigin/main一致
- [ ] secrets、Cookie、sqlite、生ログ、キャッシュを搬送していない

## 4. Second Brain

- [ ] ObsidianでWindowsローカルVaultを開く
- [ ] AGENTS.mdと必読ファイルが読める
- [ ] 添付・内部リンク・テンプレートを確認
- [ ] テストノートを作成、commit、push、別端末から確認
- [ ] Mac自動化との同時main書込みを防ぐ運用を確定

## 5. 開発

- [ ] YouTube開発の主要テストPASS
- [ ] agent-skillsの検証PASS
- [ ] agent-adaptersのdry-run PASS
- [ ] /Users/kojinn、/Volumes/SSD、\\Mac、X:、Y:、N:の固定依存を棚卸し
- [ ] WindowsネイティブとWSLの保存先を混同していない
- [ ] Windows再起動後にも同じ手順を再実行できる

## 6. 動画素材

- [ ] 元のMac用SSDを変更・フォーマットしていない
- [ ] 使用案件の素材manifestを作成
- [ ] Windowsローカルまたは固定S:へ独立コピー
- [ ] コピー元とコピー先のhash・件数が一致
- [ ] 元ymmpを上書きしていない
- [ ] 新規rebase出力に旧パス残存0
- [ ] ymmpの全素材参照missing 0
- [ ] SSDまたはネットワークを外した状態で、案件の必要素材がローカルから解決できる

## 7. YMM4

- [ ] 現行handoff v1.1.2のtransport manifest PASS
- [ ] portable release v1.1.2のbundle manifest PASS
- [ ] YMM4 4.53.0.9
- [ ] Python 3.13.14と固定依存
- [ ] machine strict gate PASS
- [ ] PRE_VOICE 311件完全一致、伏字有効0
- [ ] 応仁の乱 482 items / 34605 frames
- [ ] FilePath 205 / unique 106 / missing 0
- [ ] YMM4で開ける
- [ ] 元と別名で保存できる
- [ ] 保存後strict QA PASS
- [ ] 1920x1080、30fpsで確認MP4作成
- [ ] ffmpeg全デコード exit 0
- [ ] 先頭・中間・18:25・末尾を人間確認
- [ ] 公開・アップロードをしていない

詳細判定は既存の次のファイルを正本とする。

- 00_システム/20_Agent_Portable/specs/ymm4-ai-windows-restore-checklist.md
- SSD handoff/handoff/HANDOFF.md
- SSD handoff/release/YMM4-AI-portable-v1.1.2/README_Windows移行.md

## 8. 切替と復旧

- [ ] Windowsだけで1日分の実作業を完了
- [ ] Mac側へ戻す復旧試験PASS
- [ ] Windows故障時に4リポジトリを再cloneできる
- [ ] YMM4案件をmanifestから再復元できる
- [ ] MacとParallelsを1〜2週間保持
- [ ] 人間がWindowsメイン昇格を承認

