# ============================================================
# DataVue App - 開發環境啟動腳本 (PowerShell)
# Development Environment Startup Script
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DataVue App - 開發環境啟動" -ForegroundColor Cyan
Write-Host "   Development Environment Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

# Fix Unicode output in Windows Console
$env:PYTHONIOENCODING = "utf-8"

# ============================================================
# 1. 環境檢查 - Environment Check
# ============================================================

Write-Host "[1/5] 環境檢查 (Environment Check)..." -ForegroundColor Yellow

$pythonExe = "python"

# Check Python and detect path if necessary
try {
    $pyVer = python --version 2>&1
    if (-not $pyVer -or "$pyVer" -notmatch "Python") { throw "Invalid or empty version" }
} catch {
    # Fallback to known common paths
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $pythonExe = $c
            Write-Host "  ⚠ Default 'python' command failed. Using explicit path: $pythonExe" -ForegroundColor Yellow
            break
        }
    }
}

try {
    $pythonVersion = & $pythonExe --version 2>&1
    if (-not $pythonVersion) { throw "Still invalid" }
    Write-Host "  ✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python 未安裝或是 Windows Store Stub (請手動安裝 Python)" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Node.js 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  ✓ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ npm 未安裝" -ForegroundColor Red
    exit 1
}

# ============================================================
# 2. 後端環境變數檢查 - Backend .env Check
# ============================================================

Write-Host ""
Write-Host "[2/5] 後端設定檢查 (Backend Config Check)..." -ForegroundColor Yellow

$backendEnvPath = Join-Path $ProjectRoot "backend\.env"
if (Test-Path $backendEnvPath) {
    Write-Host "  ✓ backend/.env 存在" -ForegroundColor Green
    
    # Check for required env vars
    $envContent = Get-Content $backendEnvPath -Raw
    $requiredVars = @("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET")
    foreach ($var in $requiredVars) {
        if ($envContent -match "$var\s*=") {
            Write-Host "  ✓ $var 已設定" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ $var 未設定 (可能會影響 Google 登入)" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "  ⚠ backend/.env 不存在，將使用預設值" -ForegroundColor Yellow
}

# ============================================================
# 3. 前端環境變數檢查 - Frontend .env Check
# ============================================================

Write-Host ""
Write-Host "[3/5] 前端設定檢查 (Frontend Config Check)..." -ForegroundColor Yellow

$frontendEnvPath = Join-Path $ProjectRoot "frontend\.env"
if (Test-Path $frontendEnvPath) {
    Write-Host "  ✓ frontend/.env 存在" -ForegroundColor Green
} else {
    Write-Host "  ⚠ frontend/.env 不存在 (將使用開發預設值)" -ForegroundColor Yellow
}

# ============================================================
# 4. 啟動後端服務 - Start Backend
# ============================================================

Write-Host ""
Write-Host "[4/5] 啟動後端服務 (Starting Backend)..." -ForegroundColor Yellow

$backendPath = Join-Path $ProjectRoot "backend"
$backendJob = Start-Job -ScriptBlock {
    param($path, $exe)
    Set-Location $path
    & $exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1
} -ArgumentList $backendPath, $pythonExe

Write-Host "  → 後端服務啟動中 (Job ID: $($backendJob.Id))..." -ForegroundColor Cyan

# Wait for backend to be healthy
$maxRetries = 15
$retryCount = 0
$backendHealthy = $false

Write-Host "  → 等待後端健康檢查..." -ForegroundColor Cyan

while ($retryCount -lt $maxRetries -and -not $backendHealthy) {
    Start-Sleep -Seconds 2
    $retryCount++
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 3
        if ($response.status -eq "ok") {
            $backendHealthy = $true
            Write-Host "  ✓ 後端健康檢查通過 (status: ok, version: $($response.version))" -ForegroundColor Green
        }
    } catch {
        Write-Host "  → 重試 $retryCount/$maxRetries..." -ForegroundColor Gray
    }
}

if (-not $backendHealthy) {
    Write-Host "  ✗ 後端健康檢查失敗，請檢查錯誤訊息" -ForegroundColor Red
    Write-Host ""
    Write-Host "後端日誌 (最近輸出):" -ForegroundColor Yellow
    Receive-Job -Job $backendJob -Keep | Select-Object -Last 20
    exit 1
}

# ============================================================
# 5. 啟動前端服務 - Start Frontend
# ============================================================

Write-Host ""
Write-Host "[5/5] 啟動前端服務 (Starting Frontend)..." -ForegroundColor Yellow

$frontendPath = Join-Path $ProjectRoot "frontend"
$frontendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    npm run dev 2>&1
} -ArgumentList $frontendPath

Write-Host "  → 前端服務啟動中 (Job ID: $($frontendJob.Id))..." -ForegroundColor Cyan

# Wait for frontend to be ready
Start-Sleep -Seconds 5

$frontendHealthy = $false
$frontendRetry = 0
$maxFrontendRetries = 10

while ($frontendRetry -lt $maxFrontendRetries -and -not $frontendHealthy) {
    Start-Sleep -Seconds 1
    $frontendRetry++
    
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5173" -Method Head -TimeoutSec 3
        $frontendHealthy = $true
        Write-Host "  ✓ 前端服務已就緒" -ForegroundColor Green
    } catch {
        Write-Host "  → 等待前端啟動... ($frontendRetry/$maxFrontendRetries)" -ForegroundColor Gray
    }
}

if (-not $frontendHealthy) {
    Write-Host "  ⚠ 前端服務可能尚未完全啟動，但仍在背景執行" -ForegroundColor Yellow
}

# ============================================================
# 完成 - Complete
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   ✓ 開發環境已啟動完成!" -ForegroundColor Green
Write-Host "   ✓ Development Environment Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "服務位址 (Service URLs):" -ForegroundColor Cyan
Write-Host "  前端 (Frontend): http://localhost:5173" -ForegroundColor White
Write-Host "  後端 (Backend):  http://localhost:8000" -ForegroundColor White
Write-Host "  API 文件 (Docs): http://localhost:8000/docs" -ForegroundColor White
Write-Host "  健康檢查 (Health): http://localhost:8000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止所有服務" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep script running and stream logs
try {
    while ($true) {
        # Check if jobs are still running
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "⚠ 服務異常終止，請檢查日誌" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 5
    }
} finally {
    # Cleanup on exit
    Write-Host ""
    Write-Host "正在停止服務..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "✓ 服務已停止" -ForegroundColor Green
}
