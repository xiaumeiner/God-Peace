"""NVIDIA Profile Inspector — загрузка и применение профиля."""

from __future__ import annotations

import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from paths import app_data_dir, resource_path

TOOLS_DIR = app_data_dir() / "tools" / "nvidiaProfileInspector"
NPI_EXE = TOOLS_DIR / "nvidiaProfileInspector.exe"
PROFILE_PATH = resource_path("profiles", "nvidia_latency.nip")
NPI_URL = (
    "https://github.com/Orbmu2k/nvidiaProfileInspector/releases/download/2.4.0.19/"
    "nvidiaProfileInspector.zip"
)


def _download_npi() -> tuple[bool, str]:
    if NPI_EXE.exists():
        return True, "NPI already installed"

    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = app_data_dir() / "tools" / "npi.zip"
    try:
        with urllib.request.urlopen(NPI_URL, timeout=45) as resp:
            zip_path.write_bytes(resp.read())
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(TOOLS_DIR)
        zip_path.unlink(missing_ok=True)
    except Exception as exc:
        return False, f"Download failed: {exc}"

    if not NPI_EXE.exists():
        for candidate in TOOLS_DIR.rglob("nvidiaProfileInspector.exe"):
            if candidate != NPI_EXE:
                shutil.copy2(candidate, NPI_EXE)
                break

    return (True, "NPI downloaded") if NPI_EXE.exists() else (False, "NPI exe not found after extract")


def apply_nvidia_profile_inspector() -> tuple[bool, str]:
    if not PROFILE_PATH.exists():
        return False, f"Profile not found: {PROFILE_PATH}"

    ok, msg = _download_npi()
    if not ok:
        return False, msg

    try:
        result = subprocess.run(
            [str(NPI_EXE), str(PROFILE_PATH)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=120,
        )
        if result.returncode == 0:
            return True, (
                "NVIDIA Profile Inspector: профиль Low Latency применён.\n"
                "Low Latency Ultra, Max Prerendered=1, Max Performance, VSync Off, Ansel Off."
            )
        return False, result.stderr or result.stdout or f"Exit code {result.returncode}"
    except subprocess.TimeoutExpired:
        return False, "NPI timeout — закройте окно Inspector и повторите"
    except Exception as exc:
        return False, str(exc)


def revert_nvidia_profile_info() -> tuple[bool, str]:
    return True, (
        "Откат NPI-профиля: откройте NVIDIA Profile Inspector → "
        "Profile → Restore defaults, или переустановите драйвер."
    )
