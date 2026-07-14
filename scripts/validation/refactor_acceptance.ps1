param(
    [Parameter(Mandatory = $true)]
    [string]$BaselineSha,

    [string]$CurrentRef = "HEAD",

    [switch]$Frontend,
    [switch]$Backend,
    [switch]$Cleanup,
    [switch]$SkipExecution,

    [string]$WorktreeRoot = ".tmp\refactor_acceptance_worktrees",
    [string]$SummaryPath = ""
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $root = (& git rev-parse --show-toplevel).Trim()
    if (-not $root) {
        throw "Unable to resolve git repository root."
    }
    return $root
}

function Invoke-LoggedCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string]$LogPath
    )

    Write-Host "[$Name] $Command"
    Write-Host "[$Name] cwd: $WorkingDirectory"

    if ($SkipExecution) {
        "SKIPPED: $Command" | Set-Content -Path $LogPath -Encoding UTF8
        return 0
    }

    Push-Location $WorkingDirectory
    try {
        $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
        $exitCode = $LASTEXITCODE
        $output | Set-Content -Path $LogPath -Encoding UTF8
        return $exitCode
    }
    finally {
        Pop-Location
    }
}

function Get-FailedTests {
    param([string]$LogPath)

    if (-not (Test-Path $LogPath)) {
        return @()
    }

    $failed = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($line in Get-Content -Path $LogPath) {
        if ($line -match "FAILED\s+(.+?)(?:\s+-\s+|\s+\[|\s*$)") {
            [void]$failed.Add($Matches[1].Trim())
        }
        elseif ($line -match "^\s*(.+?::.+?)\s+FAILED\s*$") {
            [void]$failed.Add($Matches[1].Trim())
        }
        elseif ($line -match "FAIL\s+(.+\.(?:test|spec)\.[jt]sx?)") {
            [void]$failed.Add($Matches[1].Trim())
        }
    }
    return @($failed | Sort-Object)
}

function Compare-FailureSets {
    param(
        [string[]]$BaselineFailures,
        [string[]]$CurrentFailures
    )

    $baselineSet = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($failure in $BaselineFailures) {
        [void]$baselineSet.Add($failure)
    }
    $currentSet = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($failure in $CurrentFailures) {
        [void]$currentSet.Add($failure)
    }

    $newRegressions = @()
    foreach ($failure in $CurrentFailures) {
        if (-not $baselineSet.Contains($failure)) {
            $newRegressions += $failure
        }
    }

    $fixedExisting = @()
    foreach ($failure in $BaselineFailures) {
        if (-not $currentSet.Contains($failure)) {
            $fixedExisting += $failure
        }
    }

    return [pscustomobject]@{
        NewRegressions = $newRegressions
        FixedExisting = $fixedExisting
    }
}

function Copy-EnvironmentFiles {
    param(
        [string]$SourceRoot,
        [string]$TargetRoot
    )

    $candidates = @(
        ".env",
        "backend\.env",
        "frontend\.env",
        "frontend\.env.local"
    )

    foreach ($relative in $candidates) {
        $source = Join-Path $SourceRoot $relative
        $target = Join-Path $TargetRoot $relative
        if (Test-Path $source) {
            $targetDir = Split-Path $target -Parent
            if (-not (Test-Path $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
            }
            Copy-Item -Path $source -Destination $target -Force
            Write-Host "[env] copied $relative"
        }
    }
}

function Ensure-Worktree {
    param(
        [string]$RepoRoot,
        [string]$Ref,
        [string]$Path
    )

    if (Test-Path $Path) {
        Write-Host "[worktree] reusing $Path"
        return
    }

    $parent = Split-Path $Path -Parent
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }

    Push-Location $RepoRoot
    try {
        & git worktree add --detach $Path $Ref
        if ($LASTEXITCODE -ne 0) {
            throw "git worktree add failed for $Ref at $Path"
        }
    }
    finally {
        Pop-Location
    }
}

