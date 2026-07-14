[CmdletBinding()]
param(
    [string]$ReportPath,
    [switch]$SkipRemote
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($ReportPath)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $ReportPath = "C:\Migration-Work\reports\post-clone-$stamp.json"
}

$git = Get-Command git -ErrorAction SilentlyContinue | Select-Object -First 1
if ($null -eq $git) {
    Write-Error 'Git is not installed or not in PATH.'
    exit 3
}

$repos = @(
    [pscustomobject]@{
        name = '2nd-Brain-master'
        path = (Join-Path $env:USERPROFILE '2nd-Brain-master')
        remote = 'git@github.com:corocorobusiness-oss/2nd-brain.git'
        required = @('AGENTS.md', '00_システム\10_Agent\persona.md', '06_エージェント運用\00_司令塔\NOW.md')
    },
    [pscustomobject]@{
        name = 'youtube'
        path = (Join-Path $env:USERPROFILE 'Projects\youtube')
        remote = 'git@github.com:corocorobusiness-oss/youtube-work.git'
        required = @('ymm4-builder', 'asset-pipeline')
    },
    [pscustomobject]@{
        name = 'agent-skills'
        path = (Join-Path $env:USERPROFILE 'agent-skills')
        remote = 'git@github.com:corocorobusiness-oss/agent-skills.git'
        required = @('ymm4-project-builder\SKILL.md')
    },
    [pscustomobject]@{
        name = 'agent-adapters'
        path = (Join-Path $env:USERPROFILE 'agent-adapters')
        remote = 'git@github.com:corocorobusiness-oss/agent-adapters.git'
        required = @('bin\agent-run')
    }
)

$forbiddenPatterns = @(
    '(^|/)\.env$',
    '(^|/)auth\.json$',
    '(^|/)tokens?\.json$',
    '(^|/)client_secret\.json$',
    '\.sqlite([0-9-]*)?$',
    '(^|/)history\.jsonl$',
    '(^|/)\.venv/',
    '(^|/)__pycache__/',
    '\.pyc$'
)

$results = @()
foreach ($repo in $repos) {
    $issues = New-Object System.Collections.Generic.List[string]
    $localHead = $null
    $remoteHead = $null
    $origin = $null
    $dirtyCount = $null

    if (-not (Test-Path -LiteralPath $repo.path -PathType Container)) {
        $issues.Add('Repository folder missing.')
    }
    elseif (-not (Test-Path -LiteralPath (Join-Path $repo.path '.git'))) {
        $issues.Add('Not a Git worktree.')
    }
    else {
        $localHead = (& git -C $repo.path rev-parse HEAD 2>$null | Select-Object -First 1)
        if ($LASTEXITCODE -ne 0) {
            $issues.Add('Cannot read local HEAD.')
        }

        $origin = (& git -C $repo.path remote get-url origin 2>$null | Select-Object -First 1)
        if ($LASTEXITCODE -ne 0) {
            $issues.Add('Cannot read origin URL.')
        }
        elseif ($origin -ne $repo.remote) {
            $issues.Add("Unexpected origin: $origin")
        }

        $dirty = @(& git -C $repo.path status --porcelain --untracked-files=all)
        if ($LASTEXITCODE -ne 0) {
            $issues.Add('git status failed.')
        }
        else {
            $dirtyCount = $dirty.Count
            if ($dirtyCount -gt 0) {
                $issues.Add("Worktree is dirty: $dirtyCount entries.")
            }
        }

        foreach ($required in $repo.required) {
            if (-not (Test-Path -LiteralPath (Join-Path $repo.path $required))) {
                $issues.Add("Required path missing: $required")
            }
        }

        $tracked = @(& git -C $repo.path ls-files)
        if ($LASTEXITCODE -ne 0) {
            $issues.Add('git ls-files failed.')
        }
        else {
            foreach ($trackedPath in $tracked) {
                $normalized = $trackedPath.Replace('\', '/')
                foreach ($pattern in $forbiddenPatterns) {
                    if ($normalized -match $pattern) {
                        $issues.Add("Forbidden tracked path: $trackedPath")
                        break
                    }
                }
            }
        }

        if (-not $SkipRemote) {
            $remoteLine = (& git ls-remote $repo.remote refs/heads/main 2>$null | Select-Object -First 1)
            if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($remoteLine)) {
                $issues.Add('Cannot read remote main with git ls-remote.')
            }
            else {
                $remoteHead = ($remoteLine -split '\s+')[0]
                if ($localHead -ne $remoteHead) {
                    $issues.Add("Local HEAD does not equal remote main. local=$localHead remote=$remoteHead")
                }
            }
        }
    }

    $results += [pscustomobject]@{
        name = $repo.name
        path = $repo.path
        expected_remote = $repo.remote
        actual_origin = $origin
        local_head = $localHead
        remote_main = $remoteHead
        dirty_count = $dirtyCount
        status = if ($issues.Count -eq 0) { 'PASS' } else { 'FAIL' }
        issues = @($issues)
    }
}

$failCount = @($results | Where-Object status -eq 'FAIL').Count
$overall = if ($failCount -eq 0) { 'PASS' } else { 'FAIL' }
$report = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString('o')
    overall_status = $overall
    skip_remote = [bool]$SkipRemote
    repositories = $results
}

New-Item -ItemType Directory -Path (Split-Path -Parent $ReportPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ReportPath -Encoding UTF8

$results | Select-Object name, status, dirty_count, local_head, remote_main | Format-Table -AutoSize
Write-Host "POST_CLONE_VERIFY: $overall"
Write-Host "Report: $ReportPath"

if ($overall -eq 'FAIL') {
    exit 2
}
exit 0
