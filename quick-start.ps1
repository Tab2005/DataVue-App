# ============================================================
# DataVue App - 快速啟動腳本 (Quick Start)
# 適用於需要分別在兩個終端視窗啟動服務的情況
# ============================================================

param(
    [Parameter(Position=0)]
    [ValidateSet("backend", "frontend", "both", "check")]
    [string]$Service = "both"
)

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Start-Backend {
    Write-Host "🚀 啟動後端服務..." -ForegroundColor Cyan
    $backendPath = Join-Path $ProjectRoot "backend"
    Set-Location $backendPath
    python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
}

function Start-Frontend {
    Write-Host "🚀 啟動前端服務..." -ForegroundColor Cyan
    $frontendPath = Join-Path $ProjectRoot "frontend"
    Set-Location $frontendPath
    npm run dev
}

function Check-Health {
    Write-Host "🔍 健康檢查..." -ForegroundColor Cyan
    Write-Host ""
    
    # Backend
    Write-Host "後端 (Backend) - http://localhost:8000" -ForegroundColor Yellow
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 5
        Write-Host "  ✓ Status: $($response.status)" -ForegroundColor Green
        Write-Host "  ✓ Version: $($response.version)" -ForegroundColor Green
        Write-Host "  ✓ Database: $($response.database_type)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ 無法連線 (Not reachable)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Frontend
    Write-Host "前端 (Frontend) - http://localhost:5173" -ForegroundColor Yellow
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:5173" -Method Head -TimeoutSec 5
        Write-Host "  ✓ 服務運行中 (Running)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ 無法連線 (Not reachable)" -ForegroundColor Red
    }
}

# Main
switch ($Service) {
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "check" { Check-Health }
    "both" {
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "  DataVue Quick Start" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "用法 (Usage):" -ForegroundColor Yellow
        Write-Host "  .\quick-start.ps1 backend   # 啟動後端" -ForegroundColor White
        Write-Host "  .\quick-start.ps1 frontend  # 啟動前端" -ForegroundColor White
        Write-Host "  .\quick-start.ps1 check     # 健康檢查" -ForegroundColor White
        Write-Host ""
        Write-Host "建議在兩個獨立終端分別執行:" -ForegroundColor Yellow
        Write-Host "  Terminal 1: .\quick-start.ps1 backend" -ForegroundColor Cyan
        Write-Host "  Terminal 2: .\quick-start.ps1 frontend" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "或使用完整啟動腳本: .\start-dev.ps1" -ForegroundColor Yellow
    }
}
