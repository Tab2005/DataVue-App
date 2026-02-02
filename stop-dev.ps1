# ============================================================
# DataVue App - Development Environment Termination Script
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   DataVue App - Development Shutdown" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find and stop the Backend (Uvicorn) process
$backendProcess = Get-CimInstance win32_process | Where-Object { $_.CommandLine -like "*uvicorn*main:app*" }
if ($backendProcess) {
    Write-Host "  Stopping Backend (Uvicorn) process (PID: $($backendProcess.ProcessId))..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.ProcessId -Force
    Write-Host "  ✓ Backend stopped." -ForegroundColor Green
} else {
    Write-Host "  ? Backend (Uvicorn) process not found." -ForegroundColor Gray
}

# Find and stop the Frontend (Vite/npm) process
# npm run dev often spawns a node process with a specific script path
$frontendProcess = Get-CimInstance win32_process | Where-Object { $_.CommandLine -like "*node_modules\vite\bin\vite.js*--host*127.0.0.1*" }
if ($frontendProcess) {
    Write-Host "  Stopping Frontend (Vite) process (PID: $($frontendProcess.ProcessId))..." -ForegroundColor Yellow
    Stop-Process -Id $frontendProcess.ProcessId -Force
    Write-Host "  ✓ Frontend stopped." -ForegroundColor Green
} else {
    Write-Host "  ? Frontend (Vite) process not found." -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Development Environment Shutdown Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
