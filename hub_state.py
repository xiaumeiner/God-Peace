"""Persistent hub state — applied tweaks for restore."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import HUB_DIR, STATE_FILE

DEFAULT = {
    "applied_tweak_ids": [],
    "last_preset": "",
    "last_run": "",
    "restore_point_created": False,
}

_cache: dict | None = None
_cache_mtime: float = -1.0


def _load() -> dict:
    global _cache, _cache_mtime
    mtime = STATE_FILE.stat().st_mtime if STATE_FILE.is_file() else 0.0
    if _cache is not None and mtime == _cache_mtime:
        return _cache
    if not STATE_FILE.is_file():
        _cache = dict(DEFAULT)
        _cache_mtime = 0.0
        return _cache
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _cache = dict(DEFAULT)
        _cache_mtime = mtime
        return _cache
    merged = dict(DEFAULT)
    merged.update(data)
    _cache = merged
    _cache_mtime = mtime
    return _cache


def _save(data: dict) -> None:
    global _cache, _cache_mtime
    HUB_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    _cache = dict(data)
    _cache_mtime = STATE_FILE.stat().st_mtime if STATE_FILE.is_file() else 0.0


def has_applied_tweaks() -> bool:
    return bool(_load().get("applied_tweak_ids"))


def get_applied_ids() -> list[str]:
    return list(_load().get("applied_tweak_ids") or [])


def record_optimization(preset: str, applied_ids: list[str], restore_point: bool) -> None:
    data = _load()
    prev = set(data.get("applied_tweak_ids") or [])
    prev.update(applied_ids)
    data["applied_tweak_ids"] = sorted(prev)
    data["last_preset"] = preset
    data["last_run"] = datetime.now(timezone.utc).isoformat()
    data["restore_point_created"] = restore_point or data.get("restore_point_created", False)
    _save(data)


def clear_applied() -> None:
    data = _load()
    data["applied_tweak_ids"] = []
    _save(data)


def remove_applied_ids(ids: list[str]) -> None:
    data = _load()
    remaining = [i for i in data.get("applied_tweak_ids") or [] if i not in set(ids)]
    data["applied_tweak_ids"] = remaining
    _save(data)
