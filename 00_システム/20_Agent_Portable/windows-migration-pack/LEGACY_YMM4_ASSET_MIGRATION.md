# 既存YMM4案件とSSD素材の移行

## 対象

現在のv1.1.2 handoffへ入っている応仁の乱案件以外の、過去案件・編集中案件・SSD上の動画素材をWindowsでも開けるようにする。

## 基本方針

- SSD全体を無条件に複製しない
- 案件ごとに実際に参照している素材を特定する
- 元ymmpと元素材は変更しない
- 素材は独立した物理コピーにする。hardlinkを使わない
- Windowsで使う新規ymmpだけを新パスへrebaseする
- missing 0を機械確認してからYMM4で開く

## 1. 移行対象を分類する

各案件を次のいずれかへ分類する。

| 分類 | 移行 |
|---|---|
| 今後も編集する | 案件と全参照素材を移行 |
| 完成見本として使う | golden packとして移行 |
| 完成済みで保管だけ | 元SSDへ残し、必要時に後日移行 |
| 重複・用途不明 | 削除せず確認待ち |

## 2. 移行元で案件パックを作る

完成案件を再現用に登録する場合は、ymm4-project-builderのregister_golden_case.pyをcopy-assets付きで使う。inventory-onlyやhardlinkでは移行合格にしない。

必要証拠:

- 入力ymmp SHA-256
- 参照ファイル総数
- ユニーク素材数
- missing 0
- 各素材のSHA-256
- 台本、DIC、reference MP4の有無
- 素材の権利確認状態

同名パックが存在する場合は上書きせず、新しいversion名を使う。

## 3. MacからWindowsへコピーする

1. 元のMac用SSDはMac miniへ接続する。
2. 対象のversioned案件パックだけをSMBで共有する。
3. WindowsローカルのC:\Transferへコピーする。
4. transport manifestを検証する。
5. C:\YMM4-Jobsへ案件単位で独立コピーする。

動画素材の総量が内蔵SSDへ入らない場合は、新しいWindows用SSDをWindowsへ接続し、固定S:のNTFSとして使う。現在のMac用SSDを初期化しない。

## 4. Windowsパスへrebaseする

変換例:

| 旧参照 | 新参照 |
|---|---|
| /Volumes/SSD/YouTube/... | S:\YMM4-Assets\... |
| X:\YouTube\... | S:\YMM4-Assets\... |
| \\Mac\SSD\... | S:\YMM4-Assets\... |
| Mac共有内の案件パス | C:\YMM4-Jobs\案件名\... |

変換はrelease v1.1.2のRebase-Ymm4Job.pyを使い、入力と出力を別ファイルにする。部分一致や一括文字列置換を使わず、明示した旧rootと新rootだけを変換する。

## 5. 合格条件

- 元ymmpのhashが移行前後で不変
- 元素材のhashが不変
- Windowsコピーのmanifest一致
- rebase出力に旧パス残存0
- FilePathのmissing 0
- YMM4を開く前のstrict QA PASS
- YMM4で開く、別名保存、再QA PASS
- 確認MP4の全デコードPASS
- 人間が字幕・音声・映像を確認

案件ごとにこの合格条件を通す。1案件のPASSを、未監査の全案件へ流用しない。

