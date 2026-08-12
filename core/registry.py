"""Safe Windows registry operations with backup/restore."""

from __future__ import annotations

import os
import shutil
import tempfile
import winreg
from datetime import datetime
from pathlib import Path
from typing import Any


HKLM = winreg.HKEY_LOCAL_MACHINE
HKCU = winreg.HKEY_CURRENT_USER
HKU = winreg.HKEY_USERS
HKCR = winreg.HKEY_CLASSES_ROOT


class RegistryBackup:
    """Export registry branches to .reg files before editing."""

    _backups_dir: Path | None = None

    @classmethod
    def backups_dir(cls) -> Path:
        if cls._backups_dir is None:
            base = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))
            cls._backups_dir = base / "GodPeace" / "registry_backups"
        cls._backups_dir.mkdir(parents=True, exist_ok=True)
        return cls._backups_dir

    @classmethod
    def backup(cls, hive: str, path: str) -> Path:
        """Export a registry path to a timestamped .reg file."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_key = path.replace("\\", "_").replace("/", "_")
        if len(safe_key) > 80:
            safe_key = safe_key[:80]
        out = cls.backups_dir() / f"{stamp}_{hive}_{safe_key}.reg"
        import subprocess

        try:
            subprocess.run(
                ["reg", "export", f"{hive}\\{path}", str(out), "/y"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
                timeout=30,
            )
        except Exception:
            pass
        return out

    @classmethod
    def list_backups(cls) -> list[Path]:
        d = cls.backups_dir()
        if not d.exists():
            return []
        return sorted(d.glob("*.reg"), key=lambda p: p.stat().st_mtime, reverse=True)

    @classmethod
    def restore(cls, backup_path: Path) -> tuple[bool, str]:
        import subprocess

        if not backup_path.is_file():
            return False, f"Backup not found: {backup_path}"
        try:
            subprocess.run(
                ["reg", "import", str(backup_path)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                check=False,
                timeout=60,
            )
            return True, f"Imported {backup_path.name}"
        except Exception as exc:
            return False, str(exc)


def _hive_str(hive: int) -> str:
    return {HKLM: "HKLM", HKCU: "HKCU", HKU: "HKU", HKCR: "HKCR"}.get(hive, "HKLM")


def _backup_for(hive: int, path: str) -> Path | None:
    try:
        return RegistryBackup.backup(_hive_str(hive), path)
    except Exception:
        return None


def ensure_key(root: int, path: str) -> None:
    winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)


def set_dword(root: int, path: str, name: str, value: int, *, backup: bool = True) -> None:
    if backup:
        _backup_for(root, path)
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
    finally:
        winreg.CloseKey(key)


def set_qword(root: int, path: str, name: str, value: int, *, backup: bool = True) -> None:
    if backup:
        _backup_for(root, path)
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_QWORD, value)
    finally:
        winreg.CloseKey(key)


def set_string(root: int, path: str, name: str, value: str, *, backup: bool = True) -> None:
    if backup:
        _backup_for(root, path)
    key = winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE)
    try:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    finally:
        winreg.CloseKey(key)


def set_binary(root: int, path: str, name: str, value: bytes, *, backup: bool = True) -> None:
    if backup:
        _backup_for(root, path)
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


def get_string(root: int, path: str, name: str, default: str | None = None) -> str | None:
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return str(value)
    except OSError:
        return default


def delete_value(root: int, path: str, name: str, *, backup: bool = True) -> bool:
    if backup:
        _backup_for(root, path)
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
            return True
    except OSError:
        return False


def delete_key(root: int, path: str, *, backup: bool = True) -> bool:
    if backup:
        _backup_for(root, path)
    try:
        winreg.DeleteKey(root, path)
        return True
    except OSError:
        return False
