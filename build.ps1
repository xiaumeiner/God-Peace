# Build God Peace release (onedir)
$ErrorActionPreference = "Stop"
$Hub = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Hub

$Python = Join-Path $Hub ".venv\Scripts\python.exe"
$Pip = Join-Path $Hub ".venv\Scripts\pip.exe"
$PyInstaller = Join-Path $Hub ".venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $Python)) {
    python -m venv .venv
}

& $Pip install -r requirements.txt -q

if (-not (Test-Path (Join-Path $Hub "assets\icon.ico"))) {
    & $Python make_icon.py
}
& $Python make_discord_icon.py
& $Python make_capt_swords.py
if (Test-Path (Join-Path $Hub "assets\discord_feedback_source.png")) {
    & $Python prepare_discord_icon.py
}

if (-not (Test-Path (Join-Path $Hub "bundled\calamity\tweaks.py"))) {
    & powershell -ExecutionPolicy Bypass -File build_bundle.ps1
} else {
    & powershell -ExecutionPolicy Bypass -File build_bundle.ps1
}

Write-Host "PyInstaller..."
& $PyInstaller --noconfirm god_peace.spec
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Dist = Join-Path $Hub "dist\GodPeace"
$BundledSrc = Join-Path $Hub "bundled"
$BundledDst = Join-Path $Dist "bundled"

if (Test-Path $BundledDst) { Remove-Item $BundledDst -Recurse -Force }
Copy-Item $BundledSrc $BundledDst -Recurse -Force
$SideforgeDist = Join-Path $BundledDst "sideforge"
if (Test-Path $SideforgeDist) { Remove-Item $SideforgeDist -Recurse -Force }

$MajesticEnv = Join-Path $Hub "majestic.env"
$MajesticEnvDst = Join-Path $Dist "majestic.env"
if (Test-Path $MajesticEnv) {
    Copy-Item $MajesticEnv $MajesticEnvDst -Force
} elseif (-not (Test-Path $MajesticEnvDst)) {
    Copy-Item (Join-Path $Hub "majestic.env.example") $MajesticEnvDst -Force
}

Write-Host ""
Write-Host "Build ready: $Dist\GodPeace.exe"
