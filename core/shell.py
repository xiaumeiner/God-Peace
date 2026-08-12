"""Unified subprocess runner with timeout, retry and logging."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from typing import Any


CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW


class ShellError(Exception):
    """Raised when a command fails after retries."""

    def __init__(self, message: str, stdout: str = "", stderr: str = "", code: int | None = None) -> None:
        super().__init__(message)
        self.stdout = stdout
        self.stderr = stderr
        self.code = code


def run(
    cmd: list[str],
    *,
    timeout: int = 60,
    retries: int = 1,
    retry_delay: float = 0.2,
    shell: bool = False,
    check: bool = False,
    on_retry: Callable[[int, Exception], None] | None = None,
    **kwargs: Any,
) -> tuple[bool, str]:
    """Run a command. Returns (ok, output_or_error).

    kwargs are passed to subprocess.run. Creation flag CREATE_NO_WINDOW is
    applied automatically on Windows unless explicitly disabled.
    """
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("encoding", "utf-8")
    kwargs.setdefault("errors", "replace")
    if not shell and "creationflags" not in kwargs:
        kwargs["creationflags"] = CREATE_NO_WINDOW

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            result = subprocess.run(cmd, timeout=timeout, shell=shell, **kwargs)
            output = ((result.stdout or "") + (result.stderr or "")).strip()
            ok = result.returncode == 0
            if check and not ok:
                raise ShellError(
                    f"Command failed with {result.returncode}",
                    stdout=result.stdout or "",
                    stderr=result.stderr or "",
                    code=result.returncode,
                )
            return ok, output
        except subprocess.TimeoutExpired as exc:
            last_exc = exc
            if on_retry:
                on_retry(attempt, exc)
            if attempt < retries - 1:
                import time

                time.sleep(retry_delay)
        except ShellError:
            raise
        except Exception as exc:
            return False, str(exc)

    return False, f"Timeout ({timeout} s): {' '.join(cmd[:4])}"


def powershell(script: str, *, timeout: int = 90, retries: int = 1) -> tuple[bool, str]:
    """Run a PowerShell script block with Bypass execution policy."""
    return run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout=timeout,
        retries=retries,
    )
