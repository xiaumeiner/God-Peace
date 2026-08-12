@echo off
chcp 65001 >nul
title Calamity - keyboard fix
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_keyboard.ps1"
if errorlevel 1 (
    echo.
    echo ERROR running fix_keyboard.ps1
    pause
    exit /b 1
)
echo.
echo Backspace should be fast now. Press any key to close.
pause >nul
