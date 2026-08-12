@echo off
chcp 65001 >nul
title Calamity - window drag fix
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0fix_window_drag.ps1"
echo.
echo Try dragging a window now. Press any key to close.
pause >nul
