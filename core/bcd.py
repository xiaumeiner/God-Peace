"""Boot Configuration Data (BCD) helpers."""

from __future__ import annotations

from core.shell import run


def set_value(name: str, value: str) -> tuple[bool, str]:
    return run(["bcdedit", "/set", name, value], timeout=30)


def set_current_value(name: str, value: str) -> tuple[bool, str]:
    return run(["bcdedit", "/set", "{current}", name, value], timeout=30)


def delete_value(name: str) -> tuple[bool, str]:
    return run(["bcdedit", "/deletevalue", name], timeout=30)


def delete_current_value(name: str) -> tuple[bool, str]:
    return run(["bcdedit", "/deletevalue", "{current}", name], timeout=30)
