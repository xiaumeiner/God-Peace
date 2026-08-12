"""Движок применения и отката твиков Windows."""

from __future__ import annotations

import ctypes
import subprocess
import sys
import winreg
from typing import Callable


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def _run(cmd: list[str], timeout: int = 60) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=timeout,
        )
        ok = result.returncode == 0
        output = (result.stdout or "") + (result.stderr or "")
        return ok, output.strip()
    except subprocess.TimeoutExpired:
        return False, f"Таймаут команды ({timeout} с): {' '.join(cmd[:3])}"
    except Exception as exc:
        return False, str(exc)


def set_dword(root: int, path: str, name: str, value: int) -> None:
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
    finally:
        winreg.CloseKey(key)


def set_string(root: int, path: str, name: str, value: str) -> None:
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    finally:
        winreg.CloseKey(key)


def set_binary(root: int, path: str, name: str, value: bytes) -> None:
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_BINARY, value)
    finally:
        winreg.CloseKey(key)


def get_dword(root: int, path: str, name: str, default: int | None = None) -> int | None:
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return int(value)
    except OSError:
        return default


def delete_value(root: int, path: str, name: str) -> None:
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def ensure_key(root: int, path: str) -> None:
    winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)


HKLM = winreg.HKEY_LOCAL_MACHINE
HKCU = winreg.HKEY_CURRENT_USER


def apply_bcd_timer_tweaks() -> tuple[bool, str]:
    ok1, out1 = _run(["bcdedit", "/set", "disabledynamictick", "yes"])
    ok2, out2 = _run(["bcdedit", "/set", "useplatformtick", "yes"])
    ok3, out3 = _run(["bcdedit", "/deletevalue", "useplatformclock"])
    ok = ok1 and ok2
    return ok, "\n".join(filter(None, [out1, out2, out3]))


def revert_bcd_timer_tweaks() -> tuple[bool, str]:
    results = []
    for args in (
        ["bcdedit", "/deletevalue", "disabledynamictick"],
        ["bcdedit", "/deletevalue", "useplatformtick"],
        ["bcdedit", "/deletevalue", "useplatformclock"],
    ):
        ok, out = _run(args)
        results.append(out)
    return True, "\n".join(results)


def apply_usb_power_saving_off() -> tuple[bool, str]:
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$devices = Get-PnpDevice | Where-Object { $_.InstanceId -like '*USB\ROOT*' }
foreach ($device in $devices) {
    $id = $device.PNPDeviceID
    $instances = Get-CimInstance -Namespace root/wmi -ClassName MSPower_DeviceEnable |
        Where-Object { $_.InstanceName -like "*$id*" }
    foreach ($inst in $instances) {
        Set-CimInstance -InputObject $inst -Property @{ Enable = $false } | Out-Null
    }
}
"""
    return _run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
    )


def apply_gpu_thread_priority() -> tuple[bool, str]:
    script = r"""
