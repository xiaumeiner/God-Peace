"""Minimal system status snapshot."""

from __future__ import annotations

import ctypes
import time

from calamity_runner import is_admin
from hub_state import has_applied_tweaks
from mapmark_launcher import is_installed as mapmark_installed

_STATIC_TTL = 30.0
_static_cache: tuple[bool, bool, bool] | None = None
_static_at = 0.0


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def ram_percent() -> int:
    stat = MEMORYSTATUSEX()
    stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
        return 0
    return int(stat.dwMemoryLoad)


def _static_fields() -> tuple[bool, bool, bool]:
    global _static_cache, _static_at
    now = time.monotonic()
    if _static_cache is not None and now - _static_at < _STATIC_TTL:
        return _static_cache
    _static_cache = (is_admin(), mapmark_installed(), has_applied_tweaks())
    _static_at = now
    return _static_cache


def invalidate_static_cache() -> None:
    global _static_cache, _static_at
    _static_cache = None
    _static_at = 0.0


def snapshot(*, refresh_static: bool = False) -> dict[str, object]:
    if refresh_static:
        invalidate_static_cache()
    admin, mapmark, optimized = _static_fields()
    return {
        "ram": ram_percent(),
        "admin": admin,
        "mapmark": mapmark,
        "optimized": optimized,
    }


def format_status_line(data: dict[str, object] | None = None) -> str:
    s = data or snapshot()
    ram = s.get("ram", 0)
    admin = "ON" if s.get("admin") else "OFF"
    mm = "OK" if s.get("mapmark") else "—"
    opt = "YES" if s.get("optimized") else "—"
    return f"RAM {ram}%   ·   ADMIN {admin}   ·   MAP {mm}   ·   TWEAKED {opt}"
