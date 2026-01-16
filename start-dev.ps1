# ============================================================
# DataVue App - Development Environment Startup Script
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DataVue App - Development Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# 1. Environment Check
# ============================================================

Write-Host "[1/5] Environment Check..." -ForegroundColor Yellow

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  [OK] Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [ERROR] Python not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  [OK] Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [ERROR] Node.js not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  [OK] npm: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "  [ERROR] npm not installed" -ForegroundColor Red
    exit 1
}

# ============================================================
# 2. Backend .env Check
# ============================================================

Write-Host ""
Write-Host "[2/5] Backend Config Check..." -ForegroundColor Yellow

$backendEnvPath = Join-Path $ProjectRoot "backend\.env"
if (Test-Path $backendEnvPath) {
    Write-Host "  [OK] backend/.env exists" -ForegroundColor Green
}
else {
    Write-Host "  [WARN] backend/.env not found, using defaults" -ForegroundColor Yellow
}

# ============================================================
# 3. Frontend .env Check
# ============================================================

Write-Host ""
Write-Host "[3/5] Frontend Config Check..." -ForegroundColor Yellow

$frontendEnvPath = Join-Path $ProjectRoot "frontend\.env"
if (Test-Path $frontendEnvPath) {
    Write-Host "  [OK] frontend/.env exists" -ForegroundColor Green
}
else {
    Write-Host "  [WARN] frontend/.env not found, using defaults" -ForegroundColor Yellow
}

# ============================================================
# 4. Start Backend
# ============================================================

Write-Host ""
Write-Host "[4/5] Starting Backend..." -ForegroundColor Yellow

$backendPath = Join-Path $ProjectRoot "backend"
$backendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 2>&1
} -ArgumentList $backendPath

Write-Host "  Backend Job ID: $($backendJob.Id)" -ForegroundColor Cyan

# Wait for backend health
Write-Host "  Waiting for backend health check..." -ForegroundColor Cyan
$maxRetries = 30
$retryCount = 0
$backendHealthy = $false

while ($retryCount -lt $maxRetries -and -not $backendHealthy) {
    Start-Sleep -Seconds 2
    $retryCount++
    
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($response.status -eq "ok") {
            $backendHealthy = $true
            Write-Host "  [OK] Backend healthy (version: $($response.version))" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "  Retry $retryCount/$maxRetries..." -ForegroundColor Gray
    }
}

if (-not $backendHealthy) {
    Write-Host "  [ERROR] Backend health check failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Backend logs:" -ForegroundColor Yellow
    Receive-Job -Job $backendJob -Keep | Select-Object -Last 30
    exit 1
}

# ============================================================
# 5. Start Frontend
# ============================================================

Write-Host ""
Write-Host "[5/5] Starting Frontend..." -ForegroundColor Yellow

$frontendPath = Join-Path $ProjectRoot "frontend"
$frontendJob = Start-Job -ScriptBlock {
    param($path)
    Set-Location $path
    npm run dev 2>&1
} -ArgumentList $frontendPath

Write-Host "  Frontend Job ID: $($frontendJob.Id)" -ForegroundColor Cyan

# Wait for frontend
Start-Sleep -Seconds 5
$frontendRetry = 0
$frontendHealthy = $false

while ($frontendRetry -lt 15 -and -not $frontendHealthy) {
    Start-Sleep -Seconds 1
    $frontendRetry++
    
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5173" -Method Head -TimeoutSec 2 -ErrorAction Stop
        $frontendHealthy = $true
        Write-Host "  [OK] Frontend ready" -ForegroundColor Green
    }
    catch {
        Write-Host "  Waiting for frontend... ($frontendRetry/15)" -ForegroundColor Gray
    }
}

if (-not $frontendHealthy) {
    Write-Host "  [WARN] Frontend may still be starting" -ForegroundColor Yellow
}

# ============================================================
# Complete
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Development Environment Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Health:   http://localhost:8000/api/health" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
Write-Host ""

# Keep script running
try {
    while ($true) {
        if ($backendJob.State -eq "Failed" -or $frontendJob.State -eq "Failed") {
            Write-Host "[ERROR] A service has failed" -ForegroundColor Red
            break
        }
        Start-Sleep -Seconds 5
    }
}
finally {
    Write-Host ""
    Write-Host "Stopping services..." -ForegroundColor Yellow
    Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job -Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job -Job $backendJob -Force -ErrorAction SilentlyContinue
    Remove-Job -Job $frontendJob -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] Services stopped" -ForegroundColor Green
}
