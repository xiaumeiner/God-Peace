"""Безопасный запуск твиков с таймаутом (не зависать навсегда)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Callable

# Твики вне основного списка / только вручную
MANUAL_ONLY_IDS = frozenset({
    "nvidia_profile",
    "ssd_trim",
    "defender_off",
})

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
_EXECUTOR = ThreadPoolExecutor(max_workers=2)


def run_with_timeout(
    fn: Callable[[], tuple[bool, str]],
    tweak_id: str = "",
) -> tuple[bool, str]:
    timeout = TWEAK_TIMEOUTS.get(tweak_id, DEFAULT_TIMEOUT)
    future = _EXECUTOR.submit(fn)
    try:
        return future.result(timeout=timeout)
    except FuturesTimeout:
        return False, f"Таймаут {timeout} с — пропущено (зависла команда)"
    except Exception as exc:
        return False, str(exc)
