"""Paths for God Peace — assets from PyInstaller bundle, data next to exe."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def resource_dir() -> Path:
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", app_dir()))
    return Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


HUB_DIR = app_dir()
ASSETS_DIR = resource_dir() / "assets"
BUNDLED_DIR = HUB_DIR / "bundled"

_load_dotenv(HUB_DIR / "majestic.env")
_load_dotenv(Path(__file__).resolve().parent / "majestic.env")

CALAMITY_DIR = BUNDLED_DIR / "calamity"
CALAMITY_PROFILES = CALAMITY_DIR / "profiles"

MAPMARK_INSTALLER = BUNDLED_DIR / "installers" / "MapMark-Setup-1.0.0.exe"

APP_NAME = "God Peace"
APP_VERSION = "1.0.0"

# Discord XGOD
DISCORD_XGOD_URL = "https://discord.gg/PW9rSczR2W"
DISCORD_DEVELOPER = "xiaumeiner"

STATE_FILE = HUB_DIR / "god_peace_state.json"
CAPT_STATE_FILE = HUB_DIR / "capt_watch_state.json"

# Majestic API — ключ в majestic.env рядом с exe
MAJESTIC_API_BASE = os.getenv("MAJESTIC_API_BASE", "https://api.majestic-files.com")
MAJESTIC_API_KEY = os.getenv("MAJESTIC_API_KEY", "")
MAJESTIC_SERVER_ID = os.getenv("MAJESTIC_SERVER_ID", "RU18")
MAJESTIC_FAMILY_NAME = os.getenv("MAJESTIC_FAMILY_NAME", "Alarm")
MAJESTIC_LANGUAGE = os.getenv("MAJESTIC_LANGUAGE", "ru")
MAJESTIC_POLL_SECONDS = max(60, int(os.getenv("MAJESTIC_POLL_SECONDS", "60") or "60"))

MAJESTIC_SERVERS = [f"RU{i}" for i in range(1, 20)]

# GitHub Releases — public repo, автообновление без токена
GITHUB_RELEASE_OWNER = os.getenv("GITHUB_RELEASE_OWNER", "xiaumeiner")
GITHUB_RELEASE_REPO = os.getenv("GITHUB_RELEASE_REPO", "God-Peace")
