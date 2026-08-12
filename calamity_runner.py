"""Calamity optimization from new tweak catalog."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path

from config import CALAMITY_DIR
from core.system import create_restore_point as _create_restore_point
from core.system import is_admin, open_system_restore, relaunch_as_admin
from extra_tweaks import EXTRA_BY_ID, run_extra_tweaks, revert_extra_tweaks
from tweaks import get_all_tweaks, get_preset_tweaks

GAMING_EXTRA_IDS = ("gp_network", "gp_keyboard", "gp_multimon", "gp_window_drag")


MODE_PRESETS = {
    "safe": "safe",
    "gaming": "competitive",
    "full": "all",
}


def _ensure_calamity_path() -> None:
    root = str(CALAMITY_DIR)
    if root not in __import__("sys").path:
        __import__("sys").path.insert(0, root)


def bundle_ready() -> bool:
    _ensure_calamity_path()
    return (CALAMITY_DIR / "engine.py").is_file()


def create_restore_point(label: str = "God Peace") -> tuple[bool, str]:
    return _create_restore_point(label)


def get_tweaks_for_mode(mode: str) -> list:
    preset_key = MODE_PRESETS.get(mode, mode)
    selected = get_preset_tweaks(preset_key)

    if mode == "gaming":
        by_id = {t.id: t for t in get_all_tweaks()}
        seen = {t.id for t in selected}
        for tid in GAMING_EXTRA_IDS:
            if tid.startswith("gp_"):
                continue
            if tid in by_id and tid not in seen:
                selected.append(by_id[tid])
                seen.add(tid)
    return selected


def run_optimization(
    mode: str,
    *,
    on_progress: Callable[[int, int, str], None] | None = None,
    include_cleanup: bool = False,
) -> tuple[int, int, list[str], bool, list[str]]:
    if not bundle_ready():
        raise FileNotFoundError(f"Calamity engine не найден в {CALAMITY_DIR}")

    from cleanup import run_normal_cleanup
    from tweaks.catalog import apply_tweaks

    if include_cleanup or mode == "full":
        run_normal_cleanup()

    selected = get_tweaks_for_mode(mode)
    extra_count = 4
    total = len(selected) + extra_count
    ok_count = 0
    errors: list[str] = []
    applied_ids: list[str] = []
    needs_reboot = any(t.reboot for t in selected)

    def _prog(i: int, n: int, name: str) -> None:
        if on_progress:
            on_progress(i, total, name)

    ok, _, errs, applied = apply_tweaks(selected, on_progress=_prog)
    ok_count += ok
    applied_ids.extend(applied)
    errors.extend(errs)

    ex_ok, _, ex_errors, ex_applied = run_extra_tweaks(
        on_progress=lambda c, t, n: _prog(len(selected) + c, total, n),
        offset=len(selected),
        total_base=len(selected),
    )
    ok_count += ex_ok
    applied_ids.extend(ex_applied)
    errors.extend(ex_errors)

    return ok_count, total, errors, needs_reboot, applied_ids


def revert_tweaks(
    tweak_ids: list[str],
    *,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> tuple[int, int, list[str], list[str]]:
    if not bundle_ready():
        raise FileNotFoundError("Calamity engine не найден")

    from tweaks import get_tweak_by_id
    from tweaks.catalog import revert_tweaks as revert_catalog

    by_id = {t.id: t for t in get_all_tweaks()}
    calamity_ids = [i for i in tweak_ids if i in by_id]
    extra_ids = [i for i in tweak_ids if i in EXTRA_BY_ID]

    selected = [by_id[i] for i in calamity_ids]
    total = len(selected) + len(extra_ids)
    ok_count = 0
    errors: list[str] = []
    reverted: list[str] = []

    def _prog(i: int, n: int, name: str) -> None:
        if on_progress:
            on_progress(i, total, name)

    if selected:
        ok, _, errs, rev = revert_catalog(selected, on_progress=_prog)
        ok_count += ok
        reverted.extend(rev)
        errors.extend(errs)

    if extra_ids:
        ex_ok, _, ex_errors, ex_rev = revert_extra_tweaks(
            extra_ids,
            on_progress=lambda c, t, n: _prog(len(selected) + c, total, n),
        )
        ok_count += ex_ok
        reverted.extend(ex_rev)
        errors.extend(ex_errors)

    return ok_count, total, errors, reverted
