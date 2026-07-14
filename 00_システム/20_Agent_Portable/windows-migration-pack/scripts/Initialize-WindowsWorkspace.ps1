[CmdletBinding()]
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

$directories = @(
    'C:\Migration-Work',
    'C:\Migration-Work\local',
    'C:\Migration-Work\reports',
    'C:\Transfer',
    (Join-Path $env:USERPROFILE 'Projects'),
    'C:\YMM4-Jobs',
    'C:\YMM4-Assets',
    'C:\Tools\YMM4-AI',
    'C:\Dev\YMM4-AI'
)

function Test-LocalTarget {
    param([string]$Path)

    if ($Path.StartsWith('\\')) {
        throw "UNC target is forbidden: $Path"
    }
    $full = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetPathRoot($full)
    $disk = Get-CimInstance Win32_LogicalDisk |
        Where-Object { $_.DeviceID -eq $root.TrimEnd('\') } |
        Select-Object -First 1
    if ($null -eq $disk) {
        throw "Target drive not found: $root"
    }
    if ($disk.DriveType -ne 3) {
        throw "Target is not a fixed local disk: $Path"
    }
    if ($disk.FileSystem -ne 'NTFS') {
        throw "Target drive is not NTFS: $Path ($($disk.FileSystem))"
    }
}

foreach ($path in $directories) {
    Test-LocalTarget $path
}

Write-Host 'Planned directories:'
$directories | ForEach-Object {
    $state = if (Test-Path -LiteralPath $_) { 'EXISTS' } else { 'CREATE' }
    Write-Host " [$state] $_"
}

Write-Host ''
Write-Host 'Repository leaf directories are intentionally not created by this script.'
Write-Host 'Git will clone them into empty local targets later.'

if (-not $Apply) {
    Write-Host ''
    Write-Host 'PLAN_ONLY: no directories were created. Re-run with -Apply after approval.'
    exit 0
}

foreach ($path in $directories) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        throw "A file blocks the directory path: $path"
    }
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        New-Item -ItemType Directory -Path $path | Out-Null
        Write-Host "CREATED: $path"
    }
    else {
        Write-Host "UNCHANGED: $path"
    }
}

Write-Host 'INITIALIZE_WINDOWS_WORKSPACE: PASS'
exit 0

