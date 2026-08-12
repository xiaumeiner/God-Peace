"""God Peace extra tweaks from Desktop/2321 + TCP autotune."""

from __future__ import annotations

import subprocess
import winreg
from collections.abc import Callable
from dataclasses import dataclass

CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW


@dataclass(frozen=True)
class ExtraTweak:
    id: str
    name: str
    apply_fn: Callable[[], tuple[bool, str]]
    revert_fn: Callable[[], tuple[bool, str]]


def _run(cmd: list[str], timeout: int = 60) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
            timeout=timeout,
        )
        out = ((result.stdout or "") + (result.stderr or "")).strip()
        return result.returncode == 0, out or "OK"
    except subprocess.TimeoutExpired:
        return False, f"Таймаут: {' '.join(cmd[:4])}"
    except OSError as exc:
        return False, str(exc)


def _run_ps(script: str, timeout: int = 90) -> tuple[bool, str]:
    return _run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
    )


def _delete_value(root: int, path: str, name: str) -> None:
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
    except OSError:
        pass


def _set_dword(root: int, path: str, name: str, value: int) -> None:
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
    finally:
        winreg.CloseKey(key)


def _set_string(root: int, path: str, name: str, value: str) -> None:
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    finally:
        winreg.CloseKey(key)


# --- Network (fix_network.ps1 + netsh autotune) ---

def apply_network_fix() -> tuple[bool, str]:
    tcp_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters"
    for name in ("TCPNoDelay", "TcpAckFrequency", "TCPDelAckTicks"):
        _delete_value(winreg.HKEY_LOCAL_MACHINE, tcp_path, name)

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, tcp_path + r"\Interfaces", 0, winreg.KEY_READ) as interfaces:
            index = 0
            while True:
                try:
                    sub = winreg.EnumKey(interfaces, index)
                    iface_path = tcp_path + r"\Interfaces\\" + sub
                    for name in ("TcpAckFrequency", "TCPNoDelay"):
                        _delete_value(winreg.HKEY_LOCAL_MACHINE, iface_path, name)
                    index += 1
                except OSError:
                    break
    except OSError:
        pass

    _set_dword(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\Ndu", "Start", 2)

    ok_dns, msg_dns = _run_ps(
        "Get-DnsClient | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' } | "
        "ForEach-Object { Set-DnsClientServerAddress -InterfaceIndex $_.InterfaceIndex "
        "-ResetServerAddresses -ErrorAction SilentlyContinue }"
    )
    _run(["ipconfig", "/flushdns"], timeout=30)
    ok_tune, msg_tune = _run(["netsh", "interface", "tcp", "set", "global", "autotuninglevel=normal"])

    if ok_tune:
        return True, "TCP/DNS сброшены, autotuninglevel=normal"
    return False, msg_tune or msg_dns


def revert_network_fix() -> tuple[bool, str]:
    ok, msg = _run(["netsh", "interface", "tcp", "set", "global", "autotuninglevel=disabled"])
    return ok, msg or "autotune=disabled"


# --- Keyboard (fix_keyboard.ps1) ---

def apply_keyboard_fix() -> tuple[bool, str]:
    kb = r"Control Panel\Keyboard"
    _set_string(winreg.HKEY_CURRENT_USER, kb, "KeyboardDelay", "3")
    _set_string(winreg.HKEY_CURRENT_USER, kb, "KeyboardSpeed", "31")
    _delete_value(winreg.HKEY_CURRENT_USER, kb, "TypematicDelay")
    _delete_value(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "KeyboardSpeed")
    return True, "KeyboardDelay=3, KeyboardSpeed=31"


def revert_keyboard_fix() -> tuple[bool, str]:
    kb = r"Control Panel\Keyboard"
    _set_string(winreg.HKEY_CURRENT_USER, kb, "KeyboardDelay", "1")
    _set_string(winreg.HKEY_CURRENT_USER, kb, "KeyboardSpeed", "31")
    return True, "Клавиатура: значения по умолчанию"


# --- Multi-monitor (fix_multimon.ps1) ---

def apply_multimon_fix() -> tuple[bool, str]:
    dwm = r"SOFTWARE\Microsoft\Windows\Dwm"
    dxg = r"SYSTEM\CurrentControlSet\Services\DXGKrnl"
    for path, name in (
        (dwm, "OverlayTestMode"),
        (dxg, "MonitorLatencyTolerance"),
        (dxg, "MonitorRefreshLatencyTolerance"),
    ):
        _delete_value(winreg.HKEY_LOCAL_MACHINE, path, name)

    _run_ps("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Process explorer")
    return True, "MPO/overlay сняты, Explorer перезапущен"


def revert_multimon_fix() -> tuple[bool, str]:
    _set_dword(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\Dwm", "OverlayTestMode", 5)
    return True, "OverlayTestMode=5 (MPO off)"


# --- Window drag (fix_window_drag.ps1) ---

def apply_window_drag_fix() -> tuple[bool, str]:
    _set_string(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "DragFullWindows", "1")
    return True, "DragFullWindows=1"


def revert_window_drag_fix() -> tuple[bool, str]:
    _set_string(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "DragFullWindows", "0")
    return True, "DragFullWindows=0"


EXTRA_TWEAKS: list[ExtraTweak] = [
    ExtraTweak("gp_network", "Сеть: TCP/DNS + autotune normal", apply_network_fix, revert_network_fix),
    ExtraTweak("gp_keyboard", "Клавиатура: быстрый повтор", apply_keyboard_fix, revert_keyboard_fix),
    ExtraTweak("gp_multimon", "Мультимonitor: drag fix", apply_multimon_fix, revert_multimon_fix),
    ExtraTweak("gp_window_drag", "Окна: содержимое при перетаскивании", apply_window_drag_fix, revert_window_drag_fix),
]

EXTRA_BY_ID = {t.id: t for t in EXTRA_TWEAKS}


def run_extra_tweaks(
    on_progress: Callable[[int, int, str], None] | None = None,
    offset: int = 0,
    total_base: int = 0,
) -> tuple[int, int, list[str], list[str]]:
    total = total_base + len(EXTRA_TWEAKS)
    ok_count = 0
    errors: list[str] = []
    applied: list[str] = []

    for i, tweak in enumerate(EXTRA_TWEAKS, 1):
        step = offset + i
        if on_progress:
            on_progress(step, total, tweak.name)
        ok, msg = tweak.apply_fn()
        if ok:
            ok_count += 1
            applied.append(tweak.id)
        else:
            errors.append(f"{tweak.name}: {msg[:120]}")

    return ok_count, len(EXTRA_TWEAKS), errors, applied


def revert_extra_tweaks(
    tweak_ids: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
) -> tuple[int, int, list[str], list[str]]:
    selected = [EXTRA_BY_ID[i] for i in tweak_ids if i in EXTRA_BY_ID]
    total = len(selected)
    ok_count = 0
    errors: list[str] = []
    reverted: list[str] = []

    for i, tweak in enumerate(selected, 1):
        if on_progress:
            on_progress(i, total, tweak.name)
        ok, msg = tweak.revert_fn()
        if ok:
            ok_count += 1
            reverted.append(tweak.id)
        else:
            errors.append(f"{tweak.name}: {msg[:120]}")

    return ok_count, total, errors, reverted
