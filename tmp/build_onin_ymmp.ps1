param(
    [Parameter(Mandatory = $true)]
    [string]$SourceYmmp,

    [Parameter(Mandatory = $true)]
    [string]$TargetVoiceYmmp,

    [Parameter(Mandatory = $true)]
    [string]$AssetsDir,

    [Parameter(Mandatory = $true)]
    [string]$OutputYmmp
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Set-StrictMode -Version 2.0

function Get-FullPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $expanded = [Environment]::ExpandEnvironmentVariables($Path)
    if ([System.IO.Path]::IsPathRooted($expanded)) {
        return [System.IO.Path]::GetFullPath($expanded)
    }
    return [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $expanded))
}

function Convert-ToUncPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    $full = Get-FullPath $Path
    if ($full.StartsWith('\\')) {
        return $full
    }

    if ($full -match '^([A-Za-z]):(\\.*)$') {
        $driveName = $matches[1]
        $driveTail = $matches[2]
        $drive = Get-PSDrive -Name $driveName -ErrorAction SilentlyContinue
        if ($null -ne $drive) {
            $root = [string]$drive.Root
            if ($root.StartsWith('\\')) {
                return $root.TrimEnd('\') + $driveTail
            }
        }
    }
    return $full
}

function Read-JsonFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "File not found: $Path"
    }
    return ([System.IO.File]::ReadAllText($Path) | ConvertFrom-Json)
}

function Copy-JsonObject {
    param([Parameter(Mandatory = $true)]$Value)

    return (($Value | ConvertTo-Json -Depth 100 -Compress) | ConvertFrom-Json)
}

function Get-ItemKind {
    param([Parameter(Mandatory = $true)]$Item)

    $typeProperty = $Item.PSObject.Properties['$type']
    if ($null -eq $typeProperty) {
        return ''
    }
    $rawType = [string]$typeProperty.Value
    $typeName = ($rawType -split ',')[0].Trim()
    return ($typeName -split '\.')[-1]
}

function Get-SelectedTimeline {
    param(
        [Parameter(Mandatory = $true)]$Project,
        [Parameter(Mandatory = $true)][string]$Label
    )

    $index = [int]$Project.SelectedTimelineIndex
    if ($index -lt 0 -or $index -ge @($Project.Timelines).Count) {
        throw "$Label has an invalid SelectedTimelineIndex: $index"
    }
    return $Project.Timelines[$index]
}

function Get-SortedVoices {
    param([Parameter(Mandatory = $true)]$Timeline)

    return @($Timeline.Items |
        Where-Object { (Get-ItemKind $_) -eq 'VoiceItem' } |
        Sort-Object Frame, Layer)
}

function Test-JsonValueEqual {
    param($Left, $Right)

    if ($null -eq $Left -and $null -eq $Right) {
        return $true
    }
    if ($null -eq $Left -or $null -eq $Right) {
        return $false
    }
    if ($Left -is [string] -and $Right -is [string]) {
        return [string]::Equals([string]$Left, [string]$Right, [StringComparison]::Ordinal)
    }
    $leftJson = $Left | ConvertTo-Json -Depth 100 -Compress
    $rightJson = $Right | ConvertTo-Json -Depth 100 -Compress
    return [string]::Equals($leftJson, $rightJson, [StringComparison]::Ordinal)
}

$sourcePath = Get-FullPath $SourceYmmp
$targetPath = Get-FullPath $TargetVoiceYmmp
$assetsPath = Get-FullPath $AssetsDir
$outputPath = Get-FullPath $OutputYmmp

