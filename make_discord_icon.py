"""Black Discord-style icon for XGOD button."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "assets" / "discord_xgod.png"
SIZE = 64


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark circle background with subtle border
    draw.ellipse((2, 2, SIZE - 2, SIZE - 2), fill=(18, 18, 18, 255), outline=(60, 60, 60, 255), width=1)

    # Simplified Clyde / Discord mark in white
    cx, cy = SIZE // 2, SIZE // 2 + 2
    draw.ellipse((cx - 18, cy - 14, cx + 18, cy + 16), fill=(240, 240, 240, 255))
    draw.ellipse((cx - 11, cy - 4, cx - 4, cy + 3), fill=(18, 18, 18, 255))
    draw.ellipse((cx + 4, cy - 4, cx + 11, cy + 3), fill=(18, 18, 18, 255))
    draw.arc((cx - 8, cy + 4, cx + 8, cy + 14), start=200, end=340, fill=(18, 18, 18, 255), width=3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
