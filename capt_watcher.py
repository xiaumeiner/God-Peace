"""Background poll Majestic family-wars for new Alarm capts."""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from typing import Callable

from capt_notifier import notify_capt
from config import CAPT_STATE_FILE, MAJESTIC_FAMILY_NAME, MAJESTIC_POLL_SECONDS, MAJESTIC_SERVER_ID
from family_registry import refresh_registry
from majestic_api import MajesticApiError, MajesticRateLimitError
from majestic_captures import CaptEvent, fetch_family_wars, filter_family_captures


class CaptWatcher:
    def __init__(
        self,
        on_status: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_notify_ui: Callable[[str, str], None] | None = None,
        show_popup: Callable[[CaptEvent], None] | None = None,
    ) -> None:
        self._on_status = on_status
        self._on_error = on_error
        self._on_notify_ui = on_notify_ui
        self._show_popup = show_popup
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._enabled = True

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        self._emit_status("мониторинг вкл" if value else "мониторинг выкл")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="capt-watcher", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def poll_now(self) -> list[CaptEvent]:
        return self._poll_once(notify_new=True)

    def _loop(self) -> None:
        time.sleep(3)
        try:
            self._poll_once(notify_new=False)
        except Exception as exc:
            self._emit_error(str(exc))
        while not self._stop.wait(MAJESTIC_POLL_SECONDS):
            if not self._enabled:
                continue
            try:
                self._poll_once(notify_new=True)
            except MajesticRateLimitError as exc:
                self._emit_error(str(exc))
                time.sleep(15)
            except MajesticApiError as exc:
                self._emit_error(str(exc))
            except Exception as exc:
                self._emit_error(str(exc))

    def _poll_once(self, *, notify_new: bool) -> list[CaptEvent]:
        refresh_registry()
        captures = fetch_family_wars()
        events = filter_family_captures(captures)
        state = _load_state()
        seen: set[int] = set(state.get("seen_ids") or [])
        initialized = bool(state.get("initialized"))
        prev_seen = set(seen)

        new_events: list[CaptEvent] = []
        for ev in events:
            if ev.record_id not in seen:
                new_events.append(ev)
            seen.add(ev.record_id)

        if not initialized or new_events or seen != prev_seen:
            state["seen_ids"] = sorted(seen)[-500:]
            state["initialized"] = True
            state["last_poll"] = datetime.now(timezone.utc).isoformat()
            state["last_count"] = len(events)
            _save_state(state)

        if initialized and notify_new and self._enabled:
            for ev in new_events:
                notify_capt(
                    ev,
                    server_id=MAJESTIC_SERVER_ID,
                    show_popup=self._show_popup,
                    on_fallback=self._on_notify_ui,
                )

        ts = datetime.now().strftime("%H:%M")
        fam = MAJESTIC_FAMILY_NAME
        if not initialized:
            self._emit_status(f"база {len(seen)} каптов · {fam} · {ts}")
        elif new_events and notify_new:
            self._emit_status(f"новых: {len(new_events)} · {fam} · {ts}")
        else:
            self._emit_status(f"ок · {len(events)} в истории · {fam} · {ts}")

        return new_events

    def _emit_status(self, text: str) -> None:
        if self._on_status:
            self._on_status(text)

    def _emit_error(self, text: str) -> None:
        if self._on_error:
            self._on_error(text)


def _load_state() -> dict:
    if not CAPT_STATE_FILE.is_file():
        return {"seen_ids": [], "initialized": False}
    try:
        return json.loads(CAPT_STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"seen_ids": [], "initialized": False}


def _save_state(data: dict) -> None:
    CAPT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CAPT_STATE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
