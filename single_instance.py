"""One God Peace instance — second launch shows the tray window."""

from __future__ import annotations

import socket
import sys
import threading
import time
from typing import Callable

HOST = "127.0.0.1"
PORT = 47891
SHOW_CMD = b"SHOW"
MUTEX_NAME = "Global\\GodPeace_SingleInstance_v1"
_mutex_handle = None


def _win_mutex_taken() -> bool:
    if sys.platform != "win32":
        return False
    global _mutex_handle
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        _mutex_handle = kernel32.CreateMutexW(None, True, MUTEX_NAME)
        return kernel32.GetLastError() == 183
    except Exception:
        return False


def _activate_existing_window(title: str) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, title)
        if not hwnd:
            return False
        SW_SHOW = 5
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def _ping_running_instance(retries: int = 8, delay: float = 0.15) -> bool:
    for _ in range(retries):
        try:
            with socket.create_connection((HOST, PORT), timeout=0.35) as sock:
                sock.sendall(SHOW_CMD)
            return True
        except OSError:
            time.sleep(delay)
    return False


def ensure_single_instance(*, window_title: str = "God Peace") -> bool:
    """Return True if this process should start the app."""
    if not _win_mutex_taken():
        return True

    if _ping_running_instance():
        return False
    if _activate_existing_window(window_title):
        return False
    return True


def start_activation_server(on_show: Callable[[], None]) -> tuple[threading.Event, threading.Thread]:
    stop = threading.Event()

    def serve() -> None:
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind((HOST, PORT))
            srv.listen(4)
            srv.settimeout(0.5)
            while not stop.is_set():
                try:
                    conn, _addr = srv.accept()
                except OSError:
                    continue
                try:
                    data = conn.recv(16)
                    if data == SHOW_CMD:
                        on_show()
                finally:
                    conn.close()
        except OSError:
            pass
        finally:
            try:
                srv.close()
            except OSError:
                pass

    thread = threading.Thread(target=serve, name="godpeace-ipc", daemon=True)
    thread.start()
    return stop, thread
