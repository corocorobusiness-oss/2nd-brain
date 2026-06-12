# YMM4 Windows移行 調査メモ

作成日: 2026-06-11

## 結論

Macから直接見つかったYMM4プロジェクトは以下。

- `/Users/kabushikikaishakorokoro/CoworkAgent/projects/無題_BGM修正済み.ymmp`

このプロジェクトは「家康が最も恐れた男って結局誰なんや？」系の編集データ。
中身の参照先を見る限り、動画編集素材の本体は主に以下にある。

- Windows側の `X:\YouTube\2ch世界史＿動画編集\YukkuriMovieMaker_v4 (1)\`
- Google Drive側の `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\`
- Mac共有SSD側の `\\Mac\SSD\2ch世界史\家康が最も恐れた男って結局誰なんや？\`

## Parallels / Windows本体

Parallelsの履歴上、仮想Windowsの候補は以下。

- `/Volumes/SSD/windows：SSD/Windows 11.pvm/harddisk.hdd`
- `/Volumes/SSD/windows：SSD/Windows 11 (1).pvm/harddisk.hdd`
- `/Users/kabushikikaishakorokoro/Parallels/Windows 11.pvm/harddisk.hdd`

現在のMacでは `/Volumes/SSD` がマウントされていないため、外付けSSD内のWindows本体や素材は未確認。
`/Users/kabushikikaishakorokoro/Parallels` はほぼ空で、現在そこに仮想Windows本体はない。

## 見つかったYMM4関連ファイル

- `/Users/kabushikikaishakorokoro/CoworkAgent/projects/無題_BGM修正済み.ymmp`
- `/Users/kabushikikaishakorokoro/Library/CloudStorage/GoogleDrive-corocoro.business@gmail.com/マイドライブ/20260610_縄文人の生活_ymm4_user.dic`
- `01_プロジェクト/YouTube/制作アーカイブ/平将門_script/ymm4_user.dic`

## プロジェクト内の参照素材

YMM4プロジェクト内で確認できた素材カテゴリ。

- 音声アイテム: 160
- 画像アイテム: 160
- 動画アイテム: 28
- 音声/BGMアイテム: 7

主な参照フォルダ。

- `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\コメント用_画像`
- `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\背景用動画`
- `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\BGM`
- `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\共通素材\SE`
- `G:\マイドライブ\YouTube\競合分析\2ch風YouTube参考マニュアル\BGM5\メインで使用するＢＧＭ`
- `\\Mac\SSD\2ch世界史\家康が最も恐れた男って結局誰なんや？`

## WindowsノートPCへ移す時に必要なもの

優先度高。

1. `無題_BGM修正済み.ymmp`
2. `X:\YouTube\2ch世界史＿動画編集\YukkuriMovieMaker_v4 (1)\` 一式
3. `G:\マイドライブ\YouTube_2ch世界史\2ch世界史_動画編集\ゆっくり系動画_素材候補\` 一式
4. `\\Mac\SSD\2ch世界史\` 配下の制作別素材フォルダ
5. `ymm4_user.dic`

注意点。

- 新WindowsではGoogle Driveのドライブ文字が `G:` にならない可能性がある。
- YMM4で素材切れを避けるには、できれば新PCでも同じフォルダ構成にする。
- 外付けSSDをMacに接続してから、`/Volumes/SSD/windows：SSD/` と `\\Mac\SSD\2ch世界史\` 相当の実体を確認する。
