"""System tray — minimize on close, exit from menu."""

from __future__ import annotations

import threading
from typing import Callable

from PIL import Image


class TrayIcon:
    def __init__(
        self,
        *,
        icon_path,
        tooltip: str,
        on_show: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._icon_path = icon_path
        self._tooltip = tooltip
        self._on_show = on_show
        self._on_quit = on_quit
        self._icon = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="tray-icon", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _run(self) -> None:
        try:
            import pystray
            from pystray import MenuItem as item
        except ImportError:
            return

        image = Image.open(self._icon_path).convert("RGBA")
        image = image.resize((64, 64), Image.LANCZOS)

        def show_action(_icon, _item) -> None:
            self._on_show()

        def quit_action(_icon, _item) -> None:
            self._on_quit()

        menu = pystray.Menu(
            item("Открыть God Peace", show_action, default=True),
            item("Выход", quit_action),
        )
        self._icon = pystray.Icon(self._tooltip, image, self._tooltip, menu)
        self._icon.run()
