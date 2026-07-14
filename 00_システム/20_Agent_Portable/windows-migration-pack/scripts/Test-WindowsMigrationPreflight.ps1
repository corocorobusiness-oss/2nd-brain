[CmdletBinding()]
param(
    [string]$ReportPath,
    [int]$MinimumFreeGB = 50,
    [int]$RecommendedFreeGB = 100
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $ReportPath = "C:\Migration-Work\reports\windows-preflight-$stamp.json"
}

if ($ReportPath.StartsWith('\\')) {
    Write-Error 'ReportPath must be on Windows local storage, not UNC.'
    exit 3
}

$checks = New-Object System.Collections.Generic.List[object]

function Add-Check {
    param(
        [string]$Name,
        [ValidateSet('PASS', 'WARN', 'FAIL')][string]$Status,
        [string]$Evidence
    )
    $checks.Add([pscustomobject]@{
        name = $Name
        status = $Status
        evidence = $Evidence
    })
}

try {
    $os = Get-CimInstance Win32_OperatingSystem
    $computer = Get-CimInstance Win32_ComputerSystem
    $cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
    $gpus = @(Get-CimInstance Win32_VideoController | ForEach-Object {
        [pscustomobject]@{
            name = $_.Name
            adapter_ram_bytes = $_.AdapterRAM
            driver_version = $_.DriverVersion
        }
    })
    $systemDisk = Get-CimInstance Win32_LogicalDisk |
        Where-Object { $_.DeviceID -eq $env:SystemDrive } |
        Select-Object -First 1
}
catch {
    Write-Error "Hardware inspection failed: $($_.Exception.Message)"
    exit 3
}

if ($os.Caption -match 'Windows 11') {
    Add-Check 'operating_system' 'PASS' "$($os.Caption) build $($os.BuildNumber)"
}
else {
    Add-Check 'operating_system' 'FAIL' "$($os.Caption) build $($os.BuildNumber)"
}

$ramGB = [math]::Round($computer.TotalPhysicalMemory / 1GB, 1)
if ($ramGB -ge 16) {
    Add-Check 'memory' 'PASS' "$ramGB GB"
}
elseif ($ramGB -ge 8) {
    Add-Check 'memory' 'WARN' "$ramGB GB; 16 GB or more is recommended for YMM4 and development."
}
else {
    Add-Check 'memory' 'FAIL' "$ramGB GB"
}

if ($null -eq $systemDisk) {
    Add-Check 'system_disk' 'FAIL' "Cannot inspect $env:SystemDrive"
    $freeGB = 0
}
else {
    $freeGB = [math]::Round($systemDisk.FreeSpace / 1GB, 1)
    if ($systemDisk.DriveType -ne 3) {
        Add-Check 'system_disk_type' 'FAIL' "$($systemDisk.DeviceID) is not a fixed local disk."
    }
    elseif ($systemDisk.FileSystem -ne 'NTFS') {
        Add-Check 'system_disk_type' 'FAIL' "$($systemDisk.DeviceID) uses $($systemDisk.FileSystem), not NTFS."
    }
    else {
        Add-Check 'system_disk_type' 'PASS' "$($systemDisk.DeviceID) NTFS fixed disk"
    }

    if ($freeGB -ge $RecommendedFreeGB) {
        Add-Check 'system_disk_free' 'PASS' "$freeGB GB free"
    }
    elseif ($freeGB -ge $MinimumFreeGB) {
        Add-Check 'system_disk_free' 'WARN' "$freeGB GB free; $RecommendedFreeGB GB recommended."
    }
    else {
        Add-Check 'system_disk_free' 'FAIL' "$freeGB GB free; minimum policy is $MinimumFreeGB GB."
    }
}

$commandNames = @(
    'winget',
    'git',
    'pwsh',
    'powershell',
    'python',
    'py',
    'node',
    'ffmpeg',
    'ffprobe',
    'wsl',
    'robocopy'
)
$commands = @()
foreach ($name in $commandNames) {
    $command = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
    $commands += [pscustomobject]@{
        name = $name
        found = ($null -ne $command)
        path = if ($null -ne $command) { $command.Source } else { $null }
    }
}

foreach ($required in @('powershell', 'robocopy')) {
    $found = $commands | Where-Object { $_.name -eq $required -and $_.found }
    if ($found) {
        Add-Check "command_$required" 'PASS' $found.path
    }
    else {
        Add-Check "command_$required" 'FAIL' 'Not found'
    }
}

foreach ($optional in @('winget', 'git', 'pwsh', 'python', 'node', 'ffmpeg', 'ffprobe', 'wsl')) {
    $found = $commands | Where-Object { $_.name -eq $optional -and $_.found }
    if ($found) {
        Add-Check "command_$optional" 'PASS' $found.path
    }
    else {
        Add-Check "command_$optional" 'WARN' 'Not installed or not in PATH.'
    }
}

$oneDrive = $env:OneDrive
if ([string]::IsNullOrWhiteSpace($oneDrive)) {
    Add-Check 'cloud_sync_root' 'PASS' 'OneDrive environment path not detected.'
}
else {
    Add-Check 'cloud_sync_root' 'WARN' "Do not place repositories or YMM4 jobs under $oneDrive"
}

$failCount = @($checks | Where-Object status -eq 'FAIL').Count
$warnCount = @($checks | Where-Object status -eq 'WARN').Count
$overall = if ($failCount -gt 0) { 'FAIL' } elseif ($warnCount -gt 0) { 'WARN' } else { 'PASS' }

$report = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    overall_status = $overall
    fail_count = $failCount
    warn_count = $warnCount
    machine = [ordered]@{
        computer_name = $env:COMPUTERNAME
        os_caption = $os.Caption
        os_build = $os.BuildNumber
        os_architecture = $os.OSArchitecture
        processor_architecture = $env:PROCESSOR_ARCHITECTURE
        system_type = $computer.SystemType
        cpu = $cpu.Name
        logical_processors = $computer.NumberOfLogicalProcessors
        ram_gb = $ramGB
        system_drive = $env:SystemDrive
        system_drive_file_system = if ($systemDisk) { $systemDisk.FileSystem } else { $null }
        system_drive_free_gb = $freeGB
        gpu = $gpus
    }
    commands = $commands
    checks = $checks
}

$reportDirectory = Split-Path -Parent $ReportPath
New-Item -ItemType Directory -Path $reportDirectory -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

$checks | Format-Table -AutoSize
Write-Host "WINDOWS_MIGRATION_PREFLIGHT: $overall"
Write-Host "Report: $ReportPath"

if ($overall -eq 'FAIL') {
    exit 2
}
exit 0