$brand = (Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name -First 1)
if ($brand -match 'nvidia') {
    $path = 'HKLM:\SYSTEM\CurrentControlSet\Services\nvlddmkm\Parameters'
    if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
    Set-ItemProperty -Path $path -Name ThreadPriority -Value 0x1F -Type DWord
    'NVIDIA'
} elseif ($brand -match 'amd|radeon') {
    $path = 'HKLM:\SYSTEM\CurrentControlSet\Services\amdkmdap\Parameters'
    if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
    Set-ItemProperty -Path $path -Name ThreadPriority -Value 0x1F -Type DWord
    'AMD'
} else {
    throw 'GPU not found'
}
"""
    return _run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
    )


def revert_gpu_thread_priority() -> tuple[bool, str]:
    for path, name in (
        (r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Parameters", "ThreadPriority"),
        (r"SYSTEM\CurrentControlSet\Services\amdkmdap\Parameters", "ThreadPriority"),
    ):
        delete_value(HKLM, path, name)
    return True, "GPU thread priority reverted"


def apply_mouse_1to1() -> tuple[bool, str]:
    set_string(HKCU, r"Control Panel\Mouse", "MouseSpeed", "0")
    set_string(HKCU, r"Control Panel\Mouse", "MouseThreshold1", "0")
    set_string(HKCU, r"Control Panel\Mouse", "MouseThreshold2", "0")
    set_string(HKCU, r"Control Panel\Mouse", "MouseSensitivity", "10")
    curve_x = bytes.fromhex(
        "0000000000000000C0CC0C0000000000809919000000000040662600000000000033330000000000"
    )
    curve_y = bytes.fromhex(
        "0000000000000000000038000000000000007000000000000000A800000000000000E00000000000"
    )
    set_binary(HKCU, r"Control Panel\Mouse", "SmoothMouseXCurve", curve_x)
    set_binary(HKCU, r"Control Panel\Mouse", "SmoothMouseYCurve", curve_y)
    return True, "Mouse 1:1 applied"


def revert_mouse_default() -> tuple[bool, str]:
    delete_value(HKCU, r"Control Panel\Mouse", "SmoothMouseXCurve")
    delete_value(HKCU, r"Control Panel\Mouse", "SmoothMouseYCurve")
    set_string(HKCU, r"Control Panel\Mouse", "MouseSpeed", "1")
    return True, "Mouse settings reverted"


def apply_game_dvr_off() -> tuple[bool, str]:
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_Enabled", 0)
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", 2)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 0)
    set_dword(
        HKCU,
        r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
        "BackgroundRecordingEnabled",
        0,
    )
    return True, "Game DVR disabled"


def revert_game_dvr_on() -> tuple[bool, str]:
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_Enabled", 1)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled", 1)
    return True, "Game DVR enabled"


def apply_game_profile() -> tuple[bool, str]:
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    games = base + r"\Tasks\Games"
    ensure_key(HKLM, games)
    set_dword(HKLM, games, "GPU Priority", 8)
    set_dword(HKLM, games, "Priority", 6)
    set_dword(HKLM, games, "Clock Rate", 10000)
    set_string(HKLM, games, "Scheduling Category", "High")
    set_string(HKLM, games, "SFIO Priority", "High")
    set_string(HKLM, games, "Background Only", "False")
    return True, "Game multimedia profile applied"


def revert_game_profile() -> tuple[bool, str]:
    games = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    for name in ("GPU Priority", "Priority", "Clock Rate", "Scheduling Category", "SFIO Priority", "Background Only"):
        delete_value(HKLM, games, name)
    return True, "Game profile reverted"


def apply_mmcss_aggressive() -> tuple[bool, str]:
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    set_dword(HKLM, base, "NoLazyMode", 1)
    set_dword(HKLM, base, "AlwaysOn", 1)
    set_dword(HKLM, base, "SystemResponsiveness", 0)
    return True, "MMCSS aggressive mode applied"


def revert_mmcss_aggressive() -> tuple[bool, str]:
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    delete_value(HKLM, base, "NoLazyMode")
    delete_value(HKLM, base, "AlwaysOn")
    set_dword(HKLM, base, "SystemResponsiveness", 20)
    return True, "MMCSS reverted"


def apply_graphics_latency() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "MaximumFrameLatency", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "FlipQueueSize", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "PlatformPerformanceHint", 1)
    return True, "Graphics latency tweaks applied"


def revert_graphics_latency() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "MaximumFrameLatency")
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "FlipQueueSize")
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "PlatformPerformanceHint")
    return True, "Graphics latency tweaks reverted"


def apply_monitor_latency() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\DXGKrnl", "MonitorLatencyTolerance", 0)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\DXGKrnl", "MonitorRefreshLatencyTolerance", 0)
    return True, "Monitor latency tolerance minimized"


def revert_monitor_latency() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\DXGKrnl", "MonitorLatencyTolerance")
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\DXGKrnl", "MonitorRefreshLatencyTolerance")
    return True, "Monitor latency tolerance reverted"


def apply_power_throttling_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling")
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Power", "LowLatencyScalingPercentage", 100)
    return True, "Power throttling disabled"


def revert_power_throttling_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Power\PowerThrottling", "PowerThrottlingOff", 0)
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\Power", "LowLatencyScalingPercentage")
    return True, "Power throttling restored"


def apply_cpu_priority() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 0x28)
    return True, "CPU foreground priority boosted"


def revert_cpu_priority() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 0x2)
    return True, "CPU priority restored"


def apply_memory_gaming() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "DisablePagingExecutive", 1)
    set_dword(HKLM, mm, "LargeSystemCache", 0)
    set_dword(HKLM, mm, "ClearPageFileAtShutdown", 0)
    pref = mm + r"\PrefetchParameters"
    set_dword(HKLM, pref, "EnablePrefetcher", 3)
    set_dword(HKLM, pref, "EnableSuperfetch", 0)
    return True, "Memory gaming tweaks applied"


def revert_memory_gaming() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "DisablePagingExecutive", 0)
    delete_value(HKLM, mm, "LargeSystemCache")
    return True, "Memory tweaks reverted"


def apply_transparency_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting", 2)
    return True, "Transparency and visual effects reduced"


def revert_transparency_on() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency", 1)
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects", "VisualFXSetting")
    return True, "Transparency restored"


def apply_gpu_energy_drv_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\GpuEnergyDrv", "Start", 4)
    return True, "GpuEnergyDrv disabled"


def revert_gpu_energy_drv_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\GpuEnergyDrv", "Start", 3)
    return True, "GpuEnergyDrv restored"


def apply_background_apps_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", "GlobalUserDisabled", 1)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "BackgroundAppGlobalToggle", 0)
    return True, "Background apps limited"


def revert_background_apps_on() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\BackgroundAccessApplications", "GlobalUserDisabled", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "BackgroundAppGlobalToggle", 1)
    return True, "Background apps restored"


def apply_maintenance_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance")
    set_dword(HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance", "MaintenanceDisabled", 1)
    return True, "Automatic maintenance disabled"


def revert_maintenance_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Schedule\Maintenance", "MaintenanceDisabled", 0)
    return True, "Automatic maintenance enabled"


def apply_sysmain_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\SysMain", "Start", 4)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WSearch", "Start", 4)
    return True, "SysMain and Windows Search disabled"


def revert_sysmain_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\SysMain", "Start", 2)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WSearch", "Start", 2)
    return True, "SysMain and Windows Search restored"


def apply_usb_selective_suspend_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\UsbHub", "DisableSelectiveSuspend", 1)
    return True, "USB selective suspend disabled"


def revert_usb_selective_suspend_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\UsbHub", "DisableSelectiveSuspend")
    return True, "USB selective suspend restored"


def apply_desktop_responsiveness() -> tuple[bool, str]:
    set_string(HKCU, r"Control Panel\Desktop", "MenuShowDelay", "0")
    set_string(HKCU, r"Control Panel\Desktop", "AutoEndTasks", "1")
    set_string(HKCU, r"Control Panel\Desktop", "WaitToKillAppTimeout", "2000")
    set_string(HKCU, r"Control Panel\Desktop", "HungAppTimeout", "1000")
    set_dword(HKCU, r"Control Panel\Desktop", "ForegroundLockTimeout", 0)
    return True, "Desktop responsiveness improved"


def revert_desktop_responsiveness() -> tuple[bool, str]:
    set_string(HKCU, r"Control Panel\Desktop", "MenuShowDelay", "400")
    set_string(HKCU, r"Control Panel\Desktop", "WaitToKillAppTimeout", "5000")
    return True, "Desktop responsiveness restored"


def apply_gta5_priority() -> tuple[bool, str]:
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\GTA5.exe\PerfOptions"
    ensure_key(HKLM, path)
    set_dword(HKLM, path, "CpuPriorityClass", 3)
    return True, "GTA5 high CPU priority set"


def revert_gta5_priority() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\GTA5.exe\PerfOptions",
        "CpuPriorityClass",
    )
    return True, "GTA5 priority removed"


def apply_timer_resolution(ms: float) -> tuple[bool, str]:
    # NtSetTimerResolution через PowerShell — работает без внешних exe
    hundred_ns = int(ms * 10000)
    script = f"""
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class TimerResolution {{
    [DllImport("ntdll.dll")] public static extern int NtSetTimerResolution(uint Desired, bool Set, out uint Current);
    [DllImport("ntdll.dll")] public static extern int NtQueryTimerResolution(out uint Min, out uint Max, out uint Current);
}}
'@
$desired = [uint32]{hundred_ns}
$current = [uint32]0
$result = [TimerResolution]::NtSetTimerResolution($desired, $true, [ref]$current)
if ($result -ne 0) {{ throw "NtSetTimerResolution failed: $result" }}
"Timer resolution set to {ms} ms (current=$current)"
"""
    return _run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ]
    )


def _ps(script: str, timeout: int = 45) -> tuple[bool, str]:
    return _run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
    )


def apply_msi_gpu() -> tuple[bool, str]:
    script = r"""
$count = 0
Get-CimInstance Win32_VideoController | Where-Object { $_.PNPDeviceID -match 'VEN_' } | ForEach-Object {
    $base = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.PNPDeviceID)\Device Parameters\Interrupt Management"
    $msi = "$base\MessageSignaledInterruptProperties"
    $aff = "$base\Affinity Policy"
    if (-not (Test-Path $msi)) { New-Item -Path $msi -Force | Out-Null }
    Set-ItemProperty -Path $msi -Name MSISupported -Value 1 -Type DWord
    if (-not (Test-Path $aff)) { New-Item -Path $aff -Force | Out-Null }
    Set-ItemProperty -Path $aff -Name DevicePriority -Value 0 -Type DWord
    $count++
}
if ($count -eq 0) { throw 'GPU not found' }
"MSI enabled for $count GPU(s)"
"""
    return _ps(script)


def revert_msi_gpu() -> tuple[bool, str]:
    script = r"""
Get-CimInstance Win32_VideoController | Where-Object { $_.PNPDeviceID -match 'VEN_' } | ForEach-Object {
    $msi = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.PNPDeviceID)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    $aff = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.PNPDeviceID)\Device Parameters\Interrupt Management\Affinity Policy"
    Remove-ItemProperty -Path $msi -Name MSISupported -ErrorAction SilentlyContinue
    Remove-ItemProperty -Path $aff -Name DevicePriority -ErrorAction SilentlyContinue
}
'MSI GPU reverted'
"""
    return _ps(script)


def apply_msi_usb() -> tuple[bool, str]:
    script = r"""
