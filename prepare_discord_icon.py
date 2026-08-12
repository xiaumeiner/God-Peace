"""Crop Discord feedback icon — transparent bg, tight bounds."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent / "assets"
SOURCE = ASSETS / "discord_feedback_source.png"
OUT = ASSETS / "discord_feedback.png"
SIZE = 28


def _find_source() -> Path:
    if SOURCE.is_file():
        return SOURCE
    alt = ASSETS / "discord_feedback.png"
    if alt.is_file():
        return alt
    raise SystemExit(f"No source icon in {ASSETS}")


def main() -> None:
    src_path = _find_source()
    img = Image.open(src_path).convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Black -> transparent, keep white logo
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < 40 and g < 40 and b < 40:
                pixels[x, y] = (0, 0, 0, 0)
            else:
                pixels[x, y] = (255, 255, 255, min(255, a if a else 255))

    bbox = img.getbbox()
    if not bbox:
        raise SystemExit("Icon is empty after processing")
    cropped = img.crop(bbox)

    pad = max(2, int(max(cropped.size) * 0.06))
    canvas = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
    canvas.paste(cropped, (pad, pad), cropped)

    side = max(canvas.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    ox = (side - canvas.width) // 2
    oy = (side - canvas.height) // 2
    square.paste(canvas, (ox, oy), canvas)

    final = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    final.save(OUT)
    print(f"Saved {OUT} ({SIZE}x{SIZE}, cropped)")


if __name__ == "__main__":
    main()
