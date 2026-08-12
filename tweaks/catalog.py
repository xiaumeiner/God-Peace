"""Tweak catalog with presets and execution."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import replace
from functools import lru_cache
from typing import Callable

from tweaks.base import Tweak
from tweaks.catalog_loader import load_tweak_definitions


TWEAK_TIMEOUTS: dict[str, int] = {
    "nvidia_profile": 120,
    "defender_off": 90,
    "dns_cloudflare": 40,
    "ultimate_power": 30,
    "core_parking": 30,
    "msi_gpu": 40,
    "msi_usb": 40,
    "msi_network": 40,
    "nic_power_off": 40,
    "memory_compression_off": 40,
    "nvidia_driver": 40,
}
DEFAULT_TIMEOUT = 25
_EXECUTOR = ThreadPoolExecutor(max_workers=4)


MANUAL_ONLY_IDS = frozenset({"nvidia_profile", "ssd_trim", "defender_off"})


_SKIP_PRESET_ALL = frozenset({
    "nvidia_profile", "ssd_trim", "defender_off", "disable_vbs", "smartscreen_off",
    "disable_fso", "disable_mpo", "gpu_preemption", "memory_compression_off",
    "page_combining_off", "io_page_lock", "gpu_power_latency", "power_latency_pack",
    "spectre_mitigations", "hpet_bcd", "hpet_platform", "hpet_service_off",
    "tsx_off", "bits_off", "large_system_cache",
})


def _run_with_timeout(fn: Callable[[], tuple[bool, str]], tweak_id: str = "") -> tuple[bool, str]:
    timeout = TWEAK_TIMEOUTS.get(tweak_id, DEFAULT_TIMEOUT)
    future = _EXECUTOR.submit(fn)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeout:
        return False, f"Таймаут {timeout} с — пропущено"
    except Exception as exc:
        return False, str(exc)


@lru_cache(maxsize=1)
def _cached_tweaks() -> list[Tweak]:
    return load_tweak_definitions()


def get_all_tweaks() -> list[Tweak]:
    return _cached_tweaks()


def get_tweak_by_id(tweak_id: str) -> Tweak | None:
    for t in get_all_tweaks():
        if t.id == tweak_id:
            return t
    return None


def get_presets() -> dict[str, tuple[str, Callable[[Tweak], bool]]]:
    return {
        "safe": ("Безопасный", lambda t: t.preset_safe),
        "latency": ("Мин. задержка", lambda t: t.preset_latency),
        "fps": ("Макс. FPS", lambda t: t.preset_fps),
        "competitive": ("Киберспорт", lambda t: t.preset_competitive),
        "all": (
            "Рекомендуемые",
            lambda t: (
                (t.preset_safe or t.preset_latency or t.preset_fps or t.preset_competitive)
                and t.id not in _SKIP_PRESET_ALL
                and t.risk != "high"
                and t.boot_risk != "critical"
            ),
        ),
    }


def get_preset_tweaks(preset_key: str) -> list[Tweak]:
    presets = get_presets()
    if preset_key not in presets:
        return []
    _, predicate = presets[preset_key]
    return [t for t in get_all_tweaks() if predicate(t)]


def apply_tweaks(
    tweaks: list[Tweak],
    *,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> tuple[int, int, list[str], list[str]]:
    ok_count = 0
    errors: list[str] = []
    applied: list[str] = []
    total = len(tweaks)
    for i, t in enumerate(tweaks, 1):
        if on_progress:
            on_progress(i, total, t.name)
        ok, msg = _run_with_timeout(t.apply_fn, t.id)
        if ok:
            ok_count += 1
            applied.append(t.id)
        else:
            errors.append(f"{t.name}: {msg[:160]}")
    return ok_count, total, errors, applied


def revert_tweaks(
    tweaks: list[Tweak],
    *,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> tuple[int, int, list[str], list[str]]:
    ok_count = 0
    errors: list[str] = []
    reverted: list[str] = []
    total = len(tweaks)
    for i, t in enumerate(tweaks, 1):
        if on_progress:
            on_progress(i, total, t.name)
        ok, msg = _run_with_timeout(t.revert_fn, t.id)
        if ok:
            ok_count += 1
            reverted.append(t.id)
        else:
            errors.append(f"{t.name}: {msg[:160]}")
    return ok_count, total, errors, reverted
