"""MapMark — bundled installer or launch if already installed."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from config import BUNDLED_DIR, MAPMARK_INSTALLER

MAPMARK_INSTALLED_PATHS = (
    Path(r"C:\Program Files\MapMark\MapMark.exe"),
    Path.home() / "AppData" / "Local" / "Programs" / "MapMark" / "MapMark.exe",
)


def installer_path() -> Path:
    return MAPMARK_INSTALLER


def bundle_ready() -> bool:
    return MAPMARK_INSTALLER.is_file()


def is_installed() -> bool:
    return find_installed_exe() is not None


def find_installed_exe() -> Path | None:
    for path in MAPMARK_INSTALLED_PATHS:
        if path.is_file():
            return path
    return None


def run_installer() -> tuple[bool, str]:
    inst = installer_path()
    if not inst.is_file():
        return False, (
            "Установщик MapMark не найден в программе.\n\n"
            f"Ожидается: {inst}\n"
            "Пересоберите bundle: build_bundle.ps1"
        )
    try:
        os.startfile(str(inst))
    except OSError as exc:
        return False, str(exc)
    return True, "Установщик MapMark запущен"


def launch_mapmark() -> tuple[bool, str]:
    exe = find_installed_exe()
    if not exe:
        return False, "MapMark не установлен."
    try:
        subprocess.Popen([str(exe)], cwd=str(exe.parent))
    except OSError as exc:
        return False, str(exc)
    return True, "MapMark запущен"


def run_mapmark() -> tuple[bool, str, bool]:
    """Launch if installed, otherwise run bundled installer. Returns (ok, msg, launched)."""
    if is_installed():
        ok, msg = launch_mapmark()
        return ok, msg, True
    ok, msg = run_installer()
    return ok, msg, False