function Remove-WorktreeIfRequested {
    param(
        [string]$RepoRoot,
        [string]$Path
    )

    if (-not $Cleanup) {
        return
    }

    if (Test-Path $Path) {
        Push-Location $RepoRoot
        try {
            & git worktree remove --force $Path
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "git worktree remove failed for $Path"
            }
        }
        finally {
            Pop-Location
        }
    }
}

if (-not $Frontend -and -not $Backend) {
    $Frontend = $true
    $Backend = $true
}

$repoRoot = Resolve-RepoRoot
if (-not [System.IO.Path]::IsPathRooted($WorktreeRoot)) {
    $WorktreeRoot = Join-Path $repoRoot $WorktreeRoot
}
$logsRoot = Join-Path $repoRoot ".tmp\refactor_acceptance"
New-Item -ItemType Directory -Path $logsRoot -Force | Out-Null

if (-not $SummaryPath) {
    $SummaryPath = Join-Path $logsRoot "summary.md"
}

$baselinePath = Join-Path $WorktreeRoot "baseline-$BaselineSha"
$currentPath = Join-Path $WorktreeRoot "current-$($CurrentRef -replace '[\\/:*?""<>|]', '_')"

Ensure-Worktree -RepoRoot $repoRoot -Ref $BaselineSha -Path $baselinePath
Ensure-Worktree -RepoRoot $repoRoot -Ref $CurrentRef -Path $currentPath
Copy-EnvironmentFiles -SourceRoot $repoRoot -TargetRoot $baselinePath
Copy-EnvironmentFiles -SourceRoot $repoRoot -TargetRoot $currentPath

$results = @()

if ($Backend) {
    $baselineBackendLog = Join-Path $logsRoot "baseline-backend.log"
    $currentBackendLog = Join-Path $logsRoot "current-backend.log"

    $baselineCode = Invoke-LoggedCommand -Name "baseline backend" -WorkingDirectory (Join-Path $baselinePath "backend") -Command "python -m pytest" -LogPath $baselineBackendLog
    $currentCode = Invoke-LoggedCommand -Name "current backend" -WorkingDirectory (Join-Path $currentPath "backend") -Command "python -m pytest" -LogPath $currentBackendLog

    $baselineFailures = Get-FailedTests $baselineBackendLog
    $currentFailures = Get-FailedTests $currentBackendLog
    $comparison = Compare-FailureSets -BaselineFailures $baselineFailures -CurrentFailures $currentFailures

    $results += [pscustomobject]@{
        Area = "backend"
        BaselineExitCode = $baselineCode
        CurrentExitCode = $currentCode
        BaselineFailures = $baselineFailures
        CurrentFailures = $currentFailures
        NewRegressions = $comparison.NewRegressions
        FixedExisting = $comparison.FixedExisting
    }
}

if ($Frontend) {
    $baselineFrontendLog = Join-Path $logsRoot "baseline-frontend.log"
    $currentFrontendLog = Join-Path $logsRoot "current-frontend.log"
    $baselineBuildLog = Join-Path $logsRoot "baseline-frontend-build.log"
    $currentBuildLog = Join-Path $logsRoot "current-frontend-build.log"

    $baselineCode = Invoke-LoggedCommand -Name "baseline frontend test" -WorkingDirectory (Join-Path $baselinePath "frontend") -Command "npx vitest run" -LogPath $baselineFrontendLog
    $currentCode = Invoke-LoggedCommand -Name "current frontend test" -WorkingDirectory (Join-Path $currentPath "frontend") -Command "npx vitest run" -LogPath $currentFrontendLog
    $baselineBuildCode = Invoke-LoggedCommand -Name "baseline frontend build" -WorkingDirectory (Join-Path $baselinePath "frontend") -Command "npm run build" -LogPath $baselineBuildLog
    $currentBuildCode = Invoke-LoggedCommand -Name "current frontend build" -WorkingDirectory (Join-Path $currentPath "frontend") -Command "npm run build" -LogPath $currentBuildLog

    $baselineFailures = Get-FailedTests $baselineFrontendLog
    $currentFailures = Get-FailedTests $currentFrontendLog
    $comparison = Compare-FailureSets -BaselineFailures $baselineFailures -CurrentFailures $currentFailures

    $results += [pscustomobject]@{
        Area = "frontend"
        BaselineExitCode = $baselineCode
        CurrentExitCode = $currentCode
        BaselineBuildExitCode = $baselineBuildCode
        CurrentBuildExitCode = $currentBuildCode
        BaselineFailures = $baselineFailures
        CurrentFailures = $currentFailures
        NewRegressions = $comparison.NewRegressions
        FixedExisting = $comparison.FixedExisting
    }
}

