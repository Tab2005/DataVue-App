@echo off
REM DataVue App - 一鍵啟動開發環境
REM Double-click this file to start the development environment

echo Starting DataVue Development Environment...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0start-dev.ps1"

pause
