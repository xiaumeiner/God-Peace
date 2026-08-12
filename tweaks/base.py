"""Tweak dataclass and execution primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


ApplyFn = Callable[[], tuple[bool, str]]
RevertFn = Callable[[], tuple[bool, str]]


@dataclass(frozen=True)
class Tweak:
    id: str
    name: str
    tab: str
    description: str
    effects: list[str] = field(default_factory=list)
    risk: str = "low"  # low | medium | high
    reboot: bool = False
    default_on: bool = False
    preset_safe: bool = False
    preset_latency: bool = False
    preset_fps: bool = False
    preset_competitive: bool = False
    boot_risk: str | None = None  # critical | warning
    apply_fn: ApplyFn = field(default=lambda: (True, ""), repr=False)
    revert_fn: RevertFn = field(default=lambda: (True, ""), repr=False)
