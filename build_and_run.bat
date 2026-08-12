@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File build.ps1
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)
start "" "dist\GodPeace\GodPeace.exe"
