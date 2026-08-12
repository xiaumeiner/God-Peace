"""Load tweak definitions from catalog.json."""

from __future__ import annotations

import json
import re
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

from tweaks.base import Tweak


def _catalog_path() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass) / "tweaks" / "catalog.json"
    return Path(__file__).resolve().parent / "catalog.json"


_CATALOG_PATH = _catalog_path()


def _risk_value(risk: str) -> int:
    return {"low": 0, "medium": 1, "high": 2}.get(risk, 0)


def _load_json() -> list[dict[str, Any]]:
    if not _CATALOG_PATH.is_file():
        return []
    try:
        return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _resolve_fn(name: str):
    """Resolve a function by dotted path, e.g. 'engine:apply_game_dvr_off'."""
    if not name:
        return None
    module_path, fn_name = name.split(":", 1)
    # Support bundled calamity engine as well as new engine_legacy adapter
    import importlib

    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return None
    return getattr(module, fn_name, None)


def load_tweak_definitions() -> list[Tweak]:
    raw_items = _load_json()
    out: list[Tweak] = []
    for item in raw_items:
        apply_fn = _resolve_fn(item.get("apply"))
        revert_fn = _resolve_fn(item.get("revert"))
        if apply_fn is None or revert_fn is None:
            continue
        t = Tweak(
            id=item["id"],
            name=item["name"],
            tab=item["tab"],
            description=item.get("description", ""),
            effects=item.get("effects", []),
            risk=item.get("risk", "low"),
            reboot=item.get("reboot", False),
            default_on=item.get("default_on", False),
            preset_safe=item.get("preset_safe", False),
            preset_latency=item.get("preset_latency", False),
            preset_fps=item.get("preset_fps", False),
            preset_competitive=item.get("preset_competitive", False),
            boot_risk=item.get("boot_risk"),
            apply_fn=apply_fn,
            revert_fn=revert_fn,
        )
        out.append(t)
    return out
