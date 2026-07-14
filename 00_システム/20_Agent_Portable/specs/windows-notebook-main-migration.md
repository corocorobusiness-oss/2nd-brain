# Windowsノート メイン機移行

更新: 2026-07-15
状態: 移行実行パック作成・自己検証PASS。物理Windowsノートでの実行は未開始。

## 目的

Mac mini + Parallelsで行っている次の日常作業を、物理Windowsノートで再現する。

- YMM4動画編集
- Second Brain / Obsidian
- Codex
- YouTube開発
- agent-skills
- agent-adapters

Mac miniの24時間自動化は初期移行の対象外とし、当面は自動化・復旧機として残す。

## 実行パック

00_システム/20_Agent_Portable/windows-migration-pack/

入口:

- README_FIRST.md
- WINDOWS_CODEX_START_PROMPT.md
- MIGRATION_PLAN.md
- ACCEPTANCE_CHECKLIST.md

パック自身はpack.manifest.sha256とscripts/Test-MigrationPack.ps1で検証する。2026-07-15時点で15 payload files、欠落・余分・SHA差分0を確認済み。

## 動画素材

現在のMac用SSDを初期化しない。Mac miniがSSDを読み、SMB経由でWindowsローカルまたは新しいWindows用SSDへ独立コピーする。

- 編集中案件: C:\YMM4-Jobs
- 小規模素材: C:\YMM4-Assets
- 大規模素材: 固定S:\YMM4-Assets

元ymmpを上書きせず、新規出力へだけ旧パスをrebaseする。旧パス残存0、全素材missing 0、hash一致を確認してからYMM4で開く。

応仁の乱以外の既存案件は、windows-migration-pack/LEGACY_YMM4_ASSET_MIGRATION.mdに従い案件単位で移行する。

## 現行YMM4 handoff

- SSD正本: /Volumes/SSD/YouTube/YMM4-AI-HANDOFF-20260714-v1.1.2
- payload: 328 files / 3,551,386,472 bytes
- transport SHA-256: 7346B2D8311490BE9092BF24D9F844D89D95D6225F4B0D4A2B953AA783EAF543
- portable release: v1.1.2
- release manifest SHA-256: 65BD5E00950C8833DBBEBC9E73F71181C7361F1FC70F6432C838841817D4CEFC
- bootstrap: v1.1.0
- physical Windows acceptance: 未実行

## 停止条件

- 4リポジトリのMac local HEADとorigin/main一致を証明するまでWindows cloneを正本扱いしない
- 現在のParallelsでYMM4 Level 1のGUI往復・新規レンダーを凍結するまで物理Windows受入を完了扱いしない
- Windows preflight、manifest、machine gate、PRE_VOICE、YMM4往復、レンダー、人間確認が揃うまで移行完了と書かない
- Mac自動化停止、ディスク初期化、削除、force push、公開は別の明示承認を必要とする

## 次の実行

1. Windowsノートへ移行パックだけをSMBでコピーする
2. Windows版Codexでフォルダを開く
3. WINDOWS_CODEX_START_PROMPT.mdを貼る
4. Phase 0の読み取り検査で停止し、結果を確認する