$summary = [System.Collections.Generic.List[string]]::new()
$summary.Add("# Refactor Acceptance Summary")
$summary.Add("")
$summary.Add("- Baseline: ``$BaselineSha``")
$summary.Add("- Current: ``$CurrentRef``")
$summary.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$summary.Add("- SkipExecution: ``$SkipExecution``")
$summary.Add("")

foreach ($result in $results) {
    $summary.Add("## $($result.Area)")
    $summary.Add("")
    $summary.Add("- Baseline exit code: ``$($result.BaselineExitCode)``")
    $summary.Add("- Current exit code: ``$($result.CurrentExitCode)``")
    if ($null -ne $result.BaselineBuildExitCode) {
        $summary.Add("- Baseline build exit code: ``$($result.BaselineBuildExitCode)``")
        $summary.Add("- Current build exit code: ``$($result.CurrentBuildExitCode)``")
    }
    $summary.Add("")
    $summary.Add("### Baseline Failed Tests")
    if ($result.BaselineFailures.Count) {
        foreach ($failure in $result.BaselineFailures) { $summary.Add("- $failure") }
    } else {
        $summary.Add("- None")
    }
    $summary.Add("")
    $summary.Add("### Current Failed Tests")
    if ($result.CurrentFailures.Count) {
        foreach ($failure in $result.CurrentFailures) { $summary.Add("- $failure") }
    } else {
        $summary.Add("- None")
    }
    $summary.Add("")
    $summary.Add("### New Regressions")
    if ($result.NewRegressions.Count) {
        foreach ($failure in $result.NewRegressions) { $summary.Add("- $failure") }
    } else {
        $summary.Add("- None")
    }
    $summary.Add("")
    $summary.Add("### Fixed Existing Failures")
    if ($result.FixedExisting.Count) {
        foreach ($failure in $result.FixedExisting) { $summary.Add("- $failure") }
    } else {
        $summary.Add("- None")
    }
    $summary.Add("")
    $summary.Add("### Not-Run Reason")
    if ($SkipExecution) {
        $summary.Add("- Commands were not executed because `-SkipExecution` was provided.")
    } else {
        $summary.Add("- None")
    }
    $summary.Add("")
}

$summaryDir = Split-Path $SummaryPath -Parent
if ($summaryDir -and -not (Test-Path $summaryDir)) {
    New-Item -ItemType Directory -Path $summaryDir -Force | Out-Null
}
$summary | Set-Content -Path $SummaryPath -Encoding UTF8
Write-Host "[summary] $SummaryPath"
Get-Content -Path $SummaryPath

$hasNewRegression = $false
foreach ($result in $results) {
    if ($result.NewRegressions.Count -gt 0) {
        $hasNewRegression = $true
    }
    if ($result.BaselineExitCode -eq 0 -and $result.CurrentExitCode -ne 0) {
        $hasNewRegression = $true
    }
    if ($null -ne $result.BaselineBuildExitCode -and $result.BaselineBuildExitCode -eq 0 -and $result.CurrentBuildExitCode -ne 0) {
        $hasNewRegression = $true
    }
}

Remove-WorktreeIfRequested -RepoRoot $repoRoot -Path $baselinePath
Remove-WorktreeIfRequested -RepoRoot $repoRoot -Path $currentPath

if ($hasNewRegression) {
    Write-Error "Refactor acceptance found new regressions. See $SummaryPath"
    exit 1
}
