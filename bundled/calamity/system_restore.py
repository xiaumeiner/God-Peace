"""Создание точки восстановления Windows."""

from __future__ import annotations

import subprocess
from datetime import datetime


def create_restore_point(label: str = "Calamity v2") -> tuple[bool, str]:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    desc = f"{label} — {stamp}"
    safe_desc = desc.replace("'", "''")

    script = f"""
$ErrorActionPreference = 'Stop'
$desc = '{safe_desc}'
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
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120,
        )
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        if result.returncode == 0 and out.startswith("OK:"):
            return True, out[4:].strip()
        if out.startswith("ERR:"):
            return False, out[4:].strip()
        return False, out or "Не удалось создать точку восстановления"
    except subprocess.TimeoutExpired:
        return False, "Таймаут 120 с — включите восстановление системы в параметрах Windows"
    except Exception as exc:
        return False, str(exc)
