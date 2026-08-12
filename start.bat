@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
)
if not exist "assets\icon.ico" (
  echo Building icon...
  .\.venv\Scripts\python.exe make_icon.py
)
if not exist "bundled\calamity\tweaks.py" (
  echo Bundling Calamity, MapMark...
  powershell -ExecutionPolicy Bypass -File build_bundle.ps1
)
.\.venv\Scripts\python.exe app.py