$count = 0
Get-PnpDevice | Where-Object { $_.InstanceId -like 'USB\ROOT*' } | ForEach-Object {
    $msi = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    if (-not (Test-Path $msi)) { New-Item -Path $msi -Force | Out-Null }
    Set-ItemProperty -Path $msi -Name MSISupported -Value 1 -Type DWord
    $count++
}
"MSI enabled for $count USB controller(s)"
"""
    return _ps(script)


def revert_msi_usb() -> tuple[bool, str]:
    script = r"""
Get-PnpDevice | Where-Object { $_.InstanceId -like 'USB\ROOT*' } | ForEach-Object {
    $msi = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.InstanceId)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    Remove-ItemProperty -Path $msi -Name MSISupported -ErrorAction SilentlyContinue
}
'MSI USB reverted'
"""
    return _ps(script)


def apply_msi_network() -> tuple[bool, str]:
    script = r"""
$count = 0
Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.PNPDeviceID -match 'VEN_' } | ForEach-Object {
    $msi = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.PNPDeviceID)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    if (-not (Test-Path $msi)) { New-Item -Path $msi -Force | Out-Null }
    Set-ItemProperty -Path $msi -Name MSISupported -Value 1 -Type DWord
    $count++
}
"MSI enabled for $count network adapter(s)"
"""
    return _ps(script)


def revert_msi_network() -> tuple[bool, str]:
    script = r"""
Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.PNPDeviceID -match 'VEN_' } | ForEach-Object {
    $msi = "HKLM:\SYSTEM\CurrentControlSet\Enum\$($_.PNPDeviceID)\Device Parameters\Interrupt Management\MessageSignaledInterruptProperties"
    Remove-ItemProperty -Path $msi -Name MSISupported -ErrorAction SilentlyContinue
}
'MSI network reverted'
"""
    return _ps(script)


def apply_hags() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 2)
    return True, "HAGS enabled (HwSchMode=2)"


def revert_hags() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "HwSchMode", 1)
    return True, "HAGS reverted to default"


def apply_distribute_timers() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel", "DistributeTimers", 1)
    return True, "DistributeTimers enabled"


def revert_distribute_timers() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\kernel", "DistributeTimers")
    return True, "DistributeTimers reverted"


def apply_network_throttle_off() -> tuple[bool, str]:
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile"
    set_dword(HKLM, base, "NetworkThrottlingIndex", 0xFFFFFFFF)
    return True, "Network throttling disabled (xiaumm)"


def revert_network_throttle_on() -> tuple[bool, str]:
    set_dword(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
        "NetworkThrottlingIndex",
        10,
    )
    return True, "Network throttling restored"


def apply_tcp_low_latency() -> tuple[bool, str]:
    tcp = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    set_dword(HKLM, tcp, "TCPNoDelay", 1)
    set_dword(HKLM, tcp, "TcpAckFrequency", 1)
    set_dword(HKLM, tcp, "TCPDelAckTicks", 0)
    set_dword(HKLM, tcp, "EnableRSS", 1)
    set_dword(HKLM, tcp, "EnableTCPA", 1)
    return True, "TCP low-latency parameters applied"


def revert_tcp_default() -> tuple[bool, str]:
    tcp = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    for name in ("TCPNoDelay", "TcpAckFrequency", "TCPDelAckTicks"):
        delete_value(HKLM, tcp, name)
    return True, "TCP parameters reverted"


def apply_disable_dynamic_pstate() -> tuple[bool, str]:
    script = r"""
$count = 0
$base = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
    $desc = (Get-ItemProperty $_.PSPath -Name DriverDesc -ErrorAction SilentlyContinue).DriverDesc
    if ($desc -match 'NVIDIA|GeForce|RTX|GTX') {
        Set-ItemProperty -Path $_.PSPath -Name DisableDynamicPstate -Value 1 -Type DWord
        $count++
    }
}
if ($count -eq 0) { throw 'NVIDIA GPU class key not found' }
"DisableDynamicPstate set on $count adapter(s)"
"""
    return _ps(script)


def revert_disable_dynamic_pstate() -> tuple[bool, str]:
    script = r"""
$base = 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}'
Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-ItemProperty -Path $_.PSPath -Name DisableDynamicPstate -ErrorAction SilentlyContinue
}
'DisableDynamicPstate reverted'
"""
    return _ps(script)


def apply_nvidia_driver_tweaks() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "PlatformSupportMiracast", 0)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Global\NVTweak", "DisplayPowerSaving", 0)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm\FTS", "EnableRID61684", 1)
    script = r"""
$nvsmi = "${env:ProgramFiles}\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
if (Test-Path $nvsmi) { & $nvsmi -acp UNRESTRICTED 2>$null; & $nvsmi -acp DEFAULT 2>$null }
Get-ChildItem 'HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}' |
  Where-Object { (Get-ItemProperty $_.PSPath -Name DriverDesc -EA 0).DriverDesc -match 'NVIDIA' } |
  ForEach-Object {
    Set-ItemProperty $_.PSPath -Name EnableTiledDisplay -Value 0 -Type DWord -EA 0
  }
