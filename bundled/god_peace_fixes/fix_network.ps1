# Calamity network fix - run as Administrator
$ErrorActionPreference = 'SilentlyContinue'

Write-Host 'Calamity: reverting network tweaks...' -ForegroundColor Cyan

Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' -Name 'TCPNoDelay' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' -Name 'TcpAckFrequency' -ErrorAction SilentlyContinue
Remove-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters' -Name 'TCPDelAckTicks' -ErrorAction SilentlyContinue

Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces' -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-ItemProperty -Path $_.PSPath -Name 'TcpAckFrequency' -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $_.PSPath -Name 'TCPNoDelay' -ErrorAction SilentlyContinue
    }

Get-DnsClient | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } | ForEach-Object {
    Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex -ResetServerAddresses -ErrorAction SilentlyContinue
}

Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Ndu' -Name 'Start' -Value 2 -Type DWord -ErrorAction SilentlyContinue

ipconfig /flushdns | Out-Null

Write-Host '[OK] TCP and DNS reverted' -ForegroundColor Green
Write-Host 'Disable Radmin VPN when browsing or using Discord.' -ForegroundColor Yellow
Write-Host 'Reboot PC if sites are still slow.' -ForegroundColor Gray
