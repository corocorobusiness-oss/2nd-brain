[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [Parameter(Mandatory = $true)][string]$Destination,
    [switch]$Apply,
    [switch]$Resume,
    [string]$LogPath
)

$ErrorActionPreference = 'Stop'

if (-not $Source.StartsWith('\\')) {
    throw 'Source must be an SMB UNC path such as \\192.168.1.10\Share.'
}
if ($Destination.StartsWith('\\')) {
    throw 'Destination must be Windows local storage, not UNC.'
}
if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Source folder not found: $Source"
}

$destinationFull = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
$destinationRoot = [System.IO.Path]::GetPathRoot($destinationFull).TrimEnd('\')
if ($destinationFull -eq $destinationRoot) {
    throw 'Destination cannot be a drive root.'
}

$disk = Get-CimInstance Win32_LogicalDisk |
    Where-Object { $_.DeviceID -eq $destinationRoot } |
    Select-Object -First 1
if ($null -eq $disk) {
    throw "Destination drive not found: $destinationRoot"
}
if ($disk.DriveType -ne 3) {
    throw 'Destination drive must be fixed local storage. Assign a fixed drive letter to a Windows asset SSD before use.'
}
if ($disk.FileSystem -ne 'NTFS') {
    throw "Destination drive must be NTFS for this migration workflow. Found: $($disk.FileSystem)"
}

if (Test-Path -LiteralPath $destinationFull -PathType Container) {
    $hasContent = $null -ne (Get-ChildItem -LiteralPath $destinationFull -Force | Select-Object -First 1)
    if ($hasContent -and -not $Resume) {
        throw 'Destination is not empty. Use a new versioned destination, or explicitly use -Resume for an interrupted copy.'
    }
}
elseif (Test-Path -LiteralPath $destinationFull) {
    throw "A file exists at destination: $destinationFull"
}

if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $LogPath = "C:\Migration-Work\reports\robocopy-$stamp.log"
}
if ($LogPath.StartsWith('\\')) {
    throw 'LogPath must be local.'
}

$arguments = @(
    $Source,
    $destinationFull,
    '/E',
    '/Z',
    '/J',
    '/R:2',
    '/W:3',
    '/COPY:DAT',
    '/DCOPY:DAT',
    '/XJ',
    '/FFT',
    '/MT:8',
    '/NP',
    '/TEE',
    "/LOG:$LogPath"
)

Write-Host "Source:      $Source"
Write-Host "Destination: $destinationFull"
Write-Host "Log:         $LogPath"
Write-Host 'Robocopy mode: copy only. No MIR, PURGE, MOVE, or source deletion.'

if (-not $Apply) {
    Write-Host ''
    Write-Host 'PLAN_ONLY: robocopy was not executed. Re-run with -Apply after approval.'
    exit 0
}

New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
if (-not (Test-Path -LiteralPath $destinationFull)) {
    New-Item -ItemType Directory -Path $destinationFull | Out-Null
}

& robocopy.exe @arguments
$robocopyExit = $LASTEXITCODE

$reportPath = [System.IO.Path]::ChangeExtension($LogPath, '.json')
$destinationMeasure = Get-ChildItem -LiteralPath $destinationFull -File -Recurse -Force |
    Measure-Object -Property Length -Sum
$report = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    source = $Source
    destination = $destinationFull
    robocopy_exit_code = $robocopyExit
    robocopy_success_range = '0-7'
    destination_files = $destinationMeasure.Count
    destination_bytes = $destinationMeasure.Sum
    log_path = $LogPath
    source_modified = false
    destructive_options_used = false
}
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($robocopyExit -ge 8) {
    Write-Host "COPY_FROM_MAC_SHARE: FAIL (robocopy exit $robocopyExit)" -ForegroundColor Red
    Write-Host "Report: $reportPath"
    exit 2
}

Write-Host "COPY_FROM_MAC_SHARE: PASS (robocopy exit $robocopyExit)" -ForegroundColor Green
Write-Host "Report: $reportPath"
Write-Host 'Next: verify the transport or asset manifest before opening any YMM4 project.'
exit 0