'NVIDIA driver tweaks applied'
"""
    ok, msg = _ps(script)
    return ok, msg or "NVIDIA driver registry tweaks applied"


def revert_nvidia_driver_tweaks() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers", "PlatformSupportMiracast", 1)
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm\Global\NVTweak", "DisplayPowerSaving")
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm\FTS", "EnableRID61684")
    return True, "NVIDIA driver tweaks reverted"


def apply_nvidia_write_combining_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm", "DisableWriteCombining", 1)
    return True, "DisableWriteCombining enabled"


def revert_nvidia_write_combining_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\nvlddmkm", "DisableWriteCombining")
    return True, "Write combining restored"


def apply_gpu_preemption() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler", "EnablePreemption", 1)
    return True, "GPU preemption enabled"


def revert_gpu_preemption() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers\Scheduler", "EnablePreemption")
    return True, "GPU preemption reverted"


def apply_energy_logging_off() -> tuple[bool, str]:
    base = r"SYSTEM\CurrentControlSet\Control\Power\EnergyEstimation\TaggedEnergy"
    ensure_key(HKLM, base)
    set_dword(HKLM, base, "DisableTaggedEnergyLogging", 1)
    set_dword(HKLM, base, "TelemetryMaxApplication", 0)
    set_dword(HKLM, base, "TelemetryMaxTagPerApplication", 0)
    return True, "Energy logging disabled (xiaumm)"


def revert_energy_logging_on() -> tuple[bool, str]:
    base = r"SYSTEM\CurrentControlSet\Control\Power\EnergyEstimation\TaggedEnergy"
    delete_value(HKLM, base, "DisableTaggedEnergyLogging")
    return True, "Energy logging restored"


def apply_hibernate_off() -> tuple[bool, str]:
    _run(["powercfg", "/hibernate", "off"])
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\Power", "HibernateEnabled", 0)
    return True, "Hibernation disabled"


def revert_hibernate_on() -> tuple[bool, str]:
    _run(["powercfg", "/hibernate", "on"])
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\Power", "HibernateEnabled")
    return True, "Hibernation enabled"


def apply_fth_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Microsoft\FTH", "Enabled", 0)
    return True, "Fault Tolerant Heap disabled"


def revert_fth_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Microsoft\FTH", "Enabled", 1)
    return True, "FTH enabled"


def apply_game_mode_on() -> tuple[bool, str]:
    set_dword(HKCU, r"SOFTWARE\Microsoft\GameBar", "AllowAutoGameMode", 1)
    set_dword(HKCU, r"SOFTWARE\Microsoft\GameBar", "AutoGameModeEnabled", 1)
    return True, "Windows Game Mode enabled"


def revert_game_mode_off() -> tuple[bool, str]:
    set_dword(HKCU, r"SOFTWARE\Microsoft\GameBar", "AutoGameModeEnabled", 0)
    return True, "Game Mode disabled"


def apply_latency_sensitive_games() -> tuple[bool, str]:
    games = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games"
    ensure_key(HKLM, games)
    set_string(HKLM, games, "Latency Sensitive", "True")
    set_dword(HKLM, games, "Clock Rate", 10000)
    return True, "Games task marked latency-sensitive (xiaumm)"


def revert_latency_sensitive_games() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games",
        "Latency Sensitive",
    )
    return True, "Latency Sensitive flag removed"


def apply_cs2_priority() -> tuple[bool, str]:
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\cs2.exe\PerfOptions"
    ensure_key(HKLM, path)
    set_dword(HKLM, path, "CpuPriorityClass", 8)
    return True, "CS2 high CPU priority set"


def revert_cs2_priority() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\cs2.exe\PerfOptions",
        "CpuPriorityClass",
    )
    return True, "CS2 priority removed"


def apply_valorant_priority() -> tuple[bool, str]:
    for exe in ("VALORANT-Win64-Shipping.exe", "valorant.exe"):
        path = rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe}\PerfOptions"
        ensure_key(HKLM, path)
        set_dword(HKLM, path, "CpuPriorityClass", 8)
    return True, "Valorant high CPU priority set"


def revert_valorant_priority() -> tuple[bool, str]:
    for exe in ("VALORANT-Win64-Shipping.exe", "valorant.exe"):
        delete_value(
            HKLM,
            rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{exe}\PerfOptions",
            "CpuPriorityClass",
        )
    return True, "Valorant priority removed"


def apply_notifications_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 0)
    set_dword(
        HKCU,
        r"Software\Microsoft\Windows\CurrentVersion\Notifications\Settings",
        "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND",
        0,
    )
    return True, "Notifications reduced"


def revert_notifications_on() -> tuple[bool, str]:
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\PushNotifications", "ToastEnabled", 1)
    return True, "Notifications restored"


def apply_nvidia_telemetry_off() -> tuple[bool, str]:
    paths = [
        (HKLM, r"SYSTEM\CurrentControlSet\Services\NvTelemetryContainer", "Start", 4),
    ]
    for root, path, name, val in paths:
        try:
            set_dword(root, path, name, val)
        except OSError:
            pass
    return True, "NVIDIA telemetry service disabled"


def revert_nvidia_telemetry_on() -> tuple[bool, str]:
    try:
        set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\NvTelemetryContainer", "Start", 2)
    except OSError:
        pass
    return True, "NVIDIA telemetry restored"


def apply_disable_mpo() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Microsoft\Windows\Dwm")
    set_dword(HKLM, r"SOFTWARE\Microsoft\Windows\Dwm", "OverlayTestMode", 5)
    return True, "MPO overlay disabled — меньше задержка вывода"


def revert_disable_mpo() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Microsoft\Windows\Dwm", "OverlayTestMode")
    return True, "MPO restored"


def restart_explorer() -> tuple[bool, str]:
    _run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue",
        ],
        timeout=10,
    )
    try:
        subprocess.Popen(
            ["explorer.exe"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True, "Проводник перезапущен"
    except Exception as exc:
        return False, str(exc)


def fix_multimon_display() -> tuple[bool, str]:
    """Откат твиков, которые ломают перенос окон мышью между мониторами."""
    from engine_extra import (
        revert_snap_assist_on,
        revert_transparency_blur_on,
        revert_visual_performance_max,
    )

    parts: list[str] = []
    for label, fn in (
        ("MPO (OverlayTestMode)", revert_disable_mpo),
        ("Monitor latency (DXGKrnl)", revert_monitor_latency),
        ("Blur / прозрачность DWM", revert_transparency_blur_on),
        ("Visual performance UI", revert_visual_performance_max),
        ("Snap Assist", revert_snap_assist_on),
        ("Анимации DWM", revert_dwm_animations_on),
        ("Прозрачность UI", revert_transparency_on),
    ):
        try:
            ok, msg = fn()
            parts.append(f"[{label}] {'OK' if ok else 'ошибка'}: {msg}")
        except Exception as exc:
            parts.append(f"[{label}] ошибка: {exc}")

    ok, msg = restart_explorer()
    parts.append(f"[Explorer] {'OK' if ok else 'ошибка'}: {msg}")

    try:
        set_dword(HKCU, r"Control Panel\Desktop", "DragFullWindows", 1)
        parts.append("[DragFullWindows] OK: включено содержимое окна при перетаскивании")
    except Exception as exc:
        parts.append(f"[DragFullWindows] ошибка: {exc}")

    parts.append("\nПопробуй перетащить окно на второй монитор. Если не помогло — перезагрузи ПК.")
    return True, "\n".join(parts)


def fix_network_browsing() -> tuple[bool, str]:
    """Откат сетевых твиков, которые замедляют сайты, Discord и web-UI (Majestic и др.)."""
    from engine_extra import revert_tcp_interface_nodelay

    parts: list[str] = []
    for label, fn in (
        ("TCP Low Latency (глобальный)", revert_tcp_default),
        ("TCP NoDelay (интерфейсы)", revert_tcp_interface_nodelay),
        ("DNS Cloudflare → DHCP", revert_dns_dhcp),
        ("NDU (Network Diagnostic Usage)", revert_ndu_on),
    ):
        try:
            ok, msg = fn()
            parts.append(f"[{label}] {'OK' if ok else 'ошибка'}: {msg}")
        except Exception as exc:
            parts.append(f"[{label}] ошибка: {exc}")

    ok, msg = _run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            (
                "$eth = Get-NetAdapter -Physical | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -notmatch 'VPN|TAP|Tun' } | Select-Object -First 1; "
                "if ($eth) { Set-DnsClientServerAddress -InterfaceAlias $eth.Name -ResetServerAddresses -ErrorAction SilentlyContinue; "
                "'Основной адаптер: ' + $eth.Name + ' → DNS от роутера' } "
                "else { 'Физический адаптер не найден — проверь DNS вручную' }"
            ),
        ],
        timeout=30,
    )
    parts.append(f"[Ethernet DNS] {'OK' if ok else 'ошибка'}: {msg}")

    parts.append(
        "\nЕсли Radmin VPN / другой VPN включён — он часто имеет приоритет над Ethernet. "
        "Для Discord и браузера отключай VPN, когда не пользуешься им.\n"
        "Перезагрузи ПК или выполни: ipconfig /flushdns"
    )
    return True, "\n".join(parts)


def apply_disable_fso_global() -> tuple[bool, str]:
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_FSEBehaviorMode", 2)
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode", 1)
    set_dword(HKCU, r"System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible", 1)
    return True, "Fullscreen Optimizations отключены глобально"


def revert_disable_fso_global() -> tuple[bool, str]:
    delete_value(HKCU, r"System\GameConfigStore", "GameDVR_HonorUserFSEBehaviorMode")
    delete_value(HKCU, r"System\GameConfigStore", "GameDVR_DXGIHonorFSEWindowsCompatible")
    return True, "FSO settings reverted"


def apply_mouse_queue_size() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters", "MouseDataQueueSize", 0x16)
    return True, "MouseDataQueueSize=22 (shoober420 recommended)"


def revert_mouse_queue_size() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters", "MouseDataQueueSize")
    return True, "Mouse queue reverted"


def apply_keyboard_queue_size() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters", "KeyboardDataQueueSize", 0x16)
    return True, "KeyboardDataQueueSize=22 (shoober420 recommended)"


def revert_keyboard_queue_size() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters", "KeyboardDataQueueSize")
    return True, "Keyboard queue reverted"


def apply_core_parking_off() -> tuple[bool, str]:
    script = r"""
