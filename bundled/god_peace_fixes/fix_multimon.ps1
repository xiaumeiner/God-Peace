# Calamity multimon fix - run as Administrator
$ErrorActionPreference = 'SilentlyContinue'

Write-Host 'Calamity: fixing multi-monitor drag...' -ForegroundColor Cyan

Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Dwm' -Name 'OverlayTestMode' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\DXGKrnl' -Name 'MonitorLatencyTolerance' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\DXGKrnl' -Name 'MonitorRefreshLatencyTolerance' -ErrorAction SilentlyContinue

$mpo = (Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows\Dwm' -Name 'OverlayTestMode' -ErrorAction SilentlyContinue).OverlayTestMode
if ($null -eq $mpo) {
    Write-Host '[OK] OverlayTestMode removed' -ForegroundColor Green
} else {
    Write-Host "[!] OverlayTestMode still = $mpo - run as Administrator" -ForegroundColor Yellow
}

Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
Start-Process explorer

Write-Host 'Explorer restarted. Try dragging a window to the second monitor.' -ForegroundColor Green
