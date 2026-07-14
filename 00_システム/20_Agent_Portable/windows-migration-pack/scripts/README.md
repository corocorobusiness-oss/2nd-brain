# scripts

すべてPowerShell 5.1以上を対象にした補助スクリプト。元データの削除、移動、フォーマット、Git更新は行わない。

## 実行順

1. Test-MigrationPack.ps1
2. Test-WindowsMigrationPreflight.ps1
3. Initialize-WindowsWorkspace.ps1。最初はApplyなし
4. Copy-FromMacShare.ps1。最初はApplyなし
5. Git clone後にTest-PostClone.ps1

## 共通ルール

- Windows内蔵ストレージへ移行パックをコピーしてから実行する
- PowerShellを管理者権限で起動しないところから始める
- Applyのない初回実行は計画表示だけ
- 元データを変更しない
- ログとレポートはC:\Migration-Work\reportsへ置く
- レポートへ認証情報を入れない
- FAIL時は同じ操作を推測で繰り返さず、証拠をCodexへ返す

## コマンド例

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Test-MigrationPack.ps1

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Test-WindowsMigrationPreflight.ps1

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Initialize-WindowsWorkspace.ps1

確認後:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Initialize-WindowsWorkspace.ps1 -Apply

Mac共有からのコピー計画:

    powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Copy-FromMacShare.ps1 -Source '\\192.168.1.10\YMM4-HANDOFF' -Destination 'C:\Transfer\YMM4-AI-HANDOFF-20260714-v1.1.2'

承認後だけ末尾へApplyを付ける。