$guid = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
powercfg /setacvalueindex $guid SUB_PROCESSOR CPMINCORES 100
powercfg /setacvalueindex $guid SUB_PROCESSOR CPMAXCORES 100
powercfg /setdcvalueindex $guid SUB_PROCESSOR CPMINCORES 100
powercfg /setdcvalueindex $guid SUB_PROCESSOR CPMAXCORES 100
powercfg /setactive $guid
'Core parking disabled (High Performance)'
"""
    return _ps(script)


def revert_core_parking_on() -> tuple[bool, str]:
    script = r"""
$guid = '8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c'
powercfg /setacvalueindex $guid SUB_PROCESSOR CPMINCORES 10
powercfg /setdcvalueindex $guid SUB_PROCESSOR CPMINCORES 10
powercfg /setactive $guid
'Core parking default'
"""
    return _ps(script)


def apply_diagtrack_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\DiagTrack", "Start", 4)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\dmwappushservice", "Start", 4)
    return True, "DiagTrack telemetry disabled"


def revert_diagtrack_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\DiagTrack", "Start", 3)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\dmwappushservice", "Start", 3)
    return True, "DiagTrack restored"


def apply_ndu_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Ndu", "Start", 4)
    return True, "NDU (Network Diagnostic Usage) disabled"


def revert_ndu_on() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Ndu", "Start", 2)
    return True, "NDU restored"


def apply_delivery_optimization_off() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config", "DODownloadMode", 0)
    return True, "Delivery Optimization disabled"


def revert_delivery_optimization_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\DeliveryOptimization\Config", "DODownloadMode")
    return True, "Delivery Optimization restored"


def apply_win32_priority_26() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 0x26)
    return True, "Win32PrioritySeparation=26 (competitive)"


def revert_win32_priority_26() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Control\PriorityControl", "Win32PrioritySeparation", 0x2)
    return True, "Win32 priority default"


def apply_disable_vbs() -> tuple[bool, str]:
    set_dword(
        HKLM,
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard",
        "EnableVirtualizationBasedSecurity",
        0,
    )
    set_dword(
        HKLM,
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity",
        "Enabled",
        0,
    )
    return True, "VBS / Memory Integrity disabled — +5-10% FPS на части систем. Перезагрузка."


def revert_disable_vbs() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\DeviceGuard", "EnableVirtualizationBasedSecurity")
    set_dword(
        HKLM,
        r"SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity",
        "Enabled",
        1,
    )
    return True, "VBS re-enabled — reboot required"


def apply_ultimate_power_plan() -> tuple[bool, str]:
    script = r"""
$ult = 'e9a42b02-d5df-448d-aa00-03f14749eb61'
powercfg /duplicatescheme $ult 2>$null | Out-Null
powercfg /setactive $ult
'Ultimate Performance power plan activated'
"""
    return _ps(script)


def revert_high_performance_plan() -> tuple[bool, str]:
    _run(["powercfg", "/setactive", "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"])
    return True, "High Performance plan activated"


def apply_disable_cstates() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Processor\Power", "Cstates", 0)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Processor\Power", "PerfEnablePackageIdle", 0)
    return True, "CPU C-States reduced"


def revert_disable_cstates() -> tuple[bool, str]:
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\Processor\Power", "Cstates")
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Services\Processor\Power", "PerfEnablePackageIdle")
    return True, "C-States restored"


def apply_dwm_animations_off() -> tuple[bool, str]:
    set_dword(HKCU, r"Control Panel\Desktop\WindowMetrics", "MinAnimate", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAnimations", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\DWM", "EnableAeroPeek", 0)
    return True, "DWM animations reduced"


def revert_dwm_animations_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Control Panel\Desktop\WindowMetrics", "MinAnimate")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAnimations")
    return True, "DWM animations restored"


def apply_directx_tweaks() -> tuple[bool, str]:
    set_dword(HKLM, r"SOFTWARE\Microsoft\DirectDraw", "EmulationOnly", 0)
    set_dword(HKLM, r"SOFTWARE\Microsoft\Direct3D", "DisableVidMemVBs", 0)
    set_dword(HKLM, r"SOFTWARE\Microsoft\Direct3D\Drivers", "SoftwareOnly", 0)
    return True, "DirectX registry optimizations applied"


def revert_directx_tweaks() -> tuple[bool, str]:
    for path, name in (
        (r"SOFTWARE\Microsoft\DirectDraw", "EmulationOnly"),
        (r"SOFTWARE\Microsoft\Direct3D", "DisableVidMemVBs"),
        (r"SOFTWARE\Microsoft\Direct3D\Drivers", "SoftwareOnly"),
    ):
        delete_value(HKLM, path, name)
    return True, "DirectX tweaks reverted"


def apply_xbox_services_off() -> tuple[bool, str]:
    for svc in ("XblAuthManager", "XblGameSave", "XboxGipSvc", "XboxNetApiSvc"):
        try:
            set_dword(HKLM, rf"SYSTEM\CurrentControlSet\Services\{svc}", "Start", 4)
        except OSError:
            pass
    return True, "Xbox services disabled"


def revert_xbox_services_on() -> tuple[bool, str]:
    for svc, start in (("XblAuthManager", 3), ("XblGameSave", 3), ("XboxNetApiSvc", 3)):
        try:
            set_dword(HKLM, rf"SYSTEM\CurrentControlSet\Services\{svc}", "Start", start)
        except OSError:
            pass
    return True, "Xbox services restored"


def apply_disable_hpet_bcd() -> tuple[bool, str]:
    ok1, o1 = _run(["bcdedit", "/deletevalue", "useplatformclock"])
    ok2, o2 = _run(["bcdedit", "/set", "disabledynamictick", "yes"])
    return ok2, "\n".join(filter(None, [o1, o2]))


def revert_disable_hpet_bcd() -> tuple[bool, str]:
    _run(["bcdedit", "/deletevalue", "disabledynamictick"])
    return True, "BCD HPET settings reverted"


def apply_csrss_priority() -> tuple[bool, str]:
    path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\csrss.exe\PerfOptions"
    ensure_key(HKLM, path)
    set_dword(HKLM, path, "CpuPriorityClass", 4)
    set_dword(HKLM, path, "IoPriority", 3)
    return True, "CSRSS high priority (xiaumm)"


def revert_csrss_priority() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\csrss.exe\PerfOptions",
        "CpuPriorityClass",
    )
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\csrss.exe\PerfOptions",
        "IoPriority",
    )
    return True, "CSRSS priority reverted"


def apply_content_delivery_off() -> tuple[bool, str]:
    cdm = r"Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
    for name, val in (
        ("SystemPaneSuggestionsEnabled", 0),
        ("SoftLandingEnabled", 0),
        ("SubscribedContent-338388Enabled", 0),
        ("SubscribedContent-310093Enabled", 0),
        ("SubscribedContent-338389Enabled", 0),
        ("SubscribedContent-353694Enabled", 0),
        ("SubscribedContent-353696Enabled", 0),
    ):
        set_dword(HKCU, cdm, name, val)
    return True, "Windows suggestions / ads disabled"


def revert_content_delivery_on() -> tuple[bool, str]:
    return True, "Content delivery — включите вручную в параметрах Windows"


def apply_disable_pointer_shadow() -> tuple[bool, str]:
    set_dword(HKCU, r"Control Panel\Cursors", "CursorShadow", 0)
    return True, "Cursor shadow disabled"


def revert_disable_pointer_shadow() -> tuple[bool, str]:
    delete_value(HKCU, r"Control Panel\Cursors", "CursorShadow")
    return True, "Cursor shadow restored"


def apply_nic_power_off() -> tuple[bool, str]:
    script = r"""
