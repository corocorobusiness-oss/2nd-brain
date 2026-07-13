$ErrorActionPreference = 'Stop'

function Read-OninJson {
    param([string]$Path)
    Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Get-OninVoices {
    param($Project)
    @($Project.Timelines[0].Items |
        Where-Object { [string]$_.'$type' -match 'VoiceItem' } |
        Sort-Object @{ Expression = { [int]$_.Frame } }, @{ Expression = { [int]$_.Layer } })
}

function Get-OninHatsuonText {
    param($Voice)
    if ($Voice.Hatsuon -is [string]) { return [string]$Voice.Hatsuon }
    if ($null -ne $Voice.Hatsuon.Text) { return [string]$Voice.Hatsuon.Text }
    if ($null -ne $Voice.Hatsuon.Value) { return [string]$Voice.Hatsuon.Value }
    return [string]$Voice.Hatsuon
}

$dir = 'N:\YouTube\創作スレ下書き\2026-07-12_応仁の乱AI作成'
$sourceDic = Join-Path $dir 'ymm4_user.dic'
$targetDic = Join-Path $dir 'ymm4_user_修正版.dic'
$auditDir = Join-Path $dir '__診断・中間版'
$auditCsv = Join-Path $auditDir '読み差12件監査.csv'
$sourceYmmp = 'N:\YouTube\創作スレ下書き\2026-07-12_応仁の乱\【2ch歴史】応仁の乱、途中から何で戦ってるか分からなくなった件www.ymmp'
$newYmmp = Join-Path $dir '応仁の乱_AI作成_単語辞書修正版音声.ymmp'

if (Test-Path -LiteralPath $targetDic) { throw "Target DIC already exists: $targetDic" }
if (Test-Path -LiteralPath $auditCsv) { throw "Audit CSV already exists: $auditCsv" }

$sourceHashBefore = (Get-FileHash -LiteralPath $sourceDic -Algorithm SHA256).Hash
$sourceBytes = [System.IO.File]::ReadAllBytes($sourceDic)
if ($sourceBytes.Length -lt 1 -or $sourceBytes[$sourceBytes.Length - 1] -ne 0x0A) {
    throw 'Source DIC does not end with LF.'
}
if ($sourceBytes.Length -ge 3 -and $sourceBytes[0] -eq 0xEF -and $sourceBytes[1] -eq 0xBB -and $sourceBytes[2] -eq 0xBF) {
    throw 'Source DIC unexpectedly has a UTF-8 BOM.'
}

$additionText = "1`t0`t他の`tほかの`t`t1`n"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$additionBytes = $utf8NoBom.GetBytes($additionText)
$targetBytes = New-Object byte[] ($sourceBytes.Length + $additionBytes.Length)
[System.Buffer]::BlockCopy($sourceBytes, 0, $targetBytes, 0, $sourceBytes.Length)
[System.Buffer]::BlockCopy($additionBytes, 0, $targetBytes, $sourceBytes.Length, $additionBytes.Length)
[System.IO.File]::WriteAllBytes($targetDic, $targetBytes)

$dicEntries = @()
$lineNumber = 0
Get-Content -LiteralPath $sourceDic -Encoding UTF8 | ForEach-Object {
    $lineNumber++
    $parts = $_ -split "`t"
    if ($parts.Count -lt 4) { throw "Malformed DIC row: $lineNumber" }
    $dicEntries += [pscustomobject]@{
        Line = $lineNumber
        From = [string]$parts[2]
        To = [string]$parts[3]
    }
}

$meta = @{
    5 = @{ Class = '辞書による意図的修正（ｗ音声化）'; Cause = 'DICの「ｗｗｗｗｗｗ→わらわらわらわらわらわら」が適用され、正本では無音だった末尾が「わら」6回になった。'; Policy = '方針確定：維持' }
    24 = @{ Class = '語彙同一・アクセント／境界差'; Cause = '「畠山」「斯波」「管領」の明示置換後、YMM4が周辺を再解析し「だす,かんれい」から「だ_スかんれい」へ変化した。'; Policy = '維持（必要なら試聴確認）' }
    67 = @{ Class = '辞書による正しい読み補正・境界差'; Cause = '「京都民→きょうとみん」により、正本の「きょーと/みん」から仮名表記と語境界が変化。「一日→いちにち」も適用。'; Policy = '維持' }
    104 = @{ Class = '辞書による正しい読み補正'; Cause = '「後の東西軍→あとのとうざいぐん」により、正本の誤読「ごの/ひがし/せいぐん」を修正。'; Policy = '維持' }
    105 = @{ Class = '辞書による意図的修正（ｗ音声化）'; Cause = '文全体または「ｗ→わら」の辞書置換により末尾に「わら」が追加。'; Policy = '方針確定：維持' }
    109 = @{ Class = '語彙同一・アクセント／境界差'; Cause = '「義廉→よしかど」の明示置換後、同じ仮名列が「よ_シか/ど」から「よし/かど」へ再解析された。'; Policy = '維持' }
    143 = @{ Class = '辞書による意図的修正（ｗ音声化）'; Cause = '「親戚の集まり気まずすぎるｗ」または「ｗ→わら」の辞書置換により、正本の「う」から「わら」へ変化。'; Policy = '方針確定：維持' }
    153 = @{ Class = '辞書による正しい読み補正'; Cause = '「人が京都→ひとがきょうと」により、正本の誤読「にんが」を「ひとが」へ修正。人名・地名・1477年も明示置換。'; Policy = '維持' }
    156 = @{ Class = '辞書による正しい読み補正'; Cause = '「一方向→いちほうこう」により、正本の誤読「いっぽうむけ」を修正。「乱後」「国人」も明示置換。'; Policy = '維持' }
    160 = @{ Class = '辞書による意図的修正（ｗ音声化）'; Cause = '文全体または「ｗ→わら」の辞書置換により、正本の「う」から「わら」へ変化。'; Policy = '方針確定：維持' }
    165 = @{ Class = '辞書による正しい読み補正'; Cause = '「後から→あとから」により、正本の誤読「ごから」を修正。'; Policy = '維持' }
    185 = @{ Class = '元DIC非該当の明確な誤読回帰'; Cause = '元DICにこのSerifへ一致するFromがなく、再生成時に「他の」を「たの」と誤解析。'; Policy = '修正版DICに「他の→ほかの」を追加' }
}

$sourceProject = Read-OninJson $sourceYmmp
$newProject = Read-OninJson $newYmmp
$sourceVoices = Get-OninVoices $sourceProject
$newVoices = Get-OninVoices $newProject
if ($sourceVoices.Count -ne 187 -or $newVoices.Count -ne 187) {
    throw "Unexpected voice counts: source=$($sourceVoices.Count), new=$($newVoices.Count)"
}

$indices = @(5, 24, 67, 104, 105, 109, 143, 153, 156, 160, 165, 185)
$rows = @()
foreach ($index in $indices) {
    $serif = [string]$sourceVoices[$index].Serif
    $matches = @($dicEntries |
        Where-Object { $_.From.Length -gt 0 -and $serif.IndexOf($_.From, [StringComparison]::Ordinal) -ge 0 } |
        Sort-Object @{ Expression = { $_.From.Length }; Descending = $true }, Line)
    $matchText = if ($matches.Count -eq 0) {
        ''
    } else {
        ($matches | ForEach-Object { "L$($_.Line): $($_.From) → $($_.To)" }) -join ' | '
    }
    $m = $meta[$index]
    $rows += [pscustomobject][ordered]@{
        Index = $index
        Serif = $serif
        '正本Hatsuon' = Get-OninHatsuonText $sourceVoices[$index]
        '新規Hatsuon' = Get-OninHatsuonText $newVoices[$index]
        '元DIC該当有無' = if ($matches.Count -gt 0) { '有' } else { '無' }
        '元DIC該当件数' = $matches.Count
        '元DIC該当From→To' = $matchText
        '分類' = $m.Class
        '推定原因' = $m.Cause
        '対応方針' = $m.Policy
        '修正版DIC追加From→To' = if ($index -eq 185) { '他の → ほかの' } else { '' }
    }
}

if (-not (Test-Path -LiteralPath $auditDir)) {
    New-Item -ItemType Directory -Path $auditDir | Out-Null
}
$rows | Export-Csv -LiteralPath $auditCsv -NoTypeInformation -Encoding UTF8

$sourceHashAfter = (Get-FileHash -LiteralPath $sourceDic -Algorithm SHA256).Hash
if ($sourceHashBefore -cne $sourceHashAfter) { throw 'Source DIC hash changed.' }

$targetRaw = Get-Content -LiteralPath $targetDic -Raw -Encoding UTF8
$targetLines = @(Get-Content -LiteralPath $targetDic -Encoding UTF8)
$targetParsed = @($targetLines | ForEach-Object {
    $p = $_ -split "`t"
    if ($p.Count -lt 4) { throw 'Malformed target DIC row.' }
    [pscustomobject]@{ From = [string]$p[2]; To = [string]$p[3] }
})
$duplicates = @($targetParsed | Group-Object From | Where-Object { $_.Count -gt 1 })
$added = @($targetParsed | Where-Object { $_.From -ceq '他の' -and $_.To -ceq 'ほかの' })
$targetCheckBytes = [System.IO.File]::ReadAllBytes($targetDic)
$targetHasBom = $targetCheckBytes.Length -ge 3 -and $targetCheckBytes[0] -eq 0xEF -and $targetCheckBytes[1] -eq 0xBB -and $targetCheckBytes[2] -eq 0xBF
$crlfCount = ([regex]::Matches($targetRaw, "`r`n")).Count
$bareLfCount = ([regex]::Matches($targetRaw, "(?<!`r)`n")).Count
$auditRows = @(Import-Csv -LiteralPath $auditCsv -Encoding UTF8)

if ($targetLines.Count -ne 311) { throw "Target DIC row count is $($targetLines.Count), expected 311." }
if ($duplicates.Count -ne 0) { throw "Duplicate From entries found: $($duplicates.Name -join ', ')" }
if ($added.Count -ne 1) { throw "Added entry count is $($added.Count), expected 1." }
if ($targetHasBom) { throw 'Target DIC unexpectedly has BOM.' }
if ($crlfCount -ne 0 -or $bareLfCount -ne 311 -or -not $targetRaw.EndsWith("`n")) { throw 'Target DIC newline format mismatch.' }
if ($auditRows.Count -ne 12) { throw "Audit CSV row count is $($auditRows.Count), expected 12." }

[pscustomobject][ordered]@{
    SourceDic = $sourceDic
    SourceSha256 = $sourceHashAfter
    TargetDic = $targetDic
    TargetSha256 = (Get-FileHash -LiteralPath $targetDic -Algorithm SHA256).Hash
    TargetBytes = $targetCheckBytes.Length
    TargetRows = $targetLines.Count
    Utf8Bom = $targetHasBom
    Newline = 'LF'
    EndsWithLF = $targetRaw.EndsWith("`n")
    DuplicateFromCount = $duplicates.Count
    AddedEntryCount = $added.Count
    AddedFrom = $added[0].From
    AddedTo = $added[0].To
    AuditCsv = $auditCsv
    AuditCsvRows = $auditRows.Count
    AuditCsvSha256 = (Get-FileHash -LiteralPath $auditCsv -Algorithm SHA256).Hash
} | ConvertTo-Json -Depth 4
