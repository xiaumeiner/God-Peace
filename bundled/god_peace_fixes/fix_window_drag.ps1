# Restore normal window drag (full contents, not wireframe outline)
$ErrorActionPreference = 'SilentlyContinue'
Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name 'DragFullWindows' -Value '1' -Type String
Write-Host '[OK] DragFullWindows=1 - windows show content while dragging' -ForegroundColor Green