Get-CimInstance Win32_NetworkAdapter | Where-Object { $_.PNPDeviceID -match 'PCI\\' } | ForEach-Object {
    $pnp = $_.PNPDeviceID
    $pm = Get-CimInstance -NS root\wmi -Class MSPower_DeviceEnable -EA 0 |
        Where-Object { $_.InstanceName -like "*$pnp*" }
    foreach ($i in $pm) { Set-CimInstance $i -Property @{ Enable = $false } -EA 0 }
}
'NIC power saving disabled'
"""
    return _ps(script)


def revert_nic_power_on() -> tuple[bool, str]:
    return True, "NIC power — включите в свойствах адаптера вручную"


def apply_auto_end_tasks() -> tuple[bool, str]:
    set_string(HKCU, r"Control Panel\Desktop", "AutoEndTasks", "1")
    set_string(HKCU, r"Control Panel\Desktop", "WaitToKillAppTimeout", "2000")
    set_string(HKLM, r"SYSTEM\CurrentControlSet\Control", "WaitToKillServiceTimeout", "2000")
    return True, "Auto end tasks enabled"


def revert_auto_end_tasks() -> tuple[bool, str]:
    set_string(HKCU, r"Control Panel\Desktop", "WaitToKillAppTimeout", "5000")
    return True, "Auto end tasks reverted"


def apply_defender_off() -> tuple[bool, str]:
    defender = r"SOFTWARE\Policies\Microsoft\Windows Defender"
    rtp = defender + r"\Real-Time Protection"
    ensure_key(HKLM, defender)
    ensure_key(HKLM, rtp)
    for path, name, val in (
        (defender, "DisableAntiSpyware", 1),
        (defender, "DisableRoutinelyTakingAction", 1),
        (defender, "ServiceKeepAlive", 0),
        (rtp, "DisableRealtimeMonitoring", 1),
        (rtp, "DisableBehaviorMonitoring", 1),
        (rtp, "DisableOnAccessProtection", 1),
        (rtp, "DisableIOAVProtection", 1),
        (rtp, "DisableScriptScanning", 1),
        (rtp, "DisableRawWriteNotification", 1),
    ):
        set_dword(HKLM, path, name, val)
    for svc in ("WinDefend", "WdNisSvc", "Sense", "SecurityHealthService"):
        try:
            set_dword(HKLM, rf"SYSTEM\CurrentControlSet\Services\{svc}", "Start", 4)
        except OSError:
            pass
    script = r"""
try { Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction Stop } catch {}
try { Set-MpPreference -DisableIOAVProtection $true -ErrorAction Stop } catch {}
try { Set-MpPreference -DisableBehaviorMonitoring $true -ErrorAction Stop } catch {}
Stop-Service -Name WinDefend -Force -ErrorAction SilentlyContinue
Stop-Service -Name WdNisSvc -Force -ErrorAction SilentlyContinue
'Windows Defender disabled'
"""
    ok, msg = _ps(script, timeout=90)
    return ok, msg or "Windows Defender disabled (reboot recommended)"


def revert_defender_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows Defender", "DisableAntiSpyware")
    delete_value(
        HKLM,
        r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection",
        "DisableRealtimeMonitoring",
    )
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WinDefend", "Start", 2)
    _ps("try { Set-MpPreference -DisableRealtimeMonitoring $false } catch {}")
    return True, "Defender restored — reboot and check Windows Security"


def _apply_dwords(entries: list[tuple[int, str, str, int]]) -> None:
    for root, path, name, value in entries:
        ensure_key(root, path)
        set_dword(root, path, name, value)


def _revert_dwords(entries: list[tuple[int, str, str]]) -> None:
    for root, path, name in entries:
        delete_value(root, path, name)


def apply_hidusb_low_latency() -> tuple[bool, str]:
    """shoober420 InputTweaks — USB HID low-latency path."""
    hid = r"SYSTEM\CurrentControlSet\Services\HidUsb\Parameters"
    _apply_dwords([
        (HKLM, hid, "ForceLowLatencyMode", 1),
        (HKLM, hid, "ForceLowestInputLatency", 1),
        (HKLM, hid, "LowLatencyMode", 1),
        (HKLM, hid, "DisableSelectiveSuspend", 1),
        (HKLM, hid, "SelectiveSuspendEnabled", 0),
        (HKLM, hid, "DeviceSelectiveSuspended", 0),
        (HKLM, hid, "InterruptCoalescingEnabled", 0),
        (HKLM, hid, "InterruptLatencyOptimization", 1),
        (HKLM, hid, "DisableDebouncing", 1),
        (HKLM, hid, "DisableIdleTimer", 1),
        (HKLM, hid, "IdleEnabled", 0),
        (HKLM, hid, "EnhancedPowerManagementEnabled", 0),
        (HKLM, hid, "UseUsbHidPollingRate", 1),
    ])
    return True, "HidUsb low-latency mode enabled (reboot recommended)"


def revert_hidusb_low_latency() -> tuple[bool, str]:
    hid = r"SYSTEM\CurrentControlSet\Services\HidUsb\Parameters"
    _revert_dwords([(HKLM, hid, n) for n in (
        "ForceLowLatencyMode", "ForceLowestInputLatency", "LowLatencyMode",
        "DisableSelectiveSuspend", "SelectiveSuspendEnabled", "DeviceSelectiveSuspended",
        "InterruptCoalescingEnabled", "InterruptLatencyOptimization", "DisableDebouncing",
        "DisableIdleTimer", "IdleEnabled", "EnhancedPowerManagementEnabled", "UseUsbHidPollingRate",
    )])
    return True, "HidUsb parameters reverted"


def apply_raw_input_priority() -> tuple[bool, str]:
    """Microsoft Input + MOUSE_RAW_INPUT — приоритет raw input."""
    ensure_key(HKLM, r"SOFTWARE\Microsoft\Input")
    set_dword(HKLM, r"SOFTWARE\Microsoft\Input", "EnableRawInputHighPriority", 1)
    set_dword(HKLM, r"SOFTWARE\Microsoft\Input", "AllowRawInputExclusive", 1)
    set_string(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "MOUSE_RAW_INPUT", "1")
    return True, "Raw input high priority enabled"


def revert_raw_input_priority() -> tuple[bool, str]:
    _revert_dwords([
        (HKLM, r"SOFTWARE\Microsoft\Input", "EnableRawInputHighPriority"),
        (HKLM, r"SOFTWARE\Microsoft\Input", "AllowRawInputExclusive"),
    ])
    delete_value(HKLM, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment", "MOUSE_RAW_INPUT")
    return True, "Raw input priority reverted"


def apply_input_layered_latency() -> tuple[bool, str]:
    """LayeredLatency=0 для kbd/mou — shoober420 / RegentSnatch."""
    paths = (
        r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
        r"SYSTEM\CurrentControlSet\Services\kbdhid\Parameters",
        r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
        r"SYSTEM\CurrentControlSet\Services\mouhid\Parameters",
    )
    for path in paths:
        set_dword(HKLM, path, "LayeredLatency", 0)
    return True, "LayeredLatency=0 for keyboard/mouse"


def revert_input_layered_latency() -> tuple[bool, str]:
    paths = (
        r"SYSTEM\CurrentControlSet\Services\kbdclass\Parameters",
        r"SYSTEM\CurrentControlSet\Services\kbdhid\Parameters",
        r"SYSTEM\CurrentControlSet\Services\mouclass\Parameters",
        r"SYSTEM\CurrentControlSet\Services\mouhid\Parameters",
    )
    for path in paths:
        delete_value(HKLM, path, "LayeredLatency")
    return True, "LayeredLatency reverted"


def apply_keyboard_fast_delays() -> tuple[bool, str]:
    """Короткая задержка и быстрый повтор клавиш (Backspace, стрелки и т.д.)."""
    set_dword(HKCU, r"Control Panel\Keyboard", "KeyboardDelay", 3)
    set_dword(HKCU, r"Control Panel\Keyboard", "KeyboardSpeed", 31)
    delete_value(HKCU, r"Control Panel\Keyboard", "TypematicDelay")
    delete_value(HKCU, r"Control Panel\Desktop", "KeyboardSpeed")
    return True, "Keyboard delay=3, speed=31 (быстрый повтор)"


def revert_keyboard_fast_delays() -> tuple[bool, str]:
    set_dword(HKCU, r"Control Panel\Keyboard", "KeyboardDelay", 1)
    set_dword(HKCU, r"Control Panel\Keyboard", "KeyboardSpeed", 31)
    delete_value(HKCU, r"Control Panel\Keyboard", "TypematicDelay")
    delete_value(HKCU, r"Control Panel\Desktop", "KeyboardSpeed")
    return True, "Keyboard delays restored"


def apply_cursor_fast_update() -> tuple[bool, str]:
    set_dword(
        HKLM,
        r"SOFTWARE\Microsoft\Input\Settings\ControllerProcessor\CursorSpeed",
        "CursorUpdateInterval",
        1,
    )
    return True, "CursorUpdateInterval=1"


def revert_cursor_fast_update() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SOFTWARE\Microsoft\Input\Settings\ControllerProcessor\CursorSpeed",
        "CursorUpdateInterval",
    )
    return True, "Cursor update interval reverted"


def apply_gpu_power_latency_pack() -> tuple[bool, str]:
    """Ключевые GraphicsDrivers/Power latency — shoober420 GPUTweaks (подмножество)."""
    gd = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    gdp = gd + r"\Power"
    _apply_dwords([
        (HKLM, gdp, "LOWLATENCY", 1),
        (HKLM, gdp, "D3PCLatency", 1),
        (HKLM, gdp, "TransitionLatency", 1),
        (HKLM, gdp, "Node3DLowLatency", 1),
        (HKLM, gdp, "UseGpuTimer", 1),
        (HKLM, gdp, "PowerSavingTweaks", 0),
        (HKLM, gdp, "EnableRuntimePowerManagement", 0),
        (HKLM, gdp, "FlTransitionLatency", 1),
        (HKLM, gd, "LatencyToleranceDefault", 1),
        (HKLM, gd, "ForceLowLatencyDisplayMode", 1),
    ])
    return True, "GPU power/latency pack applied (reboot recommended)"


def revert_gpu_power_latency_pack() -> tuple[bool, str]:
    gd = r"SYSTEM\CurrentControlSet\Control\GraphicsDrivers"
    gdp = gd + r"\Power"
    names = (
        "LOWLATENCY", "D3PCLatency", "TransitionLatency", "Node3DLowLatency",
        "UseGpuTimer", "PowerSavingTweaks", "EnableRuntimePowerManagement",
        "FlTransitionLatency",
    )
    _revert_dwords([(HKLM, gdp, n) for n in names])
    _revert_dwords([
        (HKLM, gd, "LatencyToleranceDefault"),
        (HKLM, gd, "ForceLowLatencyDisplayMode"),
    ])
    return True, "GPU power/latency pack reverted"


def apply_power_latency_pack() -> tuple[bool, str]:
    """Control\\Power latency tolerance — shoober420 / TGO."""
    pwr = r"SYSTEM\CurrentControlSet\Control\Power"
    _apply_dwords([
        (HKLM, pwr, "ExitLatency", 1),
        (HKLM, pwr, "LatencyToleranceDefault", 1),
        (HKLM, pwr, "LatencyTolerancePerfOverride", 1),
        (HKLM, pwr, "DisableVsyncLatencyUpdate", 1),
        (HKLM, pwr, "CsEnabled", 0),
        (HKLM, pwr, "QosManagesIdleProcessors", 0),
    ])
    return True, "Power latency pack applied"


def revert_power_latency_pack() -> tuple[bool, str]:
    pwr = r"SYSTEM\CurrentControlSet\Control\Power"
    _revert_dwords([(HKLM, pwr, n) for n in (
        "ExitLatency", "LatencyToleranceDefault", "LatencyTolerancePerfOverride",
        "DisableVsyncLatencyUpdate", "CsEnabled", "QosManagesIdleProcessors",
    )])
    return True, "Power latency pack reverted"


def apply_windowed_games_opt() -> tuple[bool, str]:
    """Оптимизация оконных игр — Win11 gaming guides / DirectX UserGpuPreferences."""
    set_string(
        HKCU,
        r"Software\Microsoft\DirectX\UserGpuPreferences",
        "DirectXUserGlobalSettings",
        "SwapEffectUpgradeEnable=1;",
    )
    set_dword(HKCU, r"Software\Microsoft\GameBar", "AutoGameModeEnabled", 1)
    set_dword(HKCU, r"Software\Microsoft\GameBar", "AllowAutoGameMode", 1)
    return True, "Windowed games optimization enabled"


def revert_windowed_games_opt() -> tuple[bool, str]:
    delete_value(HKCU, r"Software\Microsoft\DirectX\UserGpuPreferences", "DirectXUserGlobalSettings")
    delete_value(HKCU, r"Software\Microsoft\GameBar", "AutoGameModeEnabled")
    delete_value(HKCU, r"Software\Microsoft\GameBar", "AllowAutoGameMode")
    return True, "Windowed games optimization reverted"


def apply_memory_compression_off() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "EnableCompressedMemory", 0)
    ok, msg = _ps("try { Disable-MMAgent -MemoryCompression -ErrorAction Stop; 'OK' } catch { $_.Exception.Message }")
    return ok, msg or "Memory compression disabled (reboot recommended)"


def revert_memory_compression_on() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    delete_value(HKLM, mm, "EnableCompressedMemory")
    _ps("try { Enable-MMAgent -MemoryCompression } catch {}")
    return True, "Memory compression restored"


def apply_disable_page_combining() -> tuple[bool, str]:
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "DisablePageCombining", 1)
    return True, "DisablePageCombining=1"


def revert_disable_page_combining() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "DisablePageCombining",
    )
    return True, "Page combining restored"


def apply_io_page_lock_limit() -> tuple[bool, str]:
    """IoPageLockLimit — игровые пакеты оптимизации памяти."""
    mm = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management"
    set_dword(HKLM, mm, "IoPageLockLimit", 0xF0000)
    return True, "IoPageLockLimit=983040"


def revert_io_page_lock_limit() -> tuple[bool, str]:
    delete_value(
        HKLM,
        r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management",
        "IoPageLockLimit",
    )
    return True, "IoPageLockLimit reverted"


def apply_disable_prefetch_gaming() -> tuple[bool, str]:
    pref = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    set_dword(HKLM, pref, "EnablePrefetcher", 0)
    return True, "Prefetcher disabled (gaming)"


def revert_disable_prefetch_gaming() -> tuple[bool, str]:
    pref = r"SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters"
    set_dword(HKLM, pref, "EnablePrefetcher", 3)
    return True, "Prefetcher restored"


def apply_telemetry_policies_off() -> tuple[bool, str]:
    """Телеметрия — Sophia / Win11Debloat / Atlas."""
    paths = (
        (r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0),
        (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection", "AllowTelemetry", 0),
        (r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications", 1),
        (r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DisableEnterpriseAuthProxy", 1),
    )
    for path, name, val in paths:
        ensure_key(HKLM, path)
        set_dword(HKLM, path, name, val)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\dmwappushservice", "Start", 4)
    return True, "Telemetry policies applied"


def revert_telemetry_policies_on() -> tuple[bool, str]:
    _revert_dwords([
        (HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry"),
        (HKLM, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection", "AllowTelemetry"),
        (HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DoNotShowFeedbackNotifications"),
        (HKLM, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "DisableEnterpriseAuthProxy"),
    ])
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\dmwappushservice", "Start", 3)
    return True, "Telemetry policies reverted"


def apply_cortana_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana", 0)
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "CortanaEnabled", 0)
    return True, "Cortana disabled"


def revert_cortana_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Search", "AllowCortana")
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Search", "CortanaEnabled")
    return True, "Cortana policy reverted"


def apply_error_reporting_off() -> tuple[bool, str]:
    wer = r"SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting"
    ensure_key(HKLM, wer)
    set_dword(HKLM, wer, "Disabled", 1)
    set_dword(HKLM, wer, "DontSendAdditionalData", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WerSvc", "Start", 4)
    return True, "Windows Error Reporting disabled"


def revert_error_reporting_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting", "Disabled")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting", "DontSendAdditionalData")
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\WerSvc", "Start", 3)
    return True, "Error reporting restored"


def apply_widgets_off() -> tuple[bool, str]:
    """Виджеты / лента новостей — Win11Debloat."""
    set_dword(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa", 0)
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests", 0)
    return True, "Widgets / news feed disabled"


def revert_widgets_on() -> tuple[bool, str]:
    delete_value(HKCU, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarDa")
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Dsh", "AllowNewsAndInterests")
    return True, "Widgets settings reverted"


def apply_audio_mmcss_pro() -> tuple[bool, str]:
    """MMCSS Pro Audio — Win11 gaming optimizer / low audio latency."""
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Pro Audio"
    ensure_key(HKLM, base)
    set_dword(HKLM, base, "Affinity", 0)
    set_dword(HKLM, base, "Background Only", 0)
    set_dword(HKLM, base, "Clock Rate", 10000)
    set_dword(HKLM, base, "GPU Priority", 18)
    set_dword(HKLM, base, "Priority", 6)
    set_string(HKLM, base, "Scheduling Category", "High")
    set_string(HKLM, base, "SFIO Priority", "High")
    return True, "MMCSS Pro Audio profile tuned"


def revert_audio_mmcss_pro() -> tuple[bool, str]:
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Pro Audio"
    for name in ("Affinity", "Background Only", "Clock Rate", "GPU Priority", "Priority",
                 "Scheduling Category", "SFIO Priority"):
        delete_value(HKLM, base, name)
    return True, "MMCSS Pro Audio reverted"


def apply_disable_print_spooler() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Spooler", "Start", 4)
    _ps("Stop-Service -Name Spooler -Force -ErrorAction SilentlyContinue")
    return True, "Print Spooler disabled"


def revert_disable_print_spooler() -> tuple[bool, str]:
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\Spooler", "Start", 2)
    return True, "Print Spooler restored (manual start)"


def apply_dns_cloudflare() -> tuple[bool, str]:
    """DNS 1.1.1.1 / 1.0.0.1 — снижает DNS-задержку."""
    script = r"""
