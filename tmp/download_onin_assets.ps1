param(
    [Parameter(Mandatory = $true)]
    [string]$TargetDir
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Web

$macronO = [char]0x014D
$macronU = [char]0x016B
$circO = [char]0x00F4

$specs = @(
    [pscustomobject]@{ id = 'onin_marker'; file = '01_onin_marker.jpg'; title = 'File:OninNoRanMarker.jpg' },
    [pscustomobject]@{ id = 'muromachi_samurai'; file = '02_muromachi_samurai.jpg'; title = 'File:MuromachiSamurai1538.jpg' },
    [pscustomobject]@{ id = 'muromachi_ship'; file = '03_muromachi_ship.jpg'; title = 'File:MuromachiShip1538.jpg' },
    [pscustomobject]@{ id = 'rakuchu_right'; file = '04_rakuchu_right.jpg'; title = "File:Kan${macronO} Eitoku - Rakuch${macronU} rakugai zu (Uesugi) - right screen.jpg" },
    [pscustomobject]@{ id = 'rakuchu_left'; file = '05_rakuchu_left.jpg'; title = "File:Kan${macronO} Eitoku - Rakuch${macronU} rakugai zu (Uesugi) - left screen.jpg" },
    [pscustomobject]@{ id = 'rakuchu_pair'; file = '06_rakuchu_pair.jpg'; title = "File:'Rakuchu Rakugai-zu' (Scenes in and around Kyoto), pair of six-fold screens, Japanese early 17th century.jpg" },
    [pscustomobject]@{ id = 'hosokawa_katsumoto'; file = '07_hosokawa_katsumoto.jpg'; title = 'File:Hosokawa Katsumoto.jpg' },
    [pscustomobject]@{ id = 'ashikaga_yoshihisa'; file = '08_ashikaga_yoshihisa.jpg'; title = 'File:Ashikaga Yoshihisa.jpg' },
    [pscustomobject]@{ id = 'ashikaga_yoshitane'; file = '09_ashikaga_yoshitane.jpg'; title = 'File:Ashikaga Yoshitane.JPG' },
    [pscustomobject]@{ id = 'ashikaga_yoshimasa'; file = '10_ashikaga_yoshimasa.jpg'; title = 'File:Ashikaga Yoshimasa detail.jpg' },
    [pscustomobject]@{ id = 'hosokawa_masamoto'; file = '11_hosokawa_masamoto.jpg'; title = 'File:Hosokawa Masamoto.jpg' },
    [pscustomobject]@{ id = 'onin_monument'; file = '12_onin_monument.jpg'; title = "File:${macronO}nin War monument, Kamigory${macronO}-jinja.jpg" },
    [pscustomobject]@{ id = 'ashikaga_yoshimi'; file = '13_ashikaga_yoshimi.jpg'; title = 'File:Asikaga yoshimi.jpg' },
    [pscustomobject]@{ id = 'funaki_kyoto'; file = '14_funaki_kyoto.jpg'; title = 'File:Scenes in and around Kyoto Funaki 1.jpg' },
    [pscustomobject]@{ id = 'yamana_sozen'; file = '15_yamana_sozen.jpg'; title = "File:Yamana S${circO}zen.jpg" },
    [pscustomobject]@{ id = 'onin_scene3'; file = '16_onin_scene3.jpg'; title = 'File:Onin War Scene 3.jpg' },
    [pscustomobject]@{ id = 'onin_yoshitora'; file = '17_onin_yoshitora.jpg'; title = 'File:Onin Yoshitora.jpg' },
    [pscustomobject]@{ id = 'kamigoryo_shrine'; file = '18_kamigoryo_shrine.jpg'; title = "File:Kamigory${macronO}-jinja (Kamigy${macronO}-ku Kyoto) Shrine hdsr S5 04.jpg" }
)

New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null

$titles = ($specs.title -join '|')
$api = 'https://commons.wikimedia.org/w/api.php?action=query&format=json&formatversion=2&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=1920&titles=' + [uri]::EscapeDataString($titles)
$headers = @{ 'User-Agent' = 'Codex-YMM4-AssetBuilder/1.0 (personal video production)' }
$response = Invoke-RestMethod -Uri $api -Headers $headers -UseBasicParsing

$pageByTitle = @{}
foreach ($page in $response.query.pages) {
    if (-not $page.missing) {
        $pageByTitle[$page.title] = $page
    }
}

function Clean-Html([string]$value) {
    if ([string]::IsNullOrWhiteSpace($value)) { return '' }
    $plain = [regex]::Replace($value, '<[^>]+>', ' ')
    $plain = [System.Web.HttpUtility]::HtmlDecode($plain)
    return ([regex]::Replace($plain, '\s+', ' ')).Trim()
}

$assets = New-Object System.Collections.Generic.List[object]
foreach ($spec in $specs) {
    $page = $pageByTitle[$spec.title]
    if ($null -eq $page) {
        throw "Commons metadata not found: $($spec.title)"
    }
    $info = $page.imageinfo[0]
    $meta = $info.extmetadata
    $downloadUrl = if ($info.thumburl) { $info.thumburl } else { $info.url }
    $license = if ($meta.LicenseShortName) { $meta.LicenseShortName.value } else { '' }
    if ($license -notmatch 'Public domain|CC0|CC BY') {
        throw "Disallowed or unknown license for $($spec.title): $license"
    }

    $destination = Join-Path $TargetDir $spec.file
    Invoke-WebRequest -Uri $downloadUrl -Headers $headers -OutFile $destination -UseBasicParsing

    $bitmap = $null
    try {
        $bitmap = [System.Drawing.Image]::FromFile($destination)
        $width = $bitmap.Width
        $height = $bitmap.Height
    }
    finally {
        if ($bitmap) { $bitmap.Dispose() }
    }

    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $destination).Hash
    $fileInfo = Get-Item -LiteralPath $destination
    $licenseUrl = if ($meta.LicenseUrl) { $meta.LicenseUrl.value } else { '' }
    $artist = if ($meta.Artist) { Clean-Html $meta.Artist.value } else { '' }
    $credit = if ($meta.Credit) { Clean-Html $meta.Credit.value } else { '' }
    $usage = if ($meta.UsageTerms) { Clean-Html $meta.UsageTerms.value } else { '' }

    $assets.Add([pscustomobject]@{
        id = $spec.id
        title = $page.title
        file = $spec.file
        source_page = $info.descriptionurl
        download_url = $downloadUrl
        license = $license
        license_url = $licenseUrl
        artist = $artist
        credit = $credit
        usage_terms = $usage
        attribution_required = ($license -notmatch 'Public domain|CC0')
        sha256 = $hash
        bytes = $fileInfo.Length
        width = $width
        height = $height
    })
}

