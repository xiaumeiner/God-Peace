"""Windows service helpers."""

from __future__ import annotations

from core.registry import HKLM, delete_value, set_dword
from core.shell import powershell, run


def set_start(service: str, start_type: int, *, stop_running: bool = False) -> tuple[bool, str]:
    """Set service Start value and optionally stop it.

    start_type: 2=auto, 3=demand, 4=disabled
    """
    path = rf"SYSTEM\CurrentControlSet\Services\{service}"
    set_dword(HKLM, path, "Start", start_type)
    if stop_running:
        return powershell(f"Stop-Service -Name '{service}' -Force -ErrorAction SilentlyContinue")
    return True, f"{service} Start={start_type}"


def start_service(service: str) -> tuple[bool, str]:
    return powershell(f"Start-Service -Name '{service}' -ErrorAction SilentlyContinue")


def stop_service(service: str) -> tuple[bool, str]:
    return powershell(f"Stop-Service -Name '{service}' -Force -ErrorAction SilentlyContinue")
