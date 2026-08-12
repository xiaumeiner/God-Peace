# Calamity keyboard fix - fixes slow Backspace repeat
$ErrorActionPreference = 'SilentlyContinue'

Write-Host 'Calamity: fixing keyboard repeat speed...' -ForegroundColor Cyan

Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardDelay' -Value 3 -Type String -ErrorAction SilentlyContinue
Set-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'KeyboardSpeed' -Value 31 -Type String -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKCU:\Control Panel\Keyboard' -Name 'TypematicDelay' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'KeyboardSpeed' -ErrorAction SilentlyContinue

Write-Host '[OK] KeyboardDelay=3, KeyboardSpeed=31 (fast Backspace repeat)' -ForegroundColor Green
