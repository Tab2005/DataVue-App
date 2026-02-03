# ============================================================
# DataVue App - 停止服務腳本 (Stop All Services)
# ============================================================

chcp 65001 > $null
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n正在停止 DataVue 相關服務與清理端口..." -ForegroundColor Yellow

# 1. 通過端口清理 (解決 Port in use 問題)
$ports = @(8000, 5173)
foreach ($port in $ports) {
    try {
        $pids = netstat -ano | Select-String "LISTENING" | Select-String ":$port\s+"
        foreach ($line in $pids) {
            $foundPid = ($line.ToString().Trim().Split(' ') | Where-Object { $_ -match '^\d+$' })[-1]
            if ($foundPid -and $foundPid -ne "0") {
                Write-Host "  正在終止佔用端口 $port 的進程 (PID: $foundPid)..." -ForegroundColor Cyan
                Stop-Process -Id $foundPid -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}

# 2. 通過名稱清理 (備援)
$procNames = @("uvicorn", "vite", "node")
foreach ($name in $procNames) {
    $procs = Get-Process | Where-Object { $_.CommandLine -like "*$name*" -or $_.Name -eq $name } -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "  正在清理 $name 相關進程..." -ForegroundColor Cyan
        $procs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "服務已完全清理。`n" -ForegroundColor Green
