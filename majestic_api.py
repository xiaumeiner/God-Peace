"""Majestic RP external API HTTP client."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from config import MAJESTIC_API_BASE, MAJESTIC_API_KEY, MAJESTIC_LANGUAGE


class MajesticApiError(Exception):
    pass


class MajesticRateLimitError(MajesticApiError):
    pass


def majestic_request(path: str) -> dict[str, Any]:
    if not MAJESTIC_API_KEY:
        raise MajesticApiError("Не задан MAJESTIC_API_KEY (majestic.env рядом с exe)")

    url = f"{MAJESTIC_API_BASE.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "X-API-KEY": MAJESTIC_API_KEY,
            "X-LANGUAGE": MAJESTIC_LANGUAGE,
            "Accept": "application/json",
            "User-Agent": "GodPeace/1.0 (Majestic Capt Watcher)",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise MajesticRateLimitError("Majestic API: слишком много запросов (5/мин)") from exc
        detail = exc.read().decode("utf-8", errors="replace")[:200]
        raise MajesticApiError(f"Majestic API HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise MajesticApiError(f"Нет связи с Majestic API: {exc.reason}") from exc

    data = json.loads(body)
    if not data.get("status"):
        err = data.get("errorDescription") or data.get("error") or "unknown"
        if str(data.get("error")) == "1315" or "too many" in str(err).lower():
            raise MajesticRateLimitError(str(err))
        raise MajesticApiError(str(err))
    return data.get("result") or {}
