"""Capt alert popup — God Peace style, bottom-right of screen."""

from __future__ import annotations

import sys

import customtkinter as ctk
from PIL import Image

from config import APP_NAME, ASSETS_DIR, MAJESTIC_SERVER_ID
from family_registry import FamilySide, load_family_avatar
from majestic_captures import CaptEvent

BG = "#0a0a0a"
CARD = "#141414"
CARD_INNER = "#181818"
BORDER = "#2a2a2a"
TEXT = "#f0f0f0"
MUTED = "#666666"
WHITE = "#ffffff"
DANGER = "#c0392b"
WARNING = "#d4a017"

POPUP_W = 408
MARGIN_X = 20
MARGIN_Y = 14
STACK_GAP = 12
AUTO_CLOSE_MS = 10000
SLIDE_MS = 14
SLIDE_STEPS = 12
TICK_MS = 50

_active: list["CaptPopup"] = []
_work_area_cache: tuple[int, int, int, int] | None = None
_swords_pil: Image.Image | None = None
_font_cache: dict[tuple, ctk.CTkFont] = {}


def _font(size: int, *, weight: str = "normal", family: str | None = None) -> ctk.CTkFont:
    key = (size, weight, family)
    hit = _font_cache.get(key)
    if hit is not None:
        return hit
    kwargs: dict = {"size": size}
    if weight != "normal":
        kwargs["weight"] = weight
    if family:
        kwargs["family"] = family
    hit = ctk.CTkFont(**kwargs)
    _font_cache[key] = hit
    return hit


def _work_area() -> tuple[int, int, int, int]:
    global _work_area_cache
    if _work_area_cache is not None:
        return _work_area_cache
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class RECT(ctypes.Structure):
                _fields_ = [
                    ("left", wintypes.LONG),
                    ("top", wintypes.LONG),
                    ("right", wintypes.LONG),
                    ("bottom", wintypes.LONG),
                ]

            rect = RECT()
            ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)
            _work_area_cache = rect.left, rect.top, rect.right, rect.bottom
            return _work_area_cache
        except Exception:
            pass
    _work_area_cache = 0, 0, 1920, 1040
    return _work_area_cache


def _swords_image() -> Image.Image | None:
    global _swords_pil
    if _swords_pil is not None:
        return _swords_pil
    swords_path = ASSETS_DIR / "capt_swords.png"
    if swords_path.is_file():
        _swords_pil = Image.open(swords_path).convert("RGBA")
    return _swords_pil


def _capt_badge(event: CaptEvent) -> tuple[str, str]:
    if event.is_defense:
        return "CAPT · ЗАЩИТА", DANGER
    return "CAPT · АТАКА", WARNING


def _subtitle(event: CaptEvent, server_id: str) -> str:
    zone = f"ЗОНА {event.zone_id}" if event.zone_id is not None else "ЗОНА —"
    return f"{zone}  ·  {server_id}  ·  Majestic RP"