if (-not (Test-Path -LiteralPath $assetsPath -PathType Container)) {
    throw "Assets directory not found: $assetsPath"
}
if ([string]::Equals($outputPath, $sourcePath, [StringComparison]::OrdinalIgnoreCase) -or
    [string]::Equals($outputPath, $targetPath, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'OutputYmmp must not overwrite either input YMMP.'
}

$outputDirectory = Split-Path -Parent $outputPath
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$source = Read-JsonFile $sourcePath
$target = Read-JsonFile $targetPath
$sourceTimeline = Get-SelectedTimeline $source 'SourceYmmp'
$targetTimeline = Get-SelectedTimeline $target 'TargetVoiceYmmp'
$sourceVoices = Get-SortedVoices $sourceTimeline
$targetVoices = Get-SortedVoices $targetTimeline

if ($sourceVoices.Count -ne 187) {
    throw "SourceYmmp must contain exactly 187 VoiceItem objects; found $($sourceVoices.Count)."
}
if ($targetVoices.Count -ne 187) {
    throw "TargetVoiceYmmp must contain exactly 187 VoiceItem objects; found $($targetVoices.Count)."
}

$scriptMismatch = New-Object System.Collections.Generic.List[object]
$characterMismatch = New-Object System.Collections.Generic.List[object]
for ($i = 0; $i -lt 187; $i++) {
    if (-not [string]::Equals([string]$sourceVoices[$i].Serif, [string]$targetVoices[$i].Serif, [StringComparison]::Ordinal)) {
        $scriptMismatch.Add([pscustomobject]@{
            index = $i
            source_frame = [int]$sourceVoices[$i].Frame
            target_frame = [int]$targetVoices[$i].Frame
            source_serif = [string]$sourceVoices[$i].Serif
            target_serif = [string]$targetVoices[$i].Serif
        })
    }
    if (-not [string]::Equals([string]$sourceVoices[$i].CharacterName, [string]$targetVoices[$i].CharacterName, [StringComparison]::Ordinal)) {
        $characterMismatch.Add([pscustomobject]@{
            index = $i
            source_character = [string]$sourceVoices[$i].CharacterName
            target_character = [string]$targetVoices[$i].CharacterName
        })
    }
}
if ($scriptMismatch.Count -ne 0) {
    throw "The 187 source and target voice scripts are not identical. Mismatches: $($scriptMismatch.Count)."
}

$sourceNonVoice = @($sourceTimeline.Items | Where-Object { (Get-ItemKind $_) -ne 'VoiceItem' })
if ($sourceNonVoice.Count -ne 295) {
    throw "SourceYmmp must contain exactly 295 non-voice items; found $($sourceNonVoice.Count)."
}

$sourceAnchors = New-Object System.Collections.Generic.List[double]
$targetAnchors = New-Object System.Collections.Generic.List[double]
foreach ($voice in $sourceVoices) {
    $sourceAnchors.Add([double]$voice.Frame)
}
foreach ($voice in $targetVoices) {
    $targetAnchors.Add([double]$voice.Frame)
}
$sourceAnchors.Add([double]$sourceTimeline.Length)
$targetAnchors.Add([double]$targetTimeline.Length)

for ($i = 1; $i -lt $sourceAnchors.Count; $i++) {
    if ($sourceAnchors[$i] -le $sourceAnchors[$i - 1]) {
        throw "Source voice/timeline anchors are not strictly increasing at index $i."
    }
    if ($targetAnchors[$i] -le $targetAnchors[$i - 1]) {
        throw "Target voice/timeline anchors are not strictly increasing at index $i."
    }
}

function Convert-Frame {
    param([Parameter(Mandatory = $true)][double]$Frame)

    if ($Frame -le $sourceAnchors[0]) {
        return [int][Math]::Round(
            $targetAnchors[0] + ($Frame - $sourceAnchors[0]),
            [MidpointRounding]::AwayFromZero
        )
    }

    for ($anchorIndex = 0; $anchorIndex -lt $sourceAnchors.Count - 1; $anchorIndex++) {
        $sourceStart = $sourceAnchors[$anchorIndex]
        $sourceEnd = $sourceAnchors[$anchorIndex + 1]
        if ($Frame -le $sourceEnd) {
            $targetStart = $targetAnchors[$anchorIndex]
            $targetEnd = $targetAnchors[$anchorIndex + 1]
            $ratio = ($Frame - $sourceStart) / ($sourceEnd - $sourceStart)
            $mapped = $targetStart + ($ratio * ($targetEnd - $targetStart))
            return [int][Math]::Round($mapped, [MidpointRounding]::AwayFromZero)
        }
    }

    $lastIndex = $sourceAnchors.Count - 1
    return [int][Math]::Round(
        $targetAnchors[$lastIndex] + ($Frame - $sourceAnchors[$lastIndex]),
        [MidpointRounding]::AwayFromZero
    )
}

# Project-local images are keyed by their source frame/layer so the mapping is
# deterministic even where the same source file is reused more than once.
$replacementSpecs = @(
    [pscustomobject]@{ Frame = 0;     Layer = 0; Asset = '17_onin_yoshitora.jpg' },
    [pscustomobject]@{ Frame = 193;   Layer = 2; Asset = '02_muromachi_samurai.jpg' },
    [pscustomobject]@{ Frame = 365;   Layer = 2; Asset = '01_onin_marker.jpg' },
    [pscustomobject]@{ Frame = 891;   Layer = 1; Asset = '14_funaki_kyoto.jpg' },
    [pscustomobject]@{ Frame = 2811;  Layer = 3; Asset = '07_hosokawa_katsumoto.jpg' },
    [pscustomobject]@{ Frame = 2811;  Layer = 4; Asset = '15_yamana_sozen.jpg' },
    [pscustomobject]@{ Frame = 4113;  Layer = 3; Asset = '16_onin_scene3.jpg' },
    [pscustomobject]@{ Frame = 4571;  Layer = 0; Asset = '10_ashikaga_yoshimasa.jpg' },
    [pscustomobject]@{ Frame = 4736;  Layer = 0; Asset = '06_rakuchu_pair.jpg' },
    [pscustomobject]@{ Frame = 4957;  Layer = 0; Asset = '16_onin_scene3.jpg' },
    [pscustomobject]@{ Frame = 6153;  Layer = 3; Asset = '06_rakuchu_pair.jpg' },
    [pscustomobject]@{ Frame = 8102;  Layer = 1; Asset = '02_muromachi_samurai.jpg' },
    [pscustomobject]@{ Frame = 9596;  Layer = 4; Asset = '13_ashikaga_yoshimi.jpg' },
    [pscustomobject]@{ Frame = 9999;  Layer = 3; Asset = '13_ashikaga_yoshimi.jpg' },
    [pscustomobject]@{ Frame = 11226; Layer = 3; Asset = '10_ashikaga_yoshimasa.jpg' },
    [pscustomobject]@{ Frame = 14453; Layer = 0; Asset = '04_rakuchu_right.jpg' },
    [pscustomobject]@{ Frame = 14630; Layer = 0; Asset = '05_rakuchu_left.jpg' },
    [pscustomobject]@{ Frame = 14814; Layer = 0; Asset = '06_rakuchu_pair.jpg' },
    [pscustomobject]@{ Frame = 14814; Layer = 2; Asset = '18_kamigoryo_shrine.jpg' },
    [pscustomobject]@{ Frame = 16189; Layer = 1; Asset = '03_muromachi_ship.jpg' },
    [pscustomobject]@{ Frame = 16920; Layer = 1; Asset = '01_onin_marker.jpg' },
    [pscustomobject]@{ Frame = 17356; Layer = 1; Asset = '16_onin_scene3.jpg' },
    [pscustomobject]@{ Frame = 24146; Layer = 0; Asset = '02_muromachi_samurai.jpg' },
    [pscustomobject]@{ Frame = 24312; Layer = 0; Asset = '14_funaki_kyoto.jpg' },
    [pscustomobject]@{ Frame = 24426; Layer = 0; Asset = '03_muromachi_ship.jpg' },
    [pscustomobject]@{ Frame = 24600; Layer = 0; Asset = '12_onin_monument.jpg' },
    [pscustomobject]@{ Frame = 24893; Layer = 4; Asset = '02_muromachi_samurai.jpg' },
    [pscustomobject]@{ Frame = 27589; Layer = 3; Asset = '01_onin_marker.jpg' },
    [pscustomobject]@{ Frame = 32256; Layer = 0; Asset = '11_hosokawa_masamoto.jpg' },
    [pscustomobject]@{ Frame = 32256; Layer = 3; Asset = '11_hosokawa_masamoto.jpg' },
    [pscustomobject]@{ Frame = 32456; Layer = 0; Asset = '06_rakuchu_pair.jpg' },
    [pscustomobject]@{ Frame = 32456; Layer = 2; Asset = '09_ashikaga_yoshitane.jpg' },
    [pscustomobject]@{ Frame = 32456; Layer = 3; Asset = '11_hosokawa_masamoto.jpg' },
    [pscustomobject]@{ Frame = 32525; Layer = 2; Asset = '08_ashikaga_yoshihisa.jpg' },
    [pscustomobject]@{ Frame = 32604; Layer = 0; Asset = '12_onin_monument.jpg' },
    [pscustomobject]@{ Frame = 32819; Layer = 0; Asset = '04_rakuchu_right.jpg' },
    [pscustomobject]@{ Frame = 33693; Layer = 2; Asset = '14_funaki_kyoto.jpg' },
    [pscustomobject]@{ Frame = 34058; Layer = 2; Asset = '17_onin_yoshitora.jpg' }
)

if ($replacementSpecs.Count -ne 38) {
    throw "The replacement table must contain exactly 38 entries; found $($replacementSpecs.Count)."
}
if (@($replacementSpecs.Asset | Sort-Object -Unique).Count -ne 18) {
    throw 'The replacement table must reference all 18 external asset files.'
}

$replacementByKey = @{}
$assetPathSet = @{}
foreach ($spec in $replacementSpecs) {
    $key = '{0}|{1}' -f [int]$spec.Frame, [int]$spec.Layer
    if ($replacementByKey.ContainsKey($key)) {
        throw "Duplicate replacement key: $key"
    }
    $assetFile = Join-Path $assetsPath ([string]$spec.Asset)
    if (-not (Test-Path -LiteralPath $assetFile -PathType Leaf)) {
        throw "Mapped asset is missing: $assetFile"
    }
    $assetUnc = Convert-ToUncPath $assetFile
    $replacementByKey[$key] = $assetUnc
    $assetPathSet[$assetUnc.ToLowerInvariant()] = $true
}

$sourceProjectLeaf = Split-Path -Leaf (Split-Path -Parent $sourcePath)
$script:sourceProjectNeedle = '\' + $sourceProjectLeaf + '\'

function Test-SourceProjectLocalImage {
    param([Parameter(Mandatory = $true)]$Item)

    if ((Get-ItemKind $Item) -ne 'ImageItem') {
        return $false
    }
    $pathProperty = $Item.PSObject.Properties['FilePath']
    if ($null -eq $pathProperty -or [string]::IsNullOrWhiteSpace([string]$pathProperty.Value)) {
        return $false
    }
    $normalized = ([string]$pathProperty.Value).Replace('/', '\')
    return $normalized.IndexOf($script:sourceProjectNeedle, [StringComparison]::OrdinalIgnoreCase) -ge 0
}

$sourceLocalImages = @($sourceNonVoice | Where-Object { Test-SourceProjectLocalImage $_ })
if ($sourceLocalImages.Count -ne 38) {
    throw "SourceYmmp must contain exactly 38 project-local ImageItem objects; found $($sourceLocalImages.Count)."
}

$localKeySet = @{}
foreach ($item in $sourceLocalImages) {
    $key = '{0}|{1}' -f [int]$item.Frame, [int]$item.Layer
    if ($localKeySet.ContainsKey($key)) {
        throw "Duplicate source-local image key: $key"
    }
    if (-not $replacementByKey.ContainsKey($key)) {
        throw "No external replacement is defined for source-local image: $key"
    }
    $localKeySet[$key] = $true
}
foreach ($key in $replacementByKey.Keys) {
    if (-not $localKeySet.ContainsKey($key)) {
        throw "Replacement key does not match a source-local image: $key"
    }
}

# The output root is a deep copy of TargetVoiceYmmp. Target voices therefore
# retain all generated audio data, including Hatsuon and VoiceCache.
$output = Copy-JsonObject $target
$outputTimeline = Get-SelectedTimeline $output 'Output project'
$outputVoices = Get-SortedVoices $outputTimeline

for ($i = 0; $i -lt 187; $i++) {
    $outputVoices[$i].Layer = [int]$sourceVoices[$i].Layer
    $outputVoices[$i].Group = $sourceVoices[$i].Group
}

$mappedNonVoice = New-Object System.Collections.Generic.List[object]
foreach ($sourceItem in $sourceNonVoice) {
    $mapped = Copy-JsonObject $sourceItem
    $sourceStart = [double]$sourceItem.Frame
    $sourceEnd = $sourceStart + [double]$sourceItem.Length
    $mappedStart = Convert-Frame $sourceStart
    $mappedEnd = Convert-Frame $sourceEnd
    $mapped.Frame = [int]$mappedStart
    $mapped.Length = [int][Math]::Max(1, $mappedEnd - $mappedStart)

    if (Test-SourceProjectLocalImage $sourceItem) {
        $key = '{0}|{1}' -f [int]$sourceItem.Frame, [int]$sourceItem.Layer
        $mapped.FilePath = [string]$replacementByKey[$key]
    }
    $mappedNonVoice.Add($mapped)
}

$rebuiltItems = @($outputVoices) + @($mappedNonVoice)
$outputTimeline.Items = $rebuiltItems
$outputTimeline.LayerSettings = @(Copy-JsonObject $sourceTimeline.LayerSettings)
$outputTimeline.CurrentFrame = 0
$outputTimeline.Length = [int]$targetTimeline.Length
$maximumLayer = ($rebuiltItems | Measure-Object -Property Layer -Maximum).Maximum
$outputTimeline.MaxLayer = [int]$maximumLayer
$output.FilePath = Convert-ToUncPath $outputPath

$expectedCounts = [ordered]@{
    VoiceItem = 187
    ImageItem = 148
    ShapeItem = 74
    VideoItem = 54
    TextItem = 16
    AudioItem = 3
}
$actualCounts = @{}
foreach ($item in $outputTimeline.Items) {
    $kind = Get-ItemKind $item
    if (-not $actualCounts.ContainsKey($kind)) {
        $actualCounts[$kind] = 0
    }
    $actualCounts[$kind]++
}

if (@($outputTimeline.Items).Count -ne 482) {
    throw "Rebuilt timeline must contain exactly 482 items; found $(@($outputTimeline.Items).Count)."
}
foreach ($kind in $expectedCounts.Keys) {
    $actual = 0
    if ($actualCounts.ContainsKey($kind)) {
        $actual = [int]$actualCounts[$kind]
    }
    if ($actual -ne [int]$expectedCounts[$kind]) {
        throw "Unexpected $kind count. Expected $($expectedCounts[$kind]); found $actual."
    }
}

$outputVoicesForValidation = Get-SortedVoices $outputTimeline
$voiceTextPreserved = $true
$voiceHatsuonPreserved = $true
$voiceCachePreserved = $true
$voiceLengthPreserved = $true
for ($i = 0; $i -lt 187; $i++) {
    if (-not [string]::Equals([string]$targetVoices[$i].Serif, [string]$outputVoicesForValidation[$i].Serif, [StringComparison]::Ordinal)) {
        $voiceTextPreserved = $false
    }
    if (-not (Test-JsonValueEqual $targetVoices[$i].Hatsuon $outputVoicesForValidation[$i].Hatsuon)) {
        $voiceHatsuonPreserved = $false
    }
    if (-not (Test-JsonValueEqual $targetVoices[$i].VoiceCache $outputVoicesForValidation[$i].VoiceCache)) {
        $voiceCachePreserved = $false
    }
    if ($targetVoices[$i].VoiceLength -ne $outputVoicesForValidation[$i].VoiceLength) {
        $voiceLengthPreserved = $false
    }
}
if (-not $voiceTextPreserved -or -not $voiceHatsuonPreserved -or
    -not $voiceCachePreserved -or -not $voiceLengthPreserved) {
    throw 'One or more target voice payload fields changed during reconstruction.'
}

$externalImageCount = @($outputTimeline.Items | Where-Object {
    if ((Get-ItemKind $_) -ne 'ImageItem') { return $false }
    $property = $_.PSObject.Properties['FilePath']
    if ($null -eq $property) { return $false }
    $key = ([string]$property.Value).ToLowerInvariant()
    return $assetPathSet.ContainsKey($key)
}).Count
if ($externalImageCount -ne 38) {
    throw "Rebuilt timeline must contain exactly 38 mapped external ImageItem objects; found $externalImageCount."
}

$oldSourceLocalCount = @($outputTimeline.Items | Where-Object { Test-SourceProjectLocalImage $_ }).Count
if ($oldSourceLocalCount -ne 0) {
    throw "Rebuilt timeline still contains $oldSourceLocalCount old source-local image paths."
}

$referencedPaths = @($outputTimeline.Items | ForEach-Object {
    $property = $_.PSObject.Properties['FilePath']
    if ($null -ne $property -and -not [string]::IsNullOrWhiteSpace([string]$property.Value)) {
        [string]$property.Value
    }
} | Sort-Object -Unique)
$missingPaths = @($referencedPaths | Where-Object { -not (Test-Path -LiteralPath $_ -PathType Leaf) })
if ($missingPaths.Count -ne 0) {
    throw "Rebuilt timeline contains $($missingPaths.Count) missing FilePath references: $($missingPaths -join '; ')"
}

$utf8Bom = New-Object System.Text.UTF8Encoding($true)
$outputJson = $output | ConvertTo-Json -Depth 100
[System.IO.File]::WriteAllText($outputPath, $outputJson, $utf8Bom)

$outputHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $outputPath).Hash
$verificationPath = Join-Path $outputDirectory (([System.IO.Path]::GetFileNameWithoutExtension($outputPath)) + '_verification.json')
$countReport = [ordered]@{}
foreach ($kind in $expectedCounts.Keys) {
    $countReport[$kind] = [int]$actualCounts[$kind]
}

$verification = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    source_ymmp = Convert-ToUncPath $sourcePath
    target_voice_ymmp = Convert-ToUncPath $targetPath
    output_ymmp = [string]$output.FilePath
    source_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $sourcePath).Hash
    target_voice_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetPath).Hash
    output_sha256 = $outputHash
    item_count = @($outputTimeline.Items).Count
    item_counts = $countReport
    source_nonvoice_count = $sourceNonVoice.Count
    external_image_count = $externalImageCount
    old_source_local_image_count = $oldSourceLocalCount
    referenced_file_count = $referencedPaths.Count
    missing_file_count = $missingPaths.Count
    source_timeline_length = [int]$sourceTimeline.Length
    target_timeline_length = [int]$targetTimeline.Length
    output_timeline_length = [int]$outputTimeline.Length
    output_max_layer = [int]$outputTimeline.MaxLayer
    voice_script_match = ($scriptMismatch.Count -eq 0)
    character_name_match = ($characterMismatch.Count -eq 0)
    character_name_mismatch_count = $characterMismatch.Count
    voice_text_preserved = $voiceTextPreserved
    voice_hatsuon_preserved = $voiceHatsuonPreserved
    voice_cache_preserved = $voiceCachePreserved
    voice_length_preserved = $voiceLengthPreserved
    output_filepath_is_unc = ([string]$output.FilePath).StartsWith('\\')
}
[System.IO.File]::WriteAllText(
    $verificationPath,
    ($verification | ConvertTo-Json -Depth 20),
    $utf8Bom
)

[pscustomobject]@{
    output = $outputPath
    output_unc = [string]$output.FilePath
    output_sha256 = $outputHash
    verification = $verificationPath
    item_count = @($outputTimeline.Items).Count
    external_image_count = $externalImageCount
    missing_file_count = $missingPaths.Count
} | ConvertTo-Json -Depth 5
