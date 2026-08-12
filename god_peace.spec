# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller — God Peace onedir."""

from pathlib import Path

import customtkinter

block_cipher = None

project_dir = Path(SPECPATH).resolve()
ctk_dir = Path(customtkinter.__file__).parent

a = Analysis(
    ["run.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=[
        (str(project_dir / "assets"), "assets"),
        (str(project_dir / "tweaks" / "catalog.json"), "tweaks"),
        (str(ctk_dir), "customtkinter"),
    ],
    hiddenimports=[
        "app",
        "config",
        "calamity_runner",
        "mapmark_launcher",
        "customtkinter",
        "extra_tweaks",
        "hub_state",
        "system_status",
        "gif_banner",
        "majestic_api",
        "majestic_captures",
        "family_registry",
        "capt_notifier",
        "capt_popup",
        "capt_watcher",
        "single_instance",
        "tray_icon",
        "pystray",
        "PIL",
        "PIL._tkinter_finder",
        "core",
        "core.shell",
        "core.registry",
        "core.services",
        "core.bcd",
        "core.system",
        "tweaks",
        "tweaks.base",
        "tweaks.catalog",
        "tweaks.catalog_loader",
        "engine_legacy",
        "updater",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GodPeace",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GodPeace",
)
