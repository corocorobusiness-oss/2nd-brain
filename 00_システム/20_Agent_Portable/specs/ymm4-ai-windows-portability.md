# YMM4動画編集AI社員 Windows移行仕様

更新: 2026-07-14  
状態: 移行bootstrap/handoffと現在のParallels開発環境は検証済み。Level 1の実YMM4往復・新規レンダーと物理WindowsノートPC受入は未完了であり、「Level 1完了」「別PC移行完了」とは扱わない。

## 目的

YMM4動画編集AI社員を、現在のParallels Windowsだけでなく、別のWindows PCでも同じ手順・辞書・素材・QAで再現する。

移行対象は「コード・設定例・ハッシュ・復元手順」と「重いゴールデン案件」を分離する。

- コード側: Git管理できる小型の `YMM4-AI-portable` バンドル
- 媒体側: SSD上のハッシュ付き `golden-001-onin` パック
- Second Brain: 仕様、チェックリスト、判断ログだけ。動画・素材・認証情報は置かない

## 2026-07-14 portable v1.1.1 事前受入証拠

- bundle manifest SHA-256: `E6BBE92D7C53AD9F6A18E79F2249ABD582536319FD025ACBC4526E31B7AF00F8`
- manifest payload: 121 files / 1,673,779 bytes。manifest自身を含む物理ファイルは122件
- fresh installでsourceとinstalledの欠落・余分・SHA差分0
- machine gate: PASS、failed 0、Python実行ファイルhashの情報WARN 1のみ
- PRE_VOICE: PASS。DIC 311件、SHA-256 `C705F55C1DD44DEE9A7BDBA58B8249DA7D5CDD9115BB75686375500C4965D31A`、Word完全一致、伏字有効0
- clean YMMP: 482 items / 34,605 frames / 205 refs / 106 unique / missing 0
- 診断用self-baseline strict QA: PASS、path maps 0、入力不変
- 独立peer監査: ACCEPT、P0/P1/P2すべて0
- Windowsノート搬送handoffのローカルmanifest: 265 payload / 3,519,083,195 bytes、SHA-256 `E5A5EEBA2BC50D4019D2499BC0A1353F95C2AD307DC2FB787BF9576F94531FFE`、verify PASS
- Windowsノートbootstrap v1.0.0: 7 files / 159,934 bytes。manifest SHA-256 `CF93D9D6C4F14F2B41FAFDC05572EB6B43405495D57697478A0D9A6FB89DFC1E`、検証スクリプトSHA-256 `A16401DBCF69CEA261B8700E63213970A4016DAF4966C598001EBC929015AFBC`
- 現在PCのYMM4ローカルコピー: 4,506 files / 4,028,195,195 bytes、tree SHA-256 `4807D45CFB5613723746944340FB77BE89A8B3CE0D74E696B28CD690D52DCBE5`、machine gate PASS

旧`reference_timeline_clean_local.json`はteacher由来であり、clean YMMPとの比較は720 errorsでFAILした。これは古い正解表を誤って合格させないfail-closedの正常動作である。self-baseline PASSはLevel 1完了の証明ではない。Level 1の最終正解表は、現在のParallelsの実YMM4で開いて別名保存した直後に2回抽出し、byte一致を確認してから固定する。物理Windowsノート受入では、その固定済み正解表を使って別途再現性を確認する。

## 現在PCでの開発／将来のWindowsノート移行契約

- Level 1〜5の開発は現在のParallels Windowsで続け、物理Windowsノート受入を待たない
- 現在PCでも実行版と開発版を分離する。実行版v1.1.1は凍結し、1.1.2-devだけを変更する
- 将来のノートでは実行版を `C:\Tools\YMM4-AI\versions\<version>`、開発版を `C:\Dev\YMM4-AI\<version>-dev` に分離し、凍結bootstrapを直接編集しない
- productionのPythonは固定した絶対`YMM4_G2P_PYTHON`と`-B`で実行する。テスト前後のmanifest一致と`__pycache__` / `.pyc` 0件を必須にする
- `machine.local.json`、認証情報、Cookie、YMM4 user設定、ログ、キャッシュはGit・SSD搬送対象外
- installed runtime内で修正せず、開発版でtest → security scan → manifest → 新version化 → installer経由で導入する
- Mac側・現在PC・将来のノートで同時編集しない。変更はGit commit/tagまたは新bundleでMac側正本へ一方向に戻し、Windows作業コピーを第二の正本にしない

## 正本

- YMM4統括スキル: `~/agent-skills/ymm4-project-builder`
- YouTube実装: `~/Projects/youtube/ymm4-builder`
- 辞書実装: `~/agent-skills/ymm4-dic-generator`
- 素材実装: `~/Projects/youtube/asset-pipeline`
- Windows案件既定: `C:\YMM4-Jobs`
- 重いリリース: `/Volumes/SSD/YouTube/_YMM4_AI_Portable/releases/<release-id>/`

## 移行バンドルの契約

```text
YMM4-AI-portable/
├─ README_Windows移行.md
├─ bundle-manifest.sha256
├─ config/
│  ├─ machine.example.json
│  ├─ environment.lock.json
│  ├─ safe-copy-allowlist.json
│  └─ requirements-win-amd64.lock.txt
├─ skills/
├─ app/
├─ scripts/
└─ licenses/
```

バンドルへ入れてはいけないもの:

- Codex / ChatGPTの認証情報、Cookie、セッション、sqlite
- APIキー、YMM4のAPI設定
- YMM4 `user/log`、`user/backup`、一時ファイル
- 未確認ライセンスのフォント・素材・YMM4本体
- 個人名を含む固定ユーザーパス

