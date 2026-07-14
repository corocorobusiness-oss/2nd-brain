# Windowsノート移行パック

状態: `PREPARED_NOT_EXECUTED`  
作成日: 2026-07-15

このフォルダは、Mac mini + Parallelsで行っている日常作業を、物理Windowsノートへ安全に再構築するための入口です。

移行する日常作業:

- YMM4動画編集
- Second Brain / Obsidian
- Codexを使った作業
- YouTube開発環境
- `agent-skills` と `agent-adapters`

当面Mac miniへ残すもの:

- 24時間稼働のlaunchd自動化
- 復旧用コピー
- Windows移行が合格するまでの現行正本

## 最初にやること

1. このフォルダ全体をWindowsノートの `C:\Migration-Work\windows-migration-pack` へコピーする。
2. ネットワーク共有やSSD上では実行せず、必ずWindows内蔵ストレージ上で使う。
3. Windows版Codexでコピー先フォルダを開く。
4. `WINDOWS_CODEX_START_PROMPT.md` の本文を新しいタスクへ貼る。
5. CodexがPhase 0の検査結果を出したところで、一度止めて確認する。

Windows版Codexをまだ入れていない場合は、OpenAI公式のWindowsアプリをインストールしてChatGPTアカウントでログインする。認証ファイルやセッションをMacからコピーしない。

## ファイル案内

- `WINDOWS_CODEX_START_PROMPT.md`: Windows側Codexへ最初に渡す指示
- `MIGRATION_PLAN.md`: 全体の実行順と停止点
- `ACCEPTANCE_CHECKLIST.md`: Windowsをメイン機へ昇格する条件
- `SOURCE_INVENTORY.json`: 現在分かっている移行元と固定値
- `TARGET_CONFIG.example.json`: Windowsの保存先例。直接書き換えず、PC外のローカル作業フォルダへコピーして使う
- `SMB_COPY_GUIDE.md`: SSDをMac経由でWindowsへ渡す方法
- `scripts/`: 非破壊の検査・初期化・コピー補助
- `pack.manifest.sha256`: このパック自身の改変・欠落検査

## 絶対にしないこと

- SSD、内蔵ディスク、既存ボリュームを初期化・フォーマットしない
- 元ファイル、元`.ymmp`、素材、Git履歴を削除・上書きしない
- `git push --force`、`git reset --hard`、`robocopy /MIR`を使わない
- `.codex`、`.claude`、Cookie、トークン、sqlite、ブラウザプロファイルを搬送しない
- Mac miniの自動化を停止・変更しない
- 共有フォルダ、SSD、UNCパス上の`.ymmp`をYMM4で直接開かない
- 合格チェック前にWindowsを正本へ切り替えない

## 現在の停止条件

- 4つのGitリポジトリについて、MacローカルとGitHub remoteの完全一致をまだ最終確認していない
- YMM4 Level 1は現在のParallelsでGUI往復・新規レンダーが未完了
- 物理WindowsノートのCPU、RAM、GPU、空き容量、アーキテクチャを未検査
- MacのSSD共有名とWindowsからの接続先を未確定

これらは失敗ではなく、Windows側Codexが勝手に先へ進まないための正常な停止条件です。
