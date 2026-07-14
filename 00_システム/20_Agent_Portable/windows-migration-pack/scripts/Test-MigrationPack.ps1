[CmdletBinding()]
param(
    [string]$PackRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
$manifestPath = Join-Path $PackRoot 'pack.manifest.sha256'

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    Write-Error "Manifest not found: $manifestPath"
    exit 2
}

$rootFull = [System.IO.Path]::GetFullPath($PackRoot).TrimEnd('\')
$expected = @{}
$failures = New-Object System.Collections.Generic.List[string]

foreach ($line in Get-Content -LiteralPath $manifestPath -Encoding UTF8) {
    if ([string]::IsNullOrWhiteSpace($line)) {
        continue
    }
    if ($line -notmatch '^([A-Fa-f0-9]{64})  (.+)$') {
        $failures.Add("Invalid manifest line: $line")
        continue
    }
    $hash = $Matches[1].ToUpperInvariant()
    $relative = $Matches[2].Replace('/', '\')
    if ($relative -eq 'pack.manifest.sha256') {
        $failures.Add('Manifest must not include itself.')
        continue
    }
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $rootFull $relative))
    if (-not $candidate.StartsWith($rootFull + '\', [System.StringComparison]::OrdinalIgnoreCase)) {
        $failures.Add("Path escapes pack root: $relative")
        continue
    }
    if ($expected.ContainsKey($relative)) {
        $failures.Add("Duplicate manifest path: $relative")
        continue
    }
    $expected[$relative] = $hash
}

foreach ($relative in $expected.Keys | Sort-Object) {
    $path = Join-Path $rootFull $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $failures.Add("Missing: $relative")
        continue
    }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actual -ne $expected[$relative]) {
        $failures.Add("SHA mismatch: $relative")
    }
}

$actualFiles = Get-ChildItem -LiteralPath $rootFull -File -Recurse |
    ForEach-Object { $_.FullName.Substring($rootFull.Length + 1) } |
    Where-Object { $_ -ne 'pack.manifest.sha256' }

foreach ($relative in $actualFiles) {
    if (-not $expected.ContainsKey($relative)) {
        $failures.Add("Unexpected file: $relative")
    }
}

if ($failures.Count -gt 0) {
    Write-Host 'MIGRATION_PACK_VERIFY: FAIL' -ForegroundColor Red
    $failures | ForEach-Object { Write-Host " - $_" }
    exit 2
}

Write-Host "MIGRATION_PACK_VERIFY: PASS ($($expected.Count) files)" -ForegroundColor Green
exit 0

