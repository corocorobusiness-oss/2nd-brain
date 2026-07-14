# YMM4動画編集AI社員 Windows復元チェックリスト

更新: 2026-07-14

## 0. 判定ルール

- すべての必須項目がPASSするまで移行完了と書かない
- Parallels内のPASSだけで物理WindowsノートPCの項目へチェックを付けない
- 元のWindows、SSD、正本ファイルを上書き・削除しない
- 失敗時は新しいレポートへ残し、同名出力を再利用しない

## 1. クリーン環境

- [ ] 別のWindowsユーザー名で実施
- [ ] X: / Y: / N: を接続していない
- [ ] `\\Mac` を接続していない
- [ ] 表示倍率100%
- [ ] 制作中はスリープしない
- [ ] YMM4を管理者権限で起動しない

## 2. バンドル検証

- [ ] `bundle-manifest.sha256` 全件一致
- [ ] 認証情報、Cookie、sqlite、APIキー0件
- [ ] `user/log`、`user/backup`、temp0件
- [ ] YMM4本体とフォントは正規の別経路から用意
- [ ] `environment.lock.json` の完全ハッシュと一致

## 3. パス設定

- [ ] `YMM4_AI_HOME`
- [ ] `YMM4_JOB_ROOT`
- [ ] `YMM4_EXE`
- [ ] `YMM4_FFMPEG`
- [ ] `YMM4_FFPROBE`
- [ ] `YMM4_G2P_PYTHON`
- [ ] `YMM4_ASSET_LIBRARY`
- [ ] 実行設定に `C:\Users\kojinn`、X/Y/N、`\\Mac` がない

## 4. 実装テスト

- [ ] `ymm4-project-builder` 全テストPASS
- [ ] `ymm4-builder` 全テストPASS
- [ ] `ymm4-dic-generator` 全テストPASS
- [ ] asset-pipelineのスモークテストPASS
- [ ] インストーラーを2回実行して二重配置0

## 4A. Windowsノート開発環境

- [ ] 実行版を`C:\Tools\YMM4-AI\versions\1.1.1`へ導入し、直接編集しない
- [ ] 開発用を`C:\Dev\YMM4-AI\1.1.2-dev`へ物理コピー
- [ ] 開発用で新しいGit baseline commitを作成
- [ ] 開発開始前の全テスト、security scan、manifest verifyがPASS
- [ ] production Pythonは固定絶対パス + `-B`
- [ ] テスト後の`__pycache__` / `.pyc` 0件
- [ ] 開発リポジトリ内の秘密情報、`machine.local.json`、YMM4 user設定0件
- [ ] 変更は新versionとして凍結し、installer経由で実行版へ導入
- [ ] Git commit/tagまたは新bundleをMac側正本へ一方向に返却し、同時編集しない

## 5. ゴールデン案件取込

- [ ] ゴールデンパックmanifest一致
- [ ] ローカル案件ルートへ独立コピー
- [ ] `.ymmp` を新しい素材ルートへrebase
- [ ] 482アイテム
- [ ] Voice 187 / Image 148 / Shape 74 / Video 54 / Text 16 / Audio 3
- [ ] FilePath 205 / unique 106 / missing 0
- [ ] 正解入力SHA一致
- [ ] Frame / Length / Layer / Group差分0
- [ ] 非音声295件差分0

## 6. 辞書と音声

- [ ] 単語辞書を全消去
- [ ] 案件DICだけを単語辞書へインポート
- [ ] 有効な伏字0件
- [ ] Word=DIC 311件完全一致
- [ ] `他の→ほかの`
- [ ] PRE_VOICE runtime gate PASS
- [ ] CSVはruntime gate後に読み込み
- [ ] VoiceCache 187/187
- [ ] VoiceLength 187/187正値
- [ ] YMM4丸め式187/187
- [ ] 音声重なり0

## 7. YMM4実機

- [ ] YMM4 4.53.0.9で開く
- [ ] 物理WindowsノートPCで実施した証拠を残す
- [ ] 読込エラー0
- [ ] 保存後に再QA PASS
- [ ] 保存後の正解表を2回抽出しbyte一致。旧teacher正解表と診断用self-baselineは使用しない
- [ ] 18:25地点が正解見本と一致
- [ ] 素材名に不要なハッシュ接尾辞が表示されない
- [ ] 字幕は漢字表示、読みはHatsuon/単語辞書どおり

## 8. レンダー

- [ ] 1920×1080
- [ ] 30fps
- [ ] 映像・音声ストリームあり
- [ ] ffmpeg全デコード exit 0
- [ ] 先頭フレーム確認
- [ ] 中間フレーム確認
- [ ] 18:25フレーム確認
- [ ] 末尾フレーム確認
- [ ] 黒画面、音声欠落、字幕切れ0

## 9. Fail-closed試験

- [ ] 素材1件をコピー上で破損するとmanifestがFAIL
- [ ] 素材1件をコピー上で欠落させるとQAがFAIL
- [ ] 有効な伏字を1件入れるとPRE_VOICEがFAIL
- [ ] 入力SHAを変えるとexact-slot fitterがFAIL
- [ ] 既存出力名を指定すると上書きせずFAIL

## 10. 引き渡し

- [ ] 完成 `.ymmp`、MP4、QA、manifestをSSDへ戻す
- [ ] Second Brainの作業ログを更新
- [ ] 公開ゲートは別判定
- [ ] AquesTalk商用条件確認
- [ ] 素材106件の権利・クレジット確認
- [ ] 人間の最終視聴承認
