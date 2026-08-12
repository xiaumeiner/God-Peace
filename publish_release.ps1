# Собрать zip для public Releases (God-Peace-Releases)
param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"
$Hub = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Hub

& .\build.ps1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Dist = Join-Path $Hub "dist\GodPeace"
$Zip = Join-Path $Hub "dist\GodPeace-v$Version.zip"
if (Test-Path $Zip) { Remove-Item $Zip -Force }

Compress-Archive -Path "$Dist\*" -DestinationPath $Zip -Force

Write-Host ""
Write-Host "Zip ready: $Zip"
Write-Host ""
Write-Host "Upload to: https://github.com/xiaumeiner/God-Peace/releases/new"
Write-Host "  Tag: v$Version"
Write-Host "  Asset: GodPeace-v$Version.zip"
