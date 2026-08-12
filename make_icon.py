"""Build rounded app icon (PNG + ICO) from source image."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parent / "assets"
SOURCE = ASSETS / "icon_source.png"
OUT_PNG = ASSETS / "icon.png"
OUT_ICO = ASSETS / "icon.ico"

SIZES = (16, 32, 48, 64, 128, 256)
CORNER_RATIO = 0.22


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def main() -> None:
    if not SOURCE.is_file():
        raise SystemExit(f"Missing source icon: {SOURCE}")

    base = Image.open(SOURCE).convert("RGBA")
    size = min(base.size)
    base = base.crop(((base.width - size) // 2, (base.height - size) // 2, (base.width + size) // 2, (base.height + size) // 2))
    base = base.resize((256, 256), Image.Resampling.LANCZOS)

    radius = max(8, int(256 * CORNER_RATIO))
    mask = _rounded_mask(256, radius)
    rounded = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    rounded.paste(base, (0, 0), mask)
    rounded.save(OUT_PNG)

    icons = []
    for s in SIZES:
        r = max(2, int(s * CORNER_RATIO))
        m = _rounded_mask(s, r)
        frame = base.resize((s, s), Image.Resampling.LANCZOS)
        out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        out.paste(frame, (0, 0), m)
        icons.append(out)
    icons[0].save(OUT_ICO, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"Saved {OUT_PNG} and {OUT_ICO}")


if __name__ == "__main__":
    main()
