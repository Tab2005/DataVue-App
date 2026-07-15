<#
.SYNOPSIS
    Recompute the file/line-count stats behind docs/31 (project source layout analysis),
    replacing the earlier ad-hoc "equivalent process" that had no committed script.

.DESCRIPTION
    Lists every tracked-or-untracked-but-not-ignored file via
    `git ls-files --cached --others --exclude-standard`, keeps only core source
    extensions (.py .js .jsx .ts .tsx .css .ps1), and excludes docs/, node_modules/,
    dist/, .tmp/, .vite/, cache dirs, and lockfiles. Buckets the result into
    backend / frontend / root-scripts and reports file counts + line counts per
    bucket plus the largest files overall, so docs/31 can be regenerated from a
    single reproducible command instead of manual recounting.

.PARAMETER Top
    How many of the largest files to list (default 40) — feeds the "large file
    split status" table in docs/31.

.PARAMETER OutFile
    If given, writes a Markdown report (overview table + top-N table) to this
    path so it can be pasted directly into docs/31.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts/validation/source_stats.ps1
    powershell -ExecutionPolicy Bypass -File scripts/validation/source_stats.ps1 -Top 60 -OutFile .tmp/source_stats.md
#>

param(
    [int]$Top = 40,
    [string]$OutFile
)

$ErrorActionPreference = "Stop"

$repoRoot = (git rev-parse --show-toplevel).Trim()
Push-Location $repoRoot
try {
    $codeExtensions = @('py', 'js', 'jsx', 'ts', 'tsx', 'css', 'ps1')
    $excludePatterns = @(
        '^docs/',
        'node_modules/',
        '(^|/)dist/',
        '(^|/)\.tmp/',
        '(^|/)\.vite/',
        '(^|/)cache/',
        'package-lock\.json$',
        '\.lock$',
        '\.lockb$'
    )

    $allFiles = git -c core.quotepath=false ls-files --cached --others --exclude-standard

    $extPattern = '\.(' + ($codeExtensions -join '|') + ')$'
    $files = $allFiles | Where-Object {
        $path = $_
        if ($path -notmatch $extPattern) { return $false }
        foreach ($pattern in $excludePatterns) {
            if ($path -match $pattern) { return $false }
        }
        return $true
    }

    function Get-LineCount([string]$path) {
        # NOTE: `Get-Content file | Measure-Object -Line` silently undercounts large
        # files (observed ~300 lines short on a 3,700-line file) due to a pipeline
        # quirk. Read raw text and split on newlines instead, to match `wc -l`.
        # Force UTF8 explicitly: default encoding detection is host-dependent and
        # has been observed to misdecode BOM-less UTF8 files with CJK content
        # under Windows PowerShell 5.1, silently undercounting lines.
        $raw = Get-Content -LiteralPath $path -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($null -eq $raw -or $raw -eq '') { return 0 }
        $parts = $raw -split "`r?`n"
        $count = $parts.Count
        if ($parts[$count - 1] -eq '') { $count -= 1 }
        return $count
    }

    $rows = foreach ($f in $files) {
        if (-not (Test-Path -LiteralPath $f)) { continue }
        [pscustomobject]@{
            Path  = $f
            Lines = Get-LineCount $f
        }
    }

    function Get-Bucket($path) {
        if ($path -like 'backend/*') { return 'backend' }
        if ($path -like 'frontend/*') { return 'frontend' }
        return 'root/scripts'
    }

    $bucketed = $rows | Group-Object { Get-Bucket $_.Path } | ForEach-Object {
        [pscustomobject]@{
            Bucket = $_.Name
            Files  = $_.Count
            Lines  = ($_.Group | Measure-Object -Property Lines -Sum).Sum
        }
    }

    $totalFiles = $rows.Count
    $totalLines = ($rows | Measure-Object -Property Lines -Sum).Sum

    Write-Host ""
    Write-Host "== Overall stats =="
    Write-Host "Total files: $totalFiles"
    Write-Host "Total lines: $totalLines"
    Write-Host ""
    Write-Host "== By bucket =="
    $bucketed | Sort-Object -Property Lines -Descending | ForEach-Object {
        $pct = if ($totalLines -gt 0) { [math]::Round(100.0 * $_.Lines / $totalLines, 1) } else { 0 }
        Write-Host ("{0,-15} files {1,5}  lines {2,7}  share {3,5}%" -f $_.Bucket, $_.Files, $_.Lines, $pct)
    }

    $topFiles = $rows | Sort-Object -Property Lines -Descending | Select-Object -First $Top
    Write-Host ""
    Write-Host "== Top $Top largest files =="
    $topFiles | ForEach-Object { Write-Host ("{0,6}  {1}" -f $_.Lines, $_.Path) }

    if ($OutFile) {
        $outDir = Split-Path -Parent $OutFile
        if ($outDir -and -not (Test-Path $outDir)) {
            New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        }
        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add("- Generated: $(Get-Date -Format 'yyyy-MM-dd')")
        $extList = $codeExtensions -join ', '
        $lines.Add("- Source: ``scripts/validation/source_stats.ps1`` (``git ls-files --cached --others --exclude-standard``, extensions: $extList; excludes docs/, node_modules/, dist/, .tmp/, .vite/, cache/, lockfiles)")
        $lines.Add("")
        $lines.Add("## Overall stats")
        $lines.Add("")
        $lines.Add("- **Total files**: $totalFiles")
        $lines.Add("- **Total lines**: $totalLines")
        $lines.Add("")
        $lines.Add("| Bucket | Files | Lines | Share |")
        $lines.Add("| :--- | :---: | :---: | :---: |")
        $bucketed | Sort-Object -Property Lines -Descending | ForEach-Object {
            $pct = if ($totalLines -gt 0) { [math]::Round(100.0 * $_.Lines / $totalLines, 1) } else { 0 }
            $lines.Add("| $($_.Bucket) | $($_.Files) | $($_.Lines) | $pct% |")
        }
        $lines.Add("| **Total** | **$totalFiles** | **$totalLines** | **100%** |")
        $lines.Add("")
        $lines.Add("## Top $Top largest files")
        $lines.Add("")
        $lines.Add("| File | Lines |")
        $lines.Add("| :--- | :---: |")
        $topFiles | ForEach-Object { $lines.Add("| ``$($_.Path)`` | $($_.Lines) |") }
        $lines | Set-Content -LiteralPath $OutFile -Encoding utf8
        Write-Host ""
        Write-Host "[output] $OutFile"
    }
}
finally {
    Pop-Location
}