$manifest = [pscustomobject]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    project = 'onin-war-ai-created'
    source = 'Wikimedia Commons API'
    policy = 'Public Domain, CC0, CC BY, and CC BY-SA only'
    assets = $assets
}

$manifestPath = Join-Path (Split-Path -Parent $TargetDir) 'assets_manifest.json'
$json = $manifest | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText($manifestPath, $json, (New-Object System.Text.UTF8Encoding($true)))

$columns = 4
$cellWidth = 480
$cellHeight = 310
$rows = [math]::Ceiling($assets.Count / $columns)
$sheet = New-Object System.Drawing.Bitmap ($columns * $cellWidth), ($rows * $cellHeight)
$graphics = [System.Drawing.Graphics]::FromImage($sheet)
$graphics.Clear([System.Drawing.Color]::FromArgb(28, 28, 32))
$graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
$font = New-Object System.Drawing.Font('Yu Gothic UI', 14, [System.Drawing.FontStyle]::Bold)
$smallFont = New-Object System.Drawing.Font('Yu Gothic UI', 10, [System.Drawing.FontStyle]::Regular)
$white = [System.Drawing.Brushes]::White
$gray = [System.Drawing.Brushes]::LightGray

try {
    for ($i = 0; $i -lt $assets.Count; $i++) {
        $asset = $assets[$i]
        $x = ($i % $columns) * $cellWidth
        $y = [math]::Floor($i / $columns) * $cellHeight
        $imagePath = Join-Path $TargetDir $asset.file
        $img = [System.Drawing.Image]::FromFile($imagePath)
        try {
            $maxW = $cellWidth - 20
            $maxH = 230
            $scale = [math]::Min($maxW / $img.Width, $maxH / $img.Height)
            $drawW = [int]($img.Width * $scale)
            $drawH = [int]($img.Height * $scale)
            $drawX = $x + [int](($cellWidth - $drawW) / 2)
            $drawY = $y + 8 + [int](($maxH - $drawH) / 2)
            $graphics.DrawImage($img, $drawX, $drawY, $drawW, $drawH)
        }
        finally {
            $img.Dispose()
        }
        $graphics.DrawString(('{0:D2}  {1}' -f ($i + 1), $asset.id), $font, $white, $x + 10, $y + 242)
        $graphics.DrawString($asset.license, $smallFont, $gray, $x + 10, $y + 275)
    }
    $contactPath = Join-Path (Split-Path -Parent $TargetDir) 'external_contact_sheet.jpg'
    $sheet.Save($contactPath, [System.Drawing.Imaging.ImageFormat]::Jpeg)
}
finally {
    $font.Dispose()
    $smallFont.Dispose()
    $graphics.Dispose()
    $sheet.Dispose()
}

[pscustomobject]@{
    asset_count = $assets.Count
    manifest = $manifestPath
    contact_sheet = $contactPath
    total_bytes = (($assets | Measure-Object -Property bytes -Sum).Sum)
} | ConvertTo-Json -Compress