class CaptPopup(ctk.CTkToplevel):
    def __init__(self, master, event: CaptEvent, *, server_id: str = MAJESTIC_SERVER_ID) -> None:
        super().__init__(master)
        self._event = event
        self._server_id = server_id
        self._accent = _capt_badge(event)[1]
        self._images: list[ctk.CTkImage] = []
        self._target_x = 0
        self._target_y = 0
        self._slide_step = 0
        self._elapsed = 0
        self._closing = False
        self._progress: ctk.CTkProgressBar | None = None

        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.97)
        except Exception:
            pass
        self.configure(fg_color=BG)
        self.resizable(False, False)

        self._build()
        _active.append(self)
        self.after(30, self._appear)

    def _appear(self) -> None:
        self.update_idletasks()
        w = max(POPUP_W, self.winfo_reqwidth())
        h = self.winfo_reqheight()
        self._target_x, self._target_y = self._calc_xy(w, h)
        off_x = 56
        self.geometry(f"{w}x{h}+{self._target_x + off_x}+{self._target_y}")
        self.deiconify()
        self._slide_step = 0
        self._animate_in(off_x)

    def _animate_in(self, off_x: int) -> None:
        if self._slide_step >= SLIDE_STEPS:
            w = int(self.winfo_width())
            h = int(self.winfo_height())
            self.geometry(f"{w}x{h}+{self._target_x}+{self._target_y}")
            self._tick_timer()
            return
        t = (self._slide_step + 1) / SLIDE_STEPS
        ease = 1 - (1 - t) ** 3
        x = self._target_x + int(off_x * (1 - ease))
        w = max(POPUP_W, self.winfo_width())
        h = self.winfo_height()
        self.geometry(f"{w}x{h}+{x}+{self._target_y}")
        self._slide_step += 1
        self.after(SLIDE_MS, lambda: self._animate_in(off_x))

    def _tick_timer(self) -> None:
        if self._closing:
            return
        self._elapsed += TICK_MS
        if self._progress:
            left = max(0.0, 1.0 - self._elapsed / AUTO_CLOSE_MS)
            self._progress.set(left)
        if self._elapsed >= AUTO_CLOSE_MS:
            self._fade_out()
            return
        self.after(TICK_MS, self._tick_timer)

    def _fade_out(self) -> None:
        self._closing = True
        try:
            alpha = float(self.attributes("-alpha"))
        except Exception:
            self._close_self()
            return
        if alpha <= 0.35:
            self._close_self()
            return
        try:
            self.attributes("-alpha", alpha - 0.08)
        except Exception:
            self._close_self()
            return
        self.after(30, self._fade_out)

    def _calc_xy(self, w: int, h: int) -> tuple[int, int]:
        _left, _top, right, bottom = _work_area()
        stack = max(0, len(_active) - 1)
        x = right - w - MARGIN_X
        y = bottom - h - MARGIN_Y - stack * (h + STACK_GAP)
        return max(_left + 8, x), max(_top + 8, y)

    def _build(self) -> None:
        shell = ctk.CTkFrame(
            self,
            fg_color=BG,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        shell.pack(fill="both", expand=True)

        body = ctk.CTkFrame(shell, fg_color=BG, corner_radius=13)
        body.pack(fill="both", expand=True, padx=1, pady=1)

        header = ctk.CTkFrame(body, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(12, 6))

        badge_text, badge_color = _capt_badge(self._event)
        ctk.CTkLabel(
            header,
            text=badge_text,
            font=_font(13, weight="bold"),
            text_color=badge_color,
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=APP_NAME,
            font=_font(11),
            text_color=MUTED,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            header,
            text="×",
            width=26,
            height=26,
            corner_radius=13,
            fg_color=CARD,
            hover_color=BORDER,
            text_color=MUTED,
            font=_font(15),
            command=self._fade_out,
        ).pack(side="right")

        row = ctk.CTkFrame(body, fg_color=CARD, corner_radius=12)
        row.pack(fill="x", padx=14, pady=(2, 8))

        inner = ctk.CTkFrame(row, fg_color="transparent")
        inner.pack(fill="x", padx=6, pady=10)
        inner.grid_columnconfigure((0, 1, 2), weight=1)

        our_left = self._event.is_attack
        self._add_side(inner, self._event.attacker, column=0, highlight=our_left)
        self._add_swords(inner, column=1)
        self._add_side(inner, self._event.defender, column=2, highlight=not our_left)

        ctk.CTkLabel(
            body,
            text=_subtitle(self._event, self._server_id),
            font=_font(10, family="Consolas"),
            text_color=MUTED,
        ).pack(anchor="w", padx=16, pady=(0, 6))

        self._progress = ctk.CTkProgressBar(
            body,
            height=3,
            corner_radius=2,
            fg_color=CARD,
            progress_color=self._accent,
            border_width=0,
        )
        self._progress.set(1.0)
        self._progress.pack(fill="x", padx=16, pady=(0, 12))

    def _ctk_image(self, pil_img: Image.Image, size: int) -> ctk.CTkImage:
        img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(size, size))
        self._images.append(img)
        return img

    def _add_side(self, parent: ctk.CTkFrame, side: FamilySide, *, column: int, highlight: bool) -> None:
        wrap = ctk.CTkFrame(
            parent,
            fg_color=CARD_INNER,
            corner_radius=12,
        )
        wrap.grid(row=0, column=column, sticky="nsew", padx=4, pady=2)

        col = ctk.CTkFrame(wrap, fg_color="transparent")
        col.pack(padx=8, pady=10)

        ring = self._accent if highlight else None
        avatar = load_family_avatar(side, size=50, ring_color=ring, server_id=self._server_id)
        ctk.CTkLabel(col, text="", image=self._ctk_image(avatar, 50)).pack()

        ctk.CTkLabel(
            col,
            text=side.display_name[:14],
            font=_font(13, weight="bold"),
            text_color=WHITE if highlight else TEXT,
            wraplength=100,
            justify="center",
        ).pack(pady=(6, 0))

        tag = side.tag or side.short_label
        if tag and tag.casefold() != side.display_name[: len(tag)].casefold():
            ctk.CTkLabel(
                col,
                text=tag.upper(),
                font=_font(9),
                text_color=MUTED,
            ).pack(pady=(2, 0))

    def _add_swords(self, parent: ctk.CTkFrame, *, column: int) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=column, sticky="ns", pady=8)

        img = _swords_image()
        if img is not None:
            ctk.CTkLabel(frame, text="", image=self._ctk_image(img, 34)).pack(pady=(18, 2))
        else:
            ctk.CTkLabel(frame, text="⚔", font=_font(22), text_color=WHITE).pack(pady=(18, 2))

        ctk.CTkLabel(
            frame,
            text="VS",
            font=_font(9, weight="bold"),
            text_color=MUTED,
        ).pack()

    def _close_self(self) -> None:
        try:
            if self in _active:
                _active.remove(self)
            self.destroy()
        except Exception:
            pass


def show_capt_popup(master, event: CaptEvent, *, server_id: str = MAJESTIC_SERVER_ID) -> None:
    CaptPopup(master, event, server_id=server_id)
