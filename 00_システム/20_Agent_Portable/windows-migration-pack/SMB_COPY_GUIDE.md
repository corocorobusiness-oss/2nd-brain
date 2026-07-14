# MacのSSDからWindowsへ安全にコピーする

## 結論

Windowsが現在のSSDを直接読めなくても、Mac miniがSSDを読み、SMB経由でWindowsへ渡せる。Windowsでフォーマット要求が出てもキャンセルする。

## Mac mini

1. SSDをMac miniへ接続したままにする。
2. システム設定、一般、共有、ファイル共有をオンにする。
3. 情報、共有フォルダから、移行に必要なフォルダだけを追加する。
4. オプションでSMB共有をオンにする。
5. Windows共有を使うMacアカウントを有効にする。
6. 表示されたsmb://IPアドレスを控える。
7. 最初はWindows側へ読み取り専用で公開する。

Mac全体やホーム全体を共有せず、移行パックまたはYMM4 handoffなど必要なフォルダだけを共有する。

## Windows

1. Mac miniと同じ家庭内ネットワークへ接続する。大容量は有線LANを推奨。
2. エクスプローラーのアドレス欄へ \\MacのIPアドレス を入力する。
3. Macのユーザー名とパスワードで接続する。
4. まず小さなテストファイルをWindowsローカルへコピーする。
5. Windows側のコピーを開けることを確認する。
6. 大容量はscripts\Copy-FromMacShare.ps1をApplyなしで確認し、承認後にApply付きで使う。

## 推奨保存先

| 種類 | Windows保存先 |
|---|---|
| 移行パック | C:\Migration-Work\windows-migration-pack |
| YMM4 transport | C:\Transfer\YMM4-AI-HANDOFF-20260714-v1.1.2 |
| 編集中案件 | C:\YMM4-Jobs\案件名 |
| 小規模素材庫 | C:\YMM4-Assets |
| 大規模素材庫 | 固定S:\YMM4-Assets |

## YMM4のパス変更

YMM4の素材参照は絶対パスを含む場合があるため、コピーだけで完了扱いにしない。

旧パス例:

- /Volumes/SSD/YouTube
- X:\YouTube
- Y:\Projects
- N:\
- \\Mac\SSD
- C:\Users\kojinn

新パス例:

- C:\YMM4-Jobs\案件名
- C:\YMM4-Assets
- S:\YMM4-Assets

移行手順:

1. 元ymmpから全参照を抽出する。
2. 必要素材をmanifest化してWindowsへコピーする。
3. コピー先のhashを検証する。
4. Rebase-Ymm4Job.pyで別名の新規ymmpを作る。
5. 旧パス残存0、missing 0を確認する。
6. その後にだけYMM4で開く。

元ymmp、元素材、SSDは上書きしない。

## 新しいWindows用SSDを使う場合

Windowsをメインにするなら、新しいSSDをWindowsへ接続してNTFSで使い、固定S:を割り当てるのが安定する。現在のMac用SSDはバックアップがない状態でフォーマットしない。

Mac用SSDから新しいWindows用SSDへのコピーは、Mac用SSDをMacへ、新しいSSDをWindowsへ接続し、SMB越しにWindows側が書き込めばよい。

