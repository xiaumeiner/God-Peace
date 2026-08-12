"""System-level helpers: admin check, restore points, reboot."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from core.shell import powershell, run


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> None:
    params = " ".join(f'"{arg}"' for arg in sys.argv)
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)


def create_restore_point(label: str = "God Peace") -> tuple[bool, str]:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    desc = f"{label} — {stamp}".replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
$desc = '{desc}'
$drive = $env:SystemDrive + '\\'
try {{
    $svc = Get-Service -Name swprv -ErrorAction SilentlyContinue
    if ($svc -and $svc.Status -ne 'Running') {{
        Start-Service swprv -ErrorAction SilentlyContinue
    }}
    Enable-ComputerRestore -Drive $drive -ErrorAction SilentlyContinue | Out-Null
    $reg = 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore'
    $prevFreq = $null
    if (Test-Path $reg) {{
        $prevFreq = (Get-ItemProperty $reg -Name SystemRestorePointCreationFrequency -EA 0).SystemRestorePointCreationFrequency
        Set-ItemProperty $reg -Name SystemRestorePointCreationFrequency -Value 0 -EA 0
    }}
    Checkpoint-Computer -Description $desc -RestorePointType MODIFY_SETTINGS
    if ($null -ne $prevFreq) {{
        Set-ItemProperty $reg -Name SystemRestorePointCreationFrequency -Value $prevFreq -EA 0
    }}
    Write-Output ('OK: ' + $desc)
}} catch {{
    Write-Output ('ERR: ' + $_.Exception.Message)
    exit 1
}}
"""
    ok, msg = powershell(script, timeout=120)
    if ok and msg.startswith("OK:"):
        return True, msg[4:].strip()
    return False, msg or "Не удалось создать точку восстановления"


def open_system_restore() -> None:
    subprocess.Popen(["rstrui.exe"], creationflags=subprocess.CREATE_NO_WINDOW)


def restart_explorer() -> tuple[bool, str]:
    run(["powershell", "-NoProfile", "-Command", "Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue"], timeout=10)
    try:
        subprocess.Popen(["explorer.exe"], creationflags=subprocess.CREATE_NO_WINDOW)
        return True, "Проводник перезапущен"
    except Exception as exc:
        return False, str(exc)


def flush_dns() -> tuple[bool, str]:
    return run(["ipconfig", "/flushdns"], timeout=30)
