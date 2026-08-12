# Populate hub/bundled from local source projects (run before release).
$ErrorActionPreference = "Stop"
$Hub = Split-Path -Parent $MyInvocation.MyCommand.Path
$Bundled = Join-Path $Hub "bundled"

$CalamitySrc = "C:\Users\xiaumeiner\Desktop\1\opt\OptTuner"
$MapmarkInstaller = "C:\Users\xiaumeiner\Projects\mapmark\release\MapMark-Setup-1.0.0.exe"

New-Item -ItemType Directory -Force -Path (Join-Path $Bundled "calamity\profiles") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Bundled "installers") | Out-Null

$calamityFiles = @(
    "apply_runner.py", "boot_risk.py", "cleanup.py", "engine.py", "engine_extra.py",
    "nvidia.py", "paths.py", "system_restore.py", "tweak_copy.py", "tweaks.py"
)
foreach ($f in $calamityFiles) {
    Copy-Item (Join-Path $CalamitySrc $f) (Join-Path $Bundled "calamity\$f") -Force
}
Copy-Item (Join-Path $CalamitySrc "profiles\nvidia_latency.nip") (Join-Path $Bundled "calamity\profiles\") -Force

$SideforgeBundled = Join-Path $Bundled "sideforge"
if (Test-Path $SideforgeBundled) {
    Remove-Item $SideforgeBundled -Recurse -Force
}

if (-not (Test-Path $MapmarkInstaller)) {
    Write-Host "MapMark installer not found. Build it first:"
    Write-Host "  cd C:\Users\xiaumeiner\Projects\mapmark"
    Write-Host "  npm run dist:installer"
    exit 1
}
$ExtraFixesSrc = "C:\Users\xiaumeiner\Desktop\2321"
$ExtraFixesDst = Join-Path $Bundled "god_peace_fixes"
if (Test-Path $ExtraFixesSrc) {
    if (Test-Path $ExtraFixesDst) { Remove-Item $ExtraFixesDst -Recurse -Force }
    Copy-Item $ExtraFixesSrc $ExtraFixesDst -Recurse -Force
}

Copy-Item $MapmarkInstaller (Join-Path $Bundled "installers\MapMark-Setup-1.0.0.exe") -Force

Write-Host "Bundle ready: $Bundled"