$ok = $false
Get-DnsClient | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } | ForEach-Object {
    try {
        Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex -ServerAddresses ('1.1.1.1','1.0.0.1') -ErrorAction Stop
        $ok = $true
    } catch {}
}
if ($ok) { 'Cloudflare DNS applied' } else { 'No active adapters updated' }
"""
    return _ps(script)


def revert_dns_dhcp() -> tuple[bool, str]:
    script = r"""
Get-DnsClient | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } | ForEach-Object {
    try { Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex -ResetServerAddresses -ErrorAction Stop } catch {}
}
'DNS reset to DHCP'
"""
    return _ps(script)


def apply_ssd_trim() -> tuple[bool, str]:
    ok, msg = _run(["fsutil", "behavior", "set", "DisableDeleteNotify", "0"], timeout=15)
    note = "TRIM включён. Оптимизацию диска запустите вручную: Параметры → Система → Память устройств."
    return ok, (msg or note) if ok else (msg or "Ошибка fsutil")


def revert_ssd_trim_info() -> tuple[bool, str]:
    return True, "TRIM left enabled (safe default); run defrag manually if needed"


def apply_location_off() -> tuple[bool, str]:
    ensure_key(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors")
    set_dword(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "DisableLocation", 1)
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\lfsvc", "Start", 4)
    return True, "Location services disabled"


def revert_location_on() -> tuple[bool, str]:
    delete_value(HKLM, r"SOFTWARE\Policies\Microsoft\Windows\LocationAndSensors", "DisableLocation")
    set_dword(HKLM, r"SYSTEM\CurrentControlSet\Services\lfsvc", "Start", 3)
    return True, "Location services restored"


ApplyFn = Callable[[], tuple[bool, str]]
RevertFn = Callable[[], tuple[bool, str]]
