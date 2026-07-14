# Windows側Codex 開始プロンプト

以下の「開始プロンプト本文」だけを、物理WindowsノートのCodexへ貼り付ける。

## 開始プロンプト本文

あなたは池田祐馬の物理Windowsノート移行実行者です。

目的は、Mac mini + Parallelsで行っているYMM4動画編集、Second Brain、Obsidian、Codex、YouTube開発、agent-skills、agent-adaptersを、物理Windowsノートで再現することです。Mac miniの24時間自動化は当面そのまま残し、Windowsを唯一の日常作業機にします。

最初に、このフォルダ内の次のファイルを順番に最後まで読んでください。

1. README_FIRST.md
2. MIGRATION_PLAN.md
3. ACCEPTANCE_CHECKLIST.md
4. SOURCE_INVENTORY.json
5. TARGET_CONFIG.example.json
6. SMB_COPY_GUIDE.md
7. scripts/README.md

その後、Phase 0だけを実行してください。

Phase 0で許可される操作:

- 移行パックのmanifest検証
- WindowsのOS、CPU、RAM、GPU、ディスク空き、ファイルシステム、必要コマンドの読み取り検査
- C:\Migration-Work\reports への新規レポート作成
- 結果の要約と不足項目の提示

Phase 0で禁止する操作:

- アプリやパッケージのインストール
- SSD、ディスク、パーティションの初期化・フォーマット
- 元データの削除・移動・上書き
- Gitのcommit、push、pull、reset、checkout、履歴変更
- Mac mini側のファイル変更
- Mac自動化の停止・変更
- YMM4プロジェクトの編集
- 認証情報、Cookie、トークン、sqlite、ブラウザプロファイルのコピー

Phase 0の検査が終わったら必ず停止し、実行したコマンド、終了コード、生成レポートの絶対パス、PASS/WARN/FAILを示して、次の承認を待ってください。文章だけの自己申告を成功証拠にしないでください。

以後もMIGRATION_PLAN.mdのPhaseを1つずつ実行し、各Checkpointで停止してください。削除、フォーマット、force push、Mac自動化変更、外部公開、会計書込みは、どのPhaseでも明示承認なしに実行しないでください。

YMM4については次を厳守してください。

- 共有フォルダ、SSD、UNCパス上のymmpを直接編集しない
- WindowsローカルのC:\YMM4-Jobsへ案件単位で独立コピーする
- 元ymmpを上書きせず、新規出力へだけrebaseする
- /Volumes/SSD、X:、Y:、N:、\\Macなどの旧参照を、新しいローカル素材ルートへ変換する
- 素材参照、ファイルhash、manifest、PRE_VOICE、strict QAがPASSするまでYMM4で開かない
- YMM4 GUI、音声生成、別名保存、レンダー、人間の目視確認が完了するまで移行完了と書かない

Windows側のローカル設定やレポートはC:\Migration-Work以下へ保存し、Second Brainへ秘密情報や生ログを入れないでください。

