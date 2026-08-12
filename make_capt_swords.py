"""Crossed swords icon for capt notifications."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent / "assets" / "capt_swords.png"
SIZE = 64


def main() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = SIZE // 2, SIZE // 2 + 1
    blade = (240, 240, 240, 255)
    guard = (212, 175, 55, 255)
    glow = (255, 255, 255, 40)

    draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=glow)

    def sword(angle_deg: float) -> None:
        a = math.radians(angle_deg)
        dx, dy = math.cos(a), math.sin(a)
        x1, y1 = cx - dx * 20, cy - dy * 20
        x2, y2 = cx + dx * 24, cy + dy * 24
        draw.line((x1, y1, x2, y2), fill=blade, width=5)
        gx, gy = cx + dx * 4, cy + dy * 4
        px, py = -dy, dx
        draw.line((gx - px * 9, gy - py * 9, gx + px * 9, gy + py * 9), fill=guard, width=4)

    sword(-52)
    sword(52)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
