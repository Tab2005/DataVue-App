# ============================================================
# DataVue App - 統一啟動腳本 (Run All Services)
# ============================================================

# 設定編碼與環境
chcp 65001 > $null
$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

$ErrorActionPreference = "Continue"
$ProjectRoot = $PSScriptRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   DataVue App - 整合開發環境啟動" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. 環境檢查與自動清理
Write-Host "[1/3] 正在檢查環境與清理舊進程..." -ForegroundColor Yellow

# 先執行清理
& "$ProjectRoot\stop-all.ps1" | Out-Null

# 檢查 Python
$backendPython = Join-Path $ProjectRoot "backend\venv\Scripts\python.exe"
if (-not (Test-Path $backendPython)) {
    Write-Host "   找不到後端虛擬環境 ($backendPython)" -ForegroundColor Red
    Write-Host "    請先在 backend 目錄執行: python -m venv venv" -ForegroundColor Yellow
    exit 1
}
Write-Host "   後端虛擬環境: 準備就緒" -ForegroundColor Green

# 檢查 Node.js
try {
    $nodeVer = node --version 2>$null
    Write-Host "   Node.js: $nodeVer" -ForegroundColor Green
} catch {
    Write-Host "   找不到 Node.js，請確保已安裝並加入 PATH" -ForegroundColor Red
    exit 1
}

# 2. 啟動服務
Write-Host "`n[2/3] 正在啟動服務..." -ForegroundColor Yellow

# 啟動後端
Write-Host "   正在啟動後端 (Port 8000)..." -ForegroundColor Cyan
$backendProc = Start-Process -FilePath $backendPython -ArgumentList "-m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -WorkingDirectory (Join-Path $ProjectRoot "backend") -NoNewWindow -PassThru -ErrorAction SilentlyContinue

# 延遲啟動前端，減少啟動日誌混亂
Start-Sleep -Seconds 2

# 啟動前端
Write-Host "   正在啟動前端 (Port 5173)..." -ForegroundColor Cyan
$frontendProc = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory (Join-Path $ProjectRoot "frontend") -NoNewWindow -PassThru -ErrorAction SilentlyContinue

# 3. 完成提示
Write-Host "`n[3/3] 啟動程序完成！" -ForegroundColor Green
Write-Host "----------------------------------------"
Write-Host "  - 前端介面: http://localhost:5173" -ForegroundColor White
Write-Host "  - 後端 API:  http://localhost:8000" -ForegroundColor White
Write-Host "  - API 文檔: http://localhost:8000/docs" -ForegroundColor White
Write-Host "----------------------------------------"
Write-Host "提示: 若要停止所有服務，請執行 .\stop-all.ps1" -ForegroundColor Yellow
Write-Host ""

# 監控進程
try {
    while ($true) {
        if ($backendProc.HasExited) { break }
        if ($frontendProc.HasExited) { break }
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`n程序終止中..." -ForegroundColor Yellow
}