YMM4本体とフォントは、利用者が正規に用意したものを検査する。YMM4 `user/` を丸ごとコピーしない。

## 環境変数

固定パスをコードへ埋め込まず、次へ集約する。

- `YMM4_AI_HOME`
- `YMM4_JOB_ROOT`
- `YMM4_EXE`
- `YMM4_FFMPEG`
- `YMM4_FFPROBE`
- `YMM4_G2P_PYTHON`
- `YMM4_ASSET_LIBRARY`

実行対象 `.ymmp` に `C:\Users\kojinn`、`X:`、`Y:`、`N:`、`\\Mac` を残さない。由来を記録するレポート内の旧パスは許容する。

## 現行ロック値

- Windows 11 Pro ARM64 build 26200、表示倍率100%
- Python 3.13.14
- YMM4 4.53.0.9
- YMM4 EXE SHA-256: `C4E32E2D620142115080F7FD2A738C796578760E4A82068B75E1487EAC9595AB`
- ffmpeg: `N-124026-g96f82f4fbb-20260417`
- ffmpeg SHA-256: `FE5A8142...ACE53`
- ffprobe SHA-256: `A9AADA47...C6993`
- Python依存:
  - `pyopenjtalk-plus==0.4.1.post8`
  - `numpy==2.5.1`
  - `SudachiPy==0.6.11`
  - `SudachiDict-core==20260428`
- 使用フォント:
  - ラノベPOP v2 / `LightNovelPOPv2.otf` / SHA `E5B1E8CD...BF51`
  - 游明朝 Demibold / `yumindb.ttf` / SHA `4AAA147E...EFF9`

省略ハッシュは、配布時の `environment.lock.json` では完全な64桁を記録する。

## 案件の復元

編集はWindowsローカルで行う。共有SSD上の `.ymmp` を直接編集しない。

1. ゴールデンパックのmanifestを検証する
2. 選んだローカル案件ルートへ独立コピーする
3. `.ymmp` の素材参照をローカル素材ルートへ安全にrebaseする
4. 参照205件、ユニーク106件、欠落0件を確認する
5. 正解入力SHA、482アイテム、187音声を固定する
6. YMM4で開く前に最終QAを通す

同じ `C:\YMM4-Jobs` へ復元すれば現行案件は開けるが、別ルートでも動くことを移行合格条件にする。

## 辞書のフェーズ契約

CSVを先に読み込んではいけない。

### PRE_VOICE

- 単語辞書を全消去
- 案件DICだけを単語辞書へインポート
- 単語辞書が案件DICと表記・読みとも完全一致
- 有効な伏字辞書0件
- 応仁の乱案件は311件、`他の→ほかの`
- runtime gateレポートがPASSしてからCSVを読み込む

### POST_JOB_CLEANUP

- 音声生成・保存後に辞書を消すことは許可
- PRE_VOICEの履歴証拠と、cleanup後の状態を別レポートにする
- cleanup後の辞書状態を、音声生成前の証明として再利用しない

## 完全再現の音声契約

- 正解見本のFrame、Length、Layer、Group、全非音声アイテムを動かさない
- 実音声が枠を超えたVoiceだけPlaybackRateを最小限上げる
- `Length=Round((VoiceLength+AdditionalTime)*FPS, AwayFromZero)` を全Voiceで満たす
- VoiceLengthが割当Lengthまたは次のVoice Frameを超えない
- `--timing reanchor` は新規台本専用。完全再現では禁止

## レベル2の独立評価

一部分だけ変更する研修では、制作者と検査者を同じエージェントにしない。

- 画像、セリフ、BGM、SE、キャラクター順は、それぞれ別の専門編集エージェントが担当する
- 各課題は未変更のゴールデン案件から別案件として開始し、変更対象は1種類だけに固定する
- 各課題のQAは、制作へ参加していない新規エージェントを別コンテキストで起動し、読み取り専用で行う
- QA担当へ制作者の自己評価を渡さない
- 司令塔は制作物を変更せず、固定見本、宣言された変更範囲、機械比較レポートだけで合否を決める
- `.ymmp`構造差分、素材ハッシュ、音声、全フレーム、音量で「指定箇所以外が不変」を証明する
- 人間は最終の見た目・聴感だけを確認する

## レンダーQA

必須証拠:

- `.ymmp` 最終QA PASS
- 1920×1080、30fps
- 映像と音声ストリームあり
- ffmpeg全デコード exit 0
- 先頭・中間・18:25・末尾の代表フレーム確認
- 音声欠落・重なり0
- 元動画との差分理由をレポート化

## 公開ゲート

確認用動画の作成はできるが、次が終わるまで公開しない。

- AquesTalkの商用利用条件確認
- 106素材の権利・クレジット確認
- ラノベPOP v2の再配布条件確認
- 人間による最終視聴

## 別PC移行の合格条件

- 別ユーザー名のクリーンWindows
- X/Y/Nドライブと `\\Mac` を接続しない
- manifest、実行環境、フォント、全テストがPASS
- PRE_VOICE辞書ゲートPASS
- ゴールデン案件482件、205参照、106ユニーク、欠落0
- YMM4で開く・保存・レンダーできる
- MP4全デコードPASS
- インストーラー2回実行で二重配置・意図しない上書き0
- 素材1件を故意に壊すとmanifest/QAが確実にFAIL
- 秘密情報・ログ・backup混入0
