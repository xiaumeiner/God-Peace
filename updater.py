"""GitHub Releases auto-updater for God Peace."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from config import APP_NAME, APP_VERSION, HUB_DIR

GITHUB_OWNER = "xiaumeiner"
GITHUB_REPO = "God-Peace"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
RELEASE_BROWSER_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def _parse_version(tag: str) -> tuple[int, ...]:
    """Convert 'v2.0.1' -> (2, 0, 1)."""
    clean = tag.lstrip("vV").strip()
    parts = []
    for part in clean.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            break
    return tuple(parts) if parts else (0,)


def _current_version() -> tuple[int, ...]:
    return _parse_version(APP_VERSION)


def check_for_update(timeout: int = 15) -> dict[str, Any] | None:
    """Return release info if newer version exists, else None."""
    try:
        req = urllib.request.Request(RELEASES_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    tag = data.get("tag_name", "")
    remote_version = _parse_version(tag)
    if remote_version <= _current_version():
        return None

    assets = data.get("assets") or []
    download_url = ""
    for asset in assets:
        name = asset.get("name", "").lower()
        if name.endswith(".zip") and "godpeace" in name:
            download_url = asset.get("browser_download_url", "")
            break
    if not download_url and assets:
        download_url = assets[0].get("browser_download_url", "")

    return {
        "version": tag.lstrip("vV"),
        "tag": tag,
        "notes": data.get("body", ""),
        "download_url": download_url,
        "browser_url": data.get("html_url") or RELEASE_BROWSER_URL,
    }


def download_update(release_info: dict[str, Any], dest_dir: Path | None = None, timeout: int = 120) -> Path | None:
    """Download zip asset to dest_dir and return zip path."""
    url = release_info.get("download_url") or ""
    if not url:
        return None
    dest_dir = dest_dir or Path(tempfile.gettempdir())
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / "GodPeace_update.zip"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}"})
        with urllib.request.urlopen(req, timeout=timeout) as resp, zip_path.open("wb") as f:
            shutil.copyfileobj(resp, f)
        return zip_path
    except Exception:
        return None


def _wait_unlock(path: Path, timeout: int = 30) -> bool:
    """Wait until a file is no longer locked by another process."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with path.open("a+b"):
                return True
        except PermissionError:
            time.sleep(0.5)
    return False


def apply_update(zip_path: Path, target_dir: Path) -> tuple[bool, str]:
    """Extract update over target_dir and restart."""
    if not zip_path.is_file():
        return False, "Файл обновления не найден"

    try:
        extract_dir = Path(tempfile.mkdtemp(prefix="GodPeace_update_"))
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except Exception as exc:
        return False, f"Ошибка распаковки: {exc}"

    # Find the actual application folder inside the archive.
    candidates = [p for p in extract_dir.iterdir() if p.is_dir()]
    source_dir = extract_dir
    for cand in candidates:
        if (cand / "GodPeace.exe").is_file():
            source_dir = cand
            break

    if not (source_dir / "GodPeace.exe").is_file():
        return False, "В архиве не найден GodPeace.exe"

    updater_bat = extract_dir / "_do_update.bat"
    old_dir = target_dir.with_name(target_dir.name + "_old")
    exe_path = target_dir / "GodPeace.exe"

    bat_content = f"""@echo off
chcp 65001 >nul
timeout /t 1 /nobreak >nul
if exist "{old_dir}" rmdir /s /q "{old_dir}"
ren "{target_dir}" "{old_dir.name}"
xcopy /s /e /i /y "{source_dir}" "{target_dir}"
start "" "{exe_path}"
"""
    updater_bat.write_text(bat_content, encoding="utf-8")

    # Spawn the updater and exit.
    subprocess.Popen([str(updater_bat)], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit(0)


def open_release_page() -> None:
    subprocess.Popen(["start", "", RELEASE_BROWSER_URL], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
