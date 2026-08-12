@echo off
chcp 65001 >nul
title Calamity - network fix
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
    echo Need Administrator rights. Right-click - Run as administrator.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_network.ps1"
if errorlevel 1 (
    echo.
    echo ERROR running fix_network.ps1
    pause
    exit /b 1
)
echo.
echo Done. Press any key to close.
pause >nul
