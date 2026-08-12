"""Capt alert sound + Telegram-style popup."""

from __future__ import annotations

import sys
import threading
from typing import Callable

from majestic_captures import CaptEvent


def _play_alert_sound() -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound

        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
    except Exception:
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass


def notify_capt(
    event: CaptEvent,
    *,
    server_id: str = "RU18",
    show_popup: Callable[[CaptEvent], None] | None = None,
    on_fallback: Callable[[str, str], None] | None = None,
) -> None:
    def _deliver() -> None:
        _play_alert_sound()
        if show_popup:
            show_popup(event)
        elif on_fallback:
            title = f"На {event.defender.display_name} напали!" if event.is_defense else f"{event.attacker.display_name} атакует!"
            msg = f"{event.attacker.display_name} ⚔ {event.defender.display_name}"
            on_fallback(title, msg)

    threading.Thread(target=_deliver, daemon=True).start()
