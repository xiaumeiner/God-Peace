# Push only hub/ to https://github.com/xiaumeiner/God-Peace
$ErrorActionPreference = "Stop"
$Hub = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $Hub
Set-Location $Root

$Branch = "god-peace-split"
git subtree split --prefix=hub -b $Branch
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git push origin "${Branch}:main" --force-with-lease
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Pushed hub/ -> origin/main (God-Peace)"
