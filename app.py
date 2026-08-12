"""God Peace — minimal hub UI."""

from __future__ import annotations

import os
import threading
import tkinter.messagebox as messagebox
import webbrowser
from typing import Any

import customtkinter as ctk
from PIL import Image

from calamity_runner import (
    bundle_ready as calamity_ready,
    create_restore_point,
    is_admin,
    relaunch_as_admin,
    run_optimization,
)
from capt_notifier import notify_capt
from capt_popup import show_capt_popup
from capt_watcher import CaptWatcher
from config import (
    APP_NAME,
    ASSETS_DIR,
    BUNDLED_DIR,
    DISCORD_DEVELOPER,
    DISCORD_XGOD_URL,
    MAJESTIC_FAMILY_NAME,
    MAJESTIC_SERVER_ID,
)
from family_registry import refresh_registry
from gif_banner import GifBanner
from hub_state import record_optimization
from majestic_captures import CaptEvent, make_test_event
from mapmark_launcher import bundle_ready as mapmark_ready
from mapmark_launcher import run_mapmark
from single_instance import start_activation_server
from system_status import format_status_line, invalidate_static_cache
from tray_icon import TrayIcon

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG = "#0a0a0a"
CARD = "#111111"
CARD_HOVER = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT = "#f0f0f0"
MUTED = "#888888"
ACCENT = "#c0392b"
ACCENT_HOVER = "#96281b"
SUCCESS = "#27ae60"
WARNING = "#d4a017"


class HubApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("420x680")
        self.minsize(380, 560)
        self.configure(fg_color=BG)

        self._busy = False
        self._quitting = False
        self._tray: TrayIcon | None = None
        self._capt_watcher: CaptWatcher | None = None
        self._ipc_stop = None

        self._apply_window_icon()
        self._ipc_stop, _ = start_activation_server(self._show_window)
        self._load_assets()
        self._build_ui()
        self._start_tray()
        self._start_capt_watcher()

        self.bind("<FocusIn>", lambda _e: self._refresh_dynamic_ui())
        self.after(200, self._refresh_dynamic_ui)
        self.after(1000, self._tick_system_status)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_window_icon(self) -> None:
        ico = ASSETS_DIR / "icon.ico"
        try:
            if ico.is_file():
                self.iconbitmap(str(ico))
        except Exception:
            pass

    def _load_assets(self) -> None:
        self._clan_icon = self._load_image(ASSETS_DIR / "discord_xgod.png", 20)
        self._feedback_icon = self._load_image(ASSETS_DIR / "discord_feedback.png", 20)

    def _load_image(self, path: Any, size: int) -> ctk.CTkImage | None:
        try:
            if path.is_file():
                img = Image.open(path).convert("RGBA").resize((size, size), Image.LANCZOS)
                return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        except Exception:
            return None
        return None

    def _start_tray(self) -> None:
        icon_png = ASSETS_DIR / "icon.png"
        if not icon_png.is_file():
            return
        self._tray = TrayIcon(
            icon_path=icon_png,
            tooltip=APP_NAME,
            on_show=self._show_window,
            on_quit=self._quit_app,
        )
        self._tray.start()

    def _show_window(self) -> None:
        self.after(0, self._deiconify_raise)

    def _deiconify_raise(self) -> None:
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
        except Exception:
            pass

    def _on_close(self) -> None:
        self.withdraw()

    def _quit_app(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        if self._ipc_stop:
            self._ipc_stop.set()
        if self._capt_watcher:
            self._capt_watcher.stop()
        if self._tray:
            self._tray.stop()
        self.destroy()

    def _build_ui(self) -> None:
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            scrollbar_button_color=CARD,
            scrollbar_button_hover_color=BORDER,
        )
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        self._scroll = scroll

        self._build_banner(scroll)
        self._build_status_line(scroll)
        self._build_optimization_card(scroll)
        self._build_mapmark_card(scroll)
        self._build_majestic_card(scroll)
        self._build_extra_tools_card(scroll)
        self._build_footer(scroll)

        self._status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            anchor="w",
            wraplength=360,
            justify="left",
        )
        self._status_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))

    def _build_banner(self, parent: ctk.CTkScrollableFrame) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        frame.grid_columnconfigure(0, weight=1)

        banner = GifBanner(frame, ASSETS_DIR / "xgod-banner.gif", width=388)
        banner.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            frame,
            text=APP_NAME,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT,
        ).grid(row=1, column=0, pady=(12, 0))

        ctk.CTkLabel(
            frame,
            text=f"{MAJESTIC_FAMILY_NAME} · Majestic {MAJESTIC_SERVER_ID}",
            font=ctk.CTkFont(size=12),
            text_color=ACCENT,
        ).grid(row=2, column=0)

    def _build_status_line(self, parent: ctk.CTkScrollableFrame) -> None:
        self._sys_status = ctk.CTkLabel(
            parent,
            text=format_status_line(),
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=MUTED,
        )
        self._sys_status.grid(row=1, column=0, pady=(0, 12))

    def _card(self, parent: ctk.CTkScrollableFrame, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 10))
        card.grid_columnconfigure(0, weight=1)
        return card

    def _build_optimization_card(self, parent: ctk.CTkScrollableFrame) -> None:
        card = self._card(parent, 2)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner,
            text="Оптимизация Windows",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text="Calamity — применить пресет твиков",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self._mode_var = ctk.StringVar(value="gaming")
        menu = ctk.CTkOptionMenu(
            inner,
            variable=self._mode_var,
            values=["safe", "gaming", "full"],
            width=110,
            fg_color=BG,
            button_color=BORDER,
            button_hover_color=ACCENT,
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
        )
        menu.grid(row=0, column=1, rowspan=2, sticky="e")
        menu.set("gaming")

        ctk.CTkButton(
            inner,
            text="Запустить",
            height=34,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#fff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_run_optimization,
        ).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(14, 0))

    def _build_mapmark_card(self, parent: ctk.CTkScrollableFrame) -> None:
        card = self._card(parent, 3)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner,
            text="MapMark",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text="Установка/запуск встроенного MapMark",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        ctk.CTkButton(
            inner,
            text="Запустить",
            width=100,
            height=30,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#fff",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_mapmark,
        ).grid(row=0, column=1, rowspan=2, sticky="e")

    def _build_majestic_card(self, parent: ctk.CTkScrollableFrame) -> None:
        card = self._card(parent, 4)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner,
            text=f"Капты · {MAJESTIC_FAMILY_NAME}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            inner,
            text=f"{MAJESTIC_SERVER_ID} · уведомление, если на нас напали",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        self._capt_status = ctk.CTkLabel(
            inner,
            text="CAPT · инициализация...",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=MUTED,
            anchor="w",
        )
        self._capt_status.grid(row=2, column=0, sticky="w", pady=(8, 0))

        self._api_key_var = ctk.StringVar(value=os.environ.get("MAJESTIC_API_KEY", ""))
        entry = ctk.CTkEntry(
            inner,
            textvariable=self._api_key_var,
            placeholder_text="MAJESTIC_API_KEY",
            height=30,
            show="•",
            fg_color=BG,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=11),
        )
        entry.grid(row=3, column=0, sticky="ew", pady=(10, 0))

        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            btn_frame,
            text="Копировать",
            height=28,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=11),
            command=self._on_copy_key,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            btn_frame,
            text="Сохранить",
            height=28,
            fg_color=ACCENT,
            hover_color=ACCENT_HOVER,
            text_color="#fff",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._on_save_key,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _build_extra_tools_card(self, parent: ctk.CTkScrollableFrame) -> None:
        card = self._card(parent, 5)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="ew", padx=16, pady=14)
        inner.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inner,
            text="Быстрые фиксы",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        fixes = [
            ("Сеть", self._on_fix_network),
            ("Клава", self._on_fix_keyboard),
            ("Мониторы", self._on_fix_multimon),
            ("BCD откат", self._on_emergency_bcd),
        ]

        for i, (label, cmd) in enumerate(fixes):
            ctk.CTkButton(
                inner,
                text=label,
                height=28,
                fg_color=BG,
                hover_color=CARD_HOVER,
                border_width=1,
                border_color=BORDER,
                text_color=TEXT,
                font=ctk.CTkFont(size=11),
                command=cmd,
            ).grid(row=1 + i // 2, column=i % 2, sticky="ew", padx=(0 if i % 2 == 0 else 4, 4 if i % 2 == 0 else 0), pady=(0, 6))

    def _build_footer(self, parent: ctk.CTkScrollableFrame) -> None:
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=6, column=0, sticky="ew", padx=16, pady=(6, 20))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame,
            text="Discord XGOD",
            image=self._clan_icon,
            compound="left",
            height=36,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_discord_clan,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            frame,
            text="Обратная связь",
            image=self._feedback_icon,
            compound="left",
            height=36,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=BORDER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_feedback,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    def _start_capt_watcher(self) -> None:
        self._capt_watcher = CaptWatcher(
            on_status=lambda text: self.after(0, lambda: self._set_capt_status(text)),
            on_error=lambda text: self.after(0, lambda: self._set_capt_status(f"ошибка · {text}", error=True)),
            on_notify_ui=self._capt_notify_fallback,
            show_popup=self._deliver_capt_popup,
        )
        self._capt_watcher.start()

    def _set_capt_status(self, text: str, *, error: bool = False) -> None:
        if not self._capt_status:
            return
        prefix = "CAPT ERR" if error else "CAPT"
        self._capt_status.configure(text=f"{prefix} · {text}", text_color=ACCENT if error else MUTED)

    def _capt_notify_fallback(self, title: str, message: str) -> None:
        self.after(0, lambda: messagebox.showinfo(title, message))

    def _deliver_capt_popup(self, event: CaptEvent) -> None:
        self.after(0, lambda e=event: show_capt_popup(self, e, server_id=MAJESTIC_SERVER_ID))

    def _on_run_optimization(self) -> None:
        if self._busy:
            return
        if not self._require_admin():
            return
        mode = self._mode_var.get()
        create_rp = messagebox.askyesno(APP_NAME, f"Запустить пресет {mode}?\n\nСоздать точку восстановления?", icon="question")

        self._busy = True
        self._set_status("Запуск оптимизации...")

        def work() -> None:
            rp_ok = False
            try:
                if create_rp:
                    self._set_status_async("Создание точки восстановления...")
                    rp_ok, _ = create_restore_point(APP_NAME)

                def prog(i: int, n: int, name: str) -> None:
                    self._set_status_async(f"{i}/{n}: {name}")

                ok, total, errors, needs_reboot, applied = run_optimization(mode, on_progress=prog)
                record_optimization(mode, applied, rp_ok)

                summary = f"Готово: {ok} из {total}"
                color = SUCCESS if ok == total else WARNING
                if needs_reboot:
                    summary += " · требуется перезагрузка"
                self._set_status_async(summary, color)
                if errors:
                    messagebox.showinfo("Результат", summary + "\n\n" + "\n".join(f"• {e}" for e in errors[:8]))
            except Exception as exc:
                self._set_status_async(f"Ошибка: {exc}", ACCENT)
            finally:
                self._busy = False

        threading.Thread(target=work, daemon=True).start()

    def _on_mapmark(self) -> None:
        if mapmark_ready():
            ok, msg, _ = run_mapmark()
            self._set_status(msg, SUCCESS if ok else ACCENT)
        else:
            messagebox.showerror(APP_NAME, f"Установщик MapMark не найден:\n{BUNDLED_DIR / 'installers'}")

    def _on_fix_network(self) -> None:
        from extra_tweaks import apply_network_fix
        ok, msg = apply_network_fix()
        self._set_status(msg, SUCCESS if ok else ACCENT)

    def _on_fix_keyboard(self) -> None:
        from extra_tweaks import apply_keyboard_fix
        ok, msg = apply_keyboard_fix()
        self._set_status(msg, SUCCESS if ok else ACCENT)

    def _on_fix_multimon(self) -> None:
        from extra_tweaks import apply_multimon_fix
        ok, msg = apply_multimon_fix()
        self._set_status(msg, SUCCESS if ok else ACCENT)

    def _on_emergency_bcd(self) -> None:
        if not self._require_admin():
            return
        from bundled.calamity.boot_risk import emergency_boot_recovery
        ok, msg = emergency_boot_recovery()
        self._set_status(msg, SUCCESS if ok else ACCENT)
        messagebox.showinfo("Экстренный откат BCD", msg)

    def _on_copy_key(self) -> None:
        key = self._api_key_var.get().strip()
        if not key:
            messagebox.showwarning(APP_NAME, "Нечего копировать")
            return
        try:
            self.clipboard_clear()
            self.clipboard_append(key)
            self.update()
            self._set_status("Ключ скопирован", SUCCESS)
        except Exception as exc:
            self._set_status(f"Ошибка копирования: {exc}", ACCENT)

    def _on_save_key(self) -> None:
        key = self._api_key_var.get().strip()
        if not key:
            messagebox.showwarning(APP_NAME, "Введите API-ключ")
            return
        env_path = Path(os.path.dirname(os.path.abspath(__file__))) / "majestic.env"
        try:
            lines = []
            if env_path.is_file():
                lines = env_path.read_text(encoding="utf-8").splitlines()
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("MAJESTIC_API_KEY="):
                    lines[i] = f"MAJESTIC_API_KEY={key}"
                    updated = True
                    break
            if not updated:
                lines.append(f"MAJESTIC_API_KEY={key}")
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            os.environ["MAJESTIC_API_KEY"] = key
            messagebox.showinfo(APP_NAME, "Ключ сохранён. Перезапусти приложение.")
            self._set_status("Ключ сохранён", SUCCESS)
        except Exception as exc:
            messagebox.showerror(APP_NAME, f"Ошибка сохранения: {exc}")

    def _require_admin(self) -> bool:
        if is_admin():
            return True
        self._set_status("Нужны права администратора. Подтверди UAC...", WARNING)
        relaunch_as_admin()
        return False

    def _refresh_dynamic_ui(self) -> None:
        invalidate_static_cache()
        if self._sys_status:
            self._sys_status.configure(text=format_status_line())

    def _tick_system_status(self) -> None:
        if self._sys_status and not self._busy:
            self._sys_status.configure(text=format_status_line())
        self.after(5000, self._tick_system_status)

    def _set_status(self, text: str, color: str = MUTED) -> None:
        self._status_label.configure(text=text, text_color=color)

    def _set_status_async(self, text: str, color: str = MUTED) -> None:
        self.after(0, lambda: self._set_status(text, color))

    def _on_discord_clan(self) -> None:
        webbrowser.open(DISCORD_XGOD_URL)
        self._set_status("Discord XGOD открыт.", SUCCESS)

    def _on_feedback(self) -> None:
        nick = DISCORD_DEVELOPER
        try:
            self.clipboard_clear()
            self.clipboard_append(nick)
            self.update()
        except Exception:
            pass
        try:
            os.startfile("discord:")
        except OSError:
            webbrowser.open("https://discord.com/channels/@me")
        messagebox.showinfo(APP_NAME, f"Ник «{nick}» скопирован. Добавь в Discord для связи.")


def main() -> None:
    app = HubApp()
    app.mainloop()
