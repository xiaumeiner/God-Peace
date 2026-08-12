"""Animated GIF banner for the hub header."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from config import ASSETS_DIR

BANNER_GIF = ASSETS_DIR / "xgod-banner.gif"
BANNER_WIDTH = 340
BG_HEX = "#0a0a0a"


class GifBanner(ctk.CTkFrame):
    def __init__(self, master, gif_path: Path | None = None, width: int = BANNER_WIDTH, **kwargs) -> None:
        super().__init__(master, fg_color="transparent", **kwargs)
        self._path = gif_path or BANNER_GIF
        self._width = width
        self._frames: list[ImageTk.PhotoImage] = []
        self._delays: list[int] = []
        self._index = 0
        self._job: str | None = None
        self._height = int(width * 405 / 720)

        self._label = tk.Label(self, bg=BG_HEX, borderwidth=0, highlightthickness=0)
        self._label.pack()

        self.configure(width=width, height=self._height)
        self._label.configure(width=width, height=self._height)

        if self._path.is_file():
            threading.Thread(target=self._load_frames_async, daemon=True).start()
        else:
            self._label.configure(text="banner missing", fg="#666", bg=BG_HEX)

    def _load_frames_async(self) -> None:
        try:
            img = Image.open(self._path)
            count = getattr(img, "n_frames", 1)
            base_w, base_h = img.size
            target_w = self._width
            target_h = max(1, int(base_h * target_w / base_w))
            self._height = target_h

            frames: list[ImageTk.PhotoImage] = []
            delays: list[int] = []
            bg_rgb = (10, 10, 10)

            for i in range(count):
                img.seek(i)
                frame = img.convert("RGBA").resize((target_w, target_h), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (target_w, target_h), bg_rgb)
                canvas.paste(frame, mask=frame.split()[3])
                frames.append(ImageTk.PhotoImage(canvas))
                delays.append(max(int(img.info.get("duration", 40)), 20))

            self.after(0, lambda: self._start_animation(frames, delays, target_w, target_h))
        except Exception as exc:
            self.after(0, lambda: self._label.configure(text=f"GIF error", fg="#c0392b"))

    def _start_animation(
        self,
        frames: list[ImageTk.PhotoImage],
        delays: list[int],
        width: int,
        height: int,
    ) -> None:
        self._frames = frames
        self._delays = delays
        self.configure(width=width, height=height)
        self._label.configure(width=width, height=height, image=frames[0])
        self._animate()

    def _animate(self) -> None:
        if not self._frames:
            return
        self._label.configure(image=self._frames[self._index])
        delay = self._delays[self._index]
        self._index = (self._index + 1) % len(self._frames)
        self._job = self.after(delay, self._animate)

    def destroy(self) -> None:
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
        super().destroy()
