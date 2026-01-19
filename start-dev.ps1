# ============================================================
# DataVue App - Development Environment Startup Script (Simplified)
# ============================================================

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDir

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DataVue App - Development Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Fix Unicode output in Windows Console
$env:PYTHONIOENCODING = "utf-8"

# ============================================================
# 1. Environment Check and Python Executable Detection
# ============================================================

Write-Host "[1/2] Environment Check..." -ForegroundColor Yellow

$pythonExe = "python"

# Check Python and detect path if necessary
try {
    $pyVer = python --version 2>&1
    if (-not $pyVer -or "$pyVer" -notmatch "Python") { throw "Invalid or empty version" }
} catch {
    # Fallback to known common paths
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe", # Python 3.13 is current
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python313\python.exe",
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

# Ensure Python executable for backend is fully qualified path
$backendPythonExe = Join-Path $ProjectRoot "backend\venv\Scripts\python.exe"
if (-not (Test-Path $backendPythonExe)) {
    Write-Host "  ✗ Backend virtual environment Python executable not found at $backendPythonExe" -ForegroundColor Red
    Write-Host "    Please ensure 'python -m venv venv' has been run in the 'backend' directory." -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Backend venv Python: $backendPythonExe" -ForegroundColor Green


# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ Node.js not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "  ✓ npm: $npmVersion" -ForegroundColor Green
}
catch {
    Write-Host "  ✗ npm not installed" -ForegroundColor Red
    exit 1
}


# ============================================================
# 2. Start Backend and Frontend
# ============================================================

Write-Host ""
Write-Host "[2/2] Starting Backend and Frontend..." -ForegroundColor Yellow

# Start Backend (Uvicorn)
Write-Host "  Starting Backend with Uvicorn (reload enabled)..." -ForegroundColor Cyan
Start-Process -FilePath $backendPythonExe -ArgumentList "-m uvicorn main:app --reload --host 0.0.0.0 --port 8000" -WorkingDirectory (Join-Path $ProjectRoot "backend") -NoNewWindow

# Start Frontend (Vite)
Write-Host "  Starting Frontend with Vite..." -ForegroundColor Cyan
Start-Process -FilePath "npm" -ArgumentList "run dev" -WorkingDirectory (Join-Path $ProjectRoot "frontend") -NoNewWindow

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Development Environment Started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Service URLs (may take a moment to become active):" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: This script does not wait for processes to exit." -ForegroundColor Yellow
Write-Host "      You will need to manually stop the processes (Ctrl+C usually works for the main window," -ForegroundColor Yellow
Write-Host "      or Task Manager for background processes if -NoNewWindow prevents Ctrl+C)." -ForegroundColor Yellow
Write-Host ""