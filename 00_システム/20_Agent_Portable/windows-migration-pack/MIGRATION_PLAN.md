# Windowsノート移行 実行計画

## 完成形

| 対象 | 日常の実行場所 | 正本・受け渡し | 当面のMac mini |
|---|---|---|---|
| Second Brain | Windows内蔵SSDのローカルclone | private Git remote | 復旧コピー、自動化出力 |
| YouTube開発 | Windows内蔵SSDのローカルclone | private Git remote | 24時間処理、復旧 |
| agent-skills / adapters | Windows内蔵SSDのローカルclone | private Git remote | 自動化互換 |
| YMM4編集中案件 | C:\YMM4-Jobs | 案件manifest付きhandoff | 緊急復旧 |
| 動画素材 | 案件内コピー、または固定S:\YMM4-Assets | Mac経由SMB、Windows用SSD | 元SSD保管 |
| 認証情報 | Windowsで再ログイン | パスワード管理 | コピーしない |

移行完了までは、Mac miniローカルの現行正本契約を変更しない。

## Phase 0: 読み取り事前検査

実行:

1. scripts\Test-MigrationPack.ps1
2. scripts\Test-WindowsMigrationPreflight.ps1
3. レポートをC:\Migration-Work\reportsへ保存

検査対象:

- Windows 11
- CPUアーキテクチャ
- RAM、GPU
- 内蔵SSDのファイルシステムと空き容量
- winget、Git、PowerShell、Python、Node、ffmpeg、WSL、robocopy
- OneDrive等の同期フォルダ外へ作業場所を作れるか
- C:\YMM4-Jobsと開発用フォルダの候補

Checkpoint A:

- FAILがあれば変更せず止める
- WARNは理由と回避策を示す
- ユーザーがPhase 1を承認するまで進まない

## Phase 1: Windowsの土台

候補:

- Codex / ChatGPT Windowsアプリ
- Obsidian
- Git for Windows
- PowerShell 7
- Python 3.13.14
- Node.js LTS
- ffmpeg / ffprobe
- 必要なMac系Bash処理だけWSL2

ルール:

- インストール前に公式配布元、版、保存先、管理者権限の要否を示す
- 一括インストールはせず、失敗時に原因が特定できる単位で行う
- WindowsネイティブのYMM4と、WSL内のLinux開発を混同しない
- 秘密情報は搬送せず再ログインする

Checkpoint B:

- 各コマンドの実パスと版を記録
- 再起動が必要なら停止してユーザーへ返す

## Phase 2: ローカル作業場所

最初はscripts\Initialize-WindowsWorkspace.ps1をApplyなしで実行し、作成予定を確認する。承認後だけApply付きで実行する。

標準配置:

- C:\Migration-Work
- %USERPROFILE%\2nd-Brain-master
- %USERPROFILE%\Projects\youtube
- %USERPROFILE%\agent-skills
- %USERPROFILE%\agent-adapters
- C:\YMM4-Jobs
- C:\YMM4-Assets
- C:\Tools\YMM4-AI
- C:\Dev\YMM4-AI

大容量素材用の新しいWindows対応SSDがある場合:

- ドライブ文字をS:へ固定
- S:\YMM4-Assetsを共有素材庫にする
- 編集中のymmpはC:\YMM4-Jobsから開く

Checkpoint C:

- 作業先がOneDrive、Dropbox、SMB、UNC、Mac共有、現在のMac用SSD上でない
- 既存データを上書きしていない

## Phase 3: Git移行

前提:

- Mac側で4リポジトリの作業ツリー、HEAD、origin/mainを確認する
- local HEADとremoteが一致したsource-ready証拠を作る
- remoteのprivate設定を維持する

対象:

1. 2nd-Brain-master
2. Projects/youtube
3. agent-skills
4. agent-adapters

Windowsでは空のローカル先へcloneする。SMBからGit作業ツリーや.gitをコピーしない。

clone後、scripts\Test-PostClone.ps1で次を検査する。

- origin URL
- local HEADとorigin/main
- dirtyファイル0
- 必須ファイル
- 禁止された認証・キャッシュファイルがGit追跡されていない

Checkpoint D:

- 4リポジトリがcleanかつremoteと一致
- YouTubeリポジトリ内の重いgolden素材と仮想環境の扱いを確認
- remote未同期ならWindowsを正本にしない

## Phase 4: Second Brain・Codex・Obsidian

1. Windowsローカルの2nd-Brain-masterをObsidian Vaultとして開く
2. AGENTS.mdと起動時必読ファイルをCodexに読ませる
3. agent-skills正本から必要スキルをCodexへ安全導入する
4. machine-local設定、認証、キャッシュはWindowsで再生成する
5. 1件のテストノートを新規作成し、差分確認後にcommitする

Macのvault-autocommitとWindowsの日常編集が同じmainへ隠れて同時書込みしないよう、正式切替前に運用契約を決める。Mac自動化の変更は別承認とする。

Checkpoint E:

- Obsidianでリンク・添付・設定が開く
- CodexがルールとNOWを読める
- 1件のテストcommitをremoteへ反映し、Mac側から読み取り確認できる

## Phase 5: 動画素材とYMM4

素材の原則:

- Mac用SSDは元データとして残す
- MacがSSDを読み、SMB経由でWindowsへコピーする
- Windows用SSDを使う場合はWindowsへ接続してNTFSへ保存する。既存SSDをフォーマットしない
- active jobはC:\YMM4-Jobsへ独立コピーする
- 共有素材はC:\YMM4-Assetsまたは固定S:\YMM4-Assetsへ置く

既存案件ごとの処理:

1. ymmpの全FilePathと埋め込み参照を読み取り監査
2. 必要素材をmanifest化
3. MacからWindowsへ非破壊コピー
4. コピー先のhashと件数を検証
5. 元ymmpとは別名の新規出力へだけrebase
6. /Volumes/SSD、X:、Y:、N:、\\Mac、旧ユーザーパスの残存0を検査
7. 全素材missing 0を確認
8. QA後にだけYMM4で開く

応仁の乱の既存handoffはv1.1.2を再利用し、同梱HANDOFF.mdとREADME_Windows移行.mdを優先する。古いv1.1.1のhashを現行扱いしない。

Checkpoint F:

- transport manifest PASS
- release bundle PASS
- machine strict gate PASS
- PRE_VOICE PASS
- YMM4で開く、別名保存、再QA、確認MP4、全デコードPASS
- 人間が代表フレーム、字幕、音声を確認

## Phase 6: 開発受入

- 各リポジトリのAGENTS.md、README、lockfileから検証コマンドを特定
- Windowsネイティブ部分とWSL部分を分けてテスト
- Mac固定パスを環境変数またはmachine-local設定へ置換
- agent-runは本番自動化へつなぐ前にdry-run
- 外部投稿、会計書込み、自動ジョブONは禁止

Checkpoint G:

- 主要テストPASS
- 既存Mac成果物との比較
- Windows再起動後も再現できる

## Phase 7: 正式切替

切替条件:

- ACCEPTANCE_CHECKLISTの必須項目が全PASS
- Windowsだけで1日分の動画編集、開発、Second Brain作業を完了
- remoteへ安全に反映できる
- Macまたはバックアップから復旧できる

切替時に初めて、Windowsを唯一の日常編集機とする。Mac miniの24時間自動化は専用branchまたはoutboxへ分離する設計を別作業で実施する。1〜2週間はMacとParallelsを削除・初期化しない。

