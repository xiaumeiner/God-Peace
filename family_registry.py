"""Family metadata + logo cache from Majestic captures zones."""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from config import HUB_DIR, MAJESTIC_API_BASE, MAJESTIC_API_KEY, MAJESTIC_LANGUAGE
from majestic_api import majestic_request

LOGO_CACHE_DIR = HUB_DIR / "cache" / "family_logos"
LOGO_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Known patterns (best-effort; API may add official URL later)
_LOGO_URL_TEMPLATES = (
    "{base}/v1/ext/family-logo/{server}/{fid}.{ext}",
    "{base}/v1/ext/logos/{server}/{fid}.{ext}",
    "https://cdn.majestic-files.com/families/{server}/{fid}.{ext}",
)


@dataclass(frozen=True)
class FamilySide:
    family_id: int | None
    name: str
    tag: str | None = None
    color: str | None = None
    has_logo: bool = False

    @property
    def display_name(self) -> str:
        return self.name or self.tag or "—"

    @property
    def short_label(self) -> str:
        if self.tag:
            return self.tag
        name = self.name or "?"
        return name[:4].upper()


_registry: dict[int, FamilySide] = {}
_name_index: dict[str, FamilySide] = {}
_lock = threading.Lock()
_last_refresh = 0.0
REGISTRY_TTL = 55.0

_avatar_cache: dict[tuple, object] = {}
_logo_miss: set[int] = set()


def _norm_name(name: str | None) -> str:
    return (name or "").strip().casefold()


def _zone_to_side(raw: dict) -> FamilySide | None:
    fid = raw.get("familyId")
    name = raw.get("familyName")
    if fid is None and not name:
        return None
    return FamilySide(
        family_id=int(fid) if fid is not None else None,
        name=str(name or "—"),
        tag=(str(raw["familyTag"]) if raw.get("familyTag") else None),
        color=(str(raw["familyMainColor"]) if raw.get("familyMainColor") else None),
        has_logo=int(raw.get("familyLogoStatus") or 0) == 1,
    )


def refresh_registry(server_id: str | None = None, *, force: bool = False) -> None:
    global _last_refresh
    now = time.monotonic()
    with _lock:
        if not force and _registry and now - _last_refresh < REGISTRY_TTL:
            return
    sid = server_id or MAJESTIC_SERVER_ID
    try:
        result = majestic_request(f"/v1/ext/captures/{sid}")
    except Exception:
        return
    zones = result.get("zones") or []
    with _lock:
        for z in zones:
            side = _zone_to_side(z)
            if not side or side.family_id is None:
                continue
            _registry[side.family_id] = side
            if side.name and side.name != "—":
                _name_index[_norm_name(side.name)] = side
            if side.tag:
                _name_index[_norm_name(side.tag)] = side
        _last_refresh = now


def lookup_side(
    *,
    family_id: int | None,
    name: str | None,
) -> FamilySide:
    with _lock:
        if family_id is not None and family_id in _registry:
            return _registry[family_id]
        hit = _name_index.get(_norm_name(name))
        if hit:
            return hit
    return FamilySide(
        family_id=family_id,
        name=str(name or "—"),
        has_logo=False,
    )


def _logo_cache_path(family_id: int, server_id: str, ext: str = "png") -> Path:
    return LOGO_CACHE_DIR / f"{server_id}_{family_id}.{ext}"


def _download_logo(family_id: int, server_id: str, ext: str = "png") -> Path | None:
    if family_id in _logo_miss:
        return None
    cache = _logo_cache_path(family_id, server_id, ext)
    if cache.is_file() and cache.stat().st_size > 0:
        return cache

    headers = {
        "X-API-KEY": MAJESTIC_API_KEY,
        "X-LANGUAGE": MAJESTIC_LANGUAGE,
        "User-Agent": "GodPeace/1.0",
    }
    for tmpl in _LOGO_URL_TEMPLATES:
        url = tmpl.format(base=MAJESTIC_API_BASE.rstrip("/"), server=server_id, fid=family_id, ext=ext)
        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = resp.read()
            if len(data) < 32:
                continue
            cache.write_bytes(data)
            return cache
        except (urllib.error.URLError, OSError, ValueError):
            continue
    _logo_miss.add(family_id)
    return None


def load_family_avatar(side: FamilySide, size: int = 40, *, ring_color: str | None = None, server_id: str | None = None):
    """Return PIL Image RGBA — круглый аватар, опционально кольцо."""
    key = (side.family_id, side.name, side.color, side.has_logo, size, ring_color, server_id)
    cached = _avatar_cache.get(key)
    if cached is not None:
        return cached
    from PIL import Image, ImageDraw, ImageFont

    inner = size - (8 if ring_color else 0)
    pad = (size - inner) // 2
    core = Image.new("RGBA", (inner, inner), (0, 0, 0, 0))
    painted = False

    if side.family_id is not None and side.has_logo:
        path = _download_logo(side.family_id, server_id or "RU18")
        if path and path.is_file():
            try:
                raw = Image.open(path).convert("RGBA").resize((inner, inner), Image.LANCZOS)
                mask = Image.new("L", (inner, inner), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, inner - 1, inner - 1), fill=255)
                core.paste(raw, (0, 0), mask)
                painted = True
            except OSError:
                pass

    if not painted:
        color = side.color or "#3a3a3a"
        if color.startswith("#") and len(color) >= 7:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
        else:
            r, g, b = 58, 58, 58
        draw = ImageDraw.Draw(core)
        draw.ellipse((0, 0, inner - 1, inner - 1), fill=(r, g, b, 255))
        letter = (side.short_label[:1] or "?").upper()
        try:
            font = ImageFont.truetype("arialbd.ttf", max(12, inner // 2))
        except OSError:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), letter, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((inner - tw) / 2, (inner - th) / 2 - 1), letter, fill=(255, 255, 255, 240), font=font)

    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(core, (pad, pad), core)
    if ring_color and ring_color.startswith("#") and len(ring_color) >= 7:
        rr = int(ring_color[1:3], 16)
        gg = int(ring_color[3:5], 16)
        bb = int(ring_color[5:7], 16)
        ring = ImageDraw.Draw(out)
        ring.ellipse((1, 1, size - 2, size - 2), outline=(rr, gg, bb, 220), width=3)
    if len(_avatar_cache) > 96:
        _avatar_cache.clear()
    _avatar_cache[key] = out
    return out
