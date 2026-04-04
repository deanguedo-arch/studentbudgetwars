from __future__ import annotations

import os
import tkinter as tk
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Callable

from budgetwars.core import GameSession, StartupOptions


@dataclass
class DesktopMail:
    sender: str
    subject: str
    received: str
    body: str
    unread: bool = False


@dataclass(frozen=True)
class DesktopAction:
    label: str
    icon_name: str
    callback: Callable[[], None]


@dataclass
class DesktopWindowState:
    app_id: str
    title: str
    position: tuple[int, int]
    size: tuple[int, int]
    normal_position: tuple[int, int]
    normal_size: tuple[int, int]
    toplevel: tk.Toplevel
    host: tk.Frame
    task_button: tk.Label
    minimized: bool = False
    maximized: bool = False


class DesktopShellApp:
    def __init__(self, session: GameSession, *, startup_options: StartupOptions | None = None):
        self.session = session
        self.startup_options = startup_options or session.options
        self.controller = self.session.ensure_started(default_player_name=self.startup_options.player_name or "DesktopPlayer")
        self.active_app = "mail"
        self.browser_page = "jobs"
        self.profile_tab = "info"
        self.mail_index = 0
        self.base_window_position = (798, 370)
        self.base_window_size = (778, 600)
        self.drag_origin: tuple[int, int] | None = None
        self.window_origin: tuple[int, int] | None = None
        self.dragging_app: str | None = None
        self.resize_origin: tuple[int, int] | None = None
        self.resize_size_origin: tuple[int, int] | None = None
        self.resize_position_origin: tuple[int, int] | None = None
        self.resize_direction: str | None = None
        self.resizing_app: str | None = None
        self.active_scroll_canvas: tk.Canvas | None = None
        self.open_windows: dict[str, DesktopWindowState] = {}
        self.start_menu_visible = False
        self.selected_recent_save: str | None = None
        self.icon_positions = self._icon_default_positions()
        self.icon_windows: dict[str, str] = {}
        self.icon_dragging: str | None = None
        self.icon_drag_origin: tuple[int, int] | None = None
        self.icon_drag_moved = False

        self.root = tk.Tk()
        self.root.configure(bg="#3b6ed4")
        self.root.geometry("1360x820")
        self.root.minsize(1120, 700)
        self.root.option_add("*Font", ("Tahoma", 10))
        self.root.title("After Grad Desktop")
        self.root.bind_all("<ButtonPress-1>", self._on_global_pointer_down, add="+")
        self.root.bind_all("<MouseWheel>", self._on_global_mousewheel)
        self.root.bind_all("<Button-4>", self._on_global_mousewheel)
        self.root.bind_all("<Button-5>", self._on_global_mousewheel)

        self.assets_root = self._resolve_assets_root()
        self.wallpaper_image: tk.PhotoImage | None = None
        self.icon_images: dict[str, tk.PhotoImage] = {}
        self.small_icons: dict[str, tk.PhotoImage] = {}
        self.profile_avatar_image: tk.PhotoImage | None = None
        self._load_assets()
        self._build_shell()
        self.open_app("mail")

    def _resolve_assets_root(self) -> Path:
        repo_root = Path(__file__).resolve().parents[4]
        return repo_root / "assets" / "desktop"

    def _load_assets(self) -> None:
        xp_root = self.assets_root / "xp"
        xp_wallpaper = xp_root / "wallpaper.png"
        fallback_wallpaper = self.assets_root / "wallpaper.ppm"
        if xp_wallpaper.exists():
            wallpaper = tk.PhotoImage(file=str(xp_wallpaper))
            self.wallpaper_image = wallpaper.zoom(2, 2) if wallpaper.width() < 1200 else wallpaper
        elif fallback_wallpaper.exists():
            self.wallpaper_image = tk.PhotoImage(file=str(fallback_wallpaper))

        for name in ("profile", "mail", "bank", "internet", "save", "leaderboard", "paperclip"):
            xp_icon_path = xp_root / "icons" / f"{name}.png"
            fallback_icon_path = self.assets_root / "icons" / f"{name}.ppm"
            if xp_icon_path.exists():
                self.icon_images[name] = tk.PhotoImage(file=str(xp_icon_path))
            elif fallback_icon_path.exists():
                self.icon_images[name] = tk.PhotoImage(file=str(fallback_icon_path))
        self.small_icons = {
            name: image.subsample(2, 2) if image.width() >= 32 else image
            for name, image in self.icon_images.items()
        }

    def _icon_default_positions(self) -> dict[str, tuple[int, int]]:
        return {
            "profile": (52, 112),
            "mail": (52, 240),
            "bank": (52, 368),
            "browser": (52, 496),
            "save": (52, 624),
            "leaderboard": (52, 752),
        }

    def _build_shell(self) -> None:
        self.top_strip = tk.Frame(self.root, bg="#f2f5f7", height=34)
        self.top_strip.pack(fill="x", side="top")
        self.top_strip.pack_propagate(False)
        tk.Label(
            self.top_strip,
            text="EIPS Chrome Quick Links      \u25a6\u25a6",
            bg="#f2f5f7",
            fg="#1f2937",
            anchor="w",
            padx=18,
            font=("Tahoma", 9),
        ).pack(fill="both", expand=True)

        self.metrics_bar = tk.Frame(self.root, bg="#d7e4ff", height=42)
        self.metrics_bar.pack(fill="x", side="top")
        self.metrics_bar.pack_propagate(False)
        self.metrics_labels: dict[str, tk.Label] = {}
        for key in ("cash", "stress", "energy", "housing", "career"):
            card = tk.Frame(self.metrics_bar, bg="#f4f8ff", bd=1, relief="solid")
            card.pack(side="left", padx=6, pady=5)
            tk.Label(card, text=key.title(), bg="#f4f8ff", fg="#4b5563", padx=8, font=("Tahoma", 8, "bold")).pack(side="left")
            value = tk.Label(card, text="--", bg="#f4f8ff", fg="#111827", padx=8, font=("Tahoma", 9, "bold"))
            value.pack(side="left")
            self.metrics_labels[key] = value

        self.top_next_turn_button = tk.Button(
            self.metrics_bar,
            text="Next turn",
            command=self.resolve_month,
            bg="#fff6d6",
            fg="#111827",
            activebackground="#ffe9a8",
            relief="raised",
            bd=1,
            padx=18,
            pady=6,
            font=("Tahoma", 10, "bold"),
        )
        self.top_next_turn_button.pack(side="right", padx=10)

        self.desktop = tk.Canvas(self.root, bg="#5e8ff4", highlightthickness=0)
        self.desktop.pack(fill="both", expand=True)
        self.desktop.bind("<Configure>", self._draw_wallpaper)
        self.desktop.bind("<Button-1>", self._maybe_close_start_menu)

        self.helper_frame = tk.Frame(self.desktop, bg="#fff4b9", bd=1, relief="solid")
        self.desktop.create_window(1128, 560, window=self.helper_frame, width=250, height=118, anchor="nw")
        self.helper_label = tk.Label(
            self.helper_frame,
            text="",
            bg="#fff4b9",
            fg="#222222",
            justify="left",
            wraplength=206,
            padx=18,
            pady=14,
            font=("Tahoma", 10),
        )
        self.helper_label.pack(fill="both", expand=True)

        self.toast_frame = tk.Frame(self.desktop, bg="#fff6c9", bd=1, relief="solid")
        self.desktop.create_window(1068, 82, window=self.toast_frame, width=310, height=76, anchor="nw")
        self.toast_title = tk.Label(self.toast_frame, text="Desktop Alert", bg="#fff6c9", fg="#3b3b3b", anchor="w", padx=10, pady=4, font=("Tahoma", 9, "bold"))
        self.toast_title.pack(fill="x")
        self.toast_label = tk.Label(self.toast_frame, text="", bg="#fff6c9", fg="#222222", justify="left", wraplength=280, padx=10, pady=4, font=("Tahoma", 9))
        self.toast_label.pack(fill="both", expand=True)

        paperclip_icon = self.icon_images.get("paperclip")
        self.paperclip_label = tk.Label(
            self.desktop,
            image=paperclip_icon,
            text="" if paperclip_icon else "( )\n/|\\\n / \\",
            bg="#5e8ff4",
            fg="#f8f8f8",
            justify="center",
            font=("Consolas", 14, "bold"),
            compound="top",
        )
        self.desktop.create_window(1102, 655, window=self.paperclip_label, anchor="nw")

        self.taskbar = tk.Frame(self.root, bg="#1154d8", height=30)
        self.taskbar.pack(fill="x", side="bottom")
        self.taskbar.pack_propagate(False)

        self.start_button = tk.Label(
            self.taskbar,
            text="Start",
            bg="#46ad42",
            fg="white",
            width=8,
            padx=12,
            font=("Tahoma", 12, "bold italic"),
            cursor="hand2",
        )
        self.start_button.pack(side="left")
        self.start_button.bind("<Button-1>", self.toggle_start_menu)
        tk.Frame(self.taskbar, bg="#0c3fb5", width=2).pack(side="left", fill="y")

        self.taskbar_windows = tk.Frame(self.taskbar, bg="#1154d8")
        self.taskbar_windows.pack(side="left", padx=6, pady=3)

        self.taskbar_status = tk.Label(
            self.taskbar,
            text="",
            bg="#1154d8",
            fg="white",
            anchor="w",
            padx=18,
            font=("Tahoma", 9),
        )
        self.taskbar_status.pack(side="left", fill="x", expand=True)

        self.tray_label = tk.Label(
            self.taskbar,
            text="",
            bg="#1154d8",
            fg="white",
            padx=10,
            font=("Tahoma", 9),
        )
        self.tray_label.pack(side="right")

        self.clock_label = tk.Label(
            self.taskbar,
            text="",
            bg="#1e88e5",
            fg="white",
            padx=14,
            font=("Tahoma", 9),
        )
        self.clock_label.pack(side="right")

        self._build_icons()
        self._build_start_menu()

    def _draw_wallpaper(self, event) -> None:
        self.desktop.delete("wallpaper")
        width = max(1, event.width)
        height = max(1, event.height)
        if self.wallpaper_image is not None:
            self.desktop.create_image(0, 0, image=self.wallpaper_image, anchor="nw", tags="wallpaper")
            if width > self.wallpaper_image.width():
                extra_width = width - self.wallpaper_image.width()
                self.desktop.create_rectangle(
                    self.wallpaper_image.width(),
                    0,
                    self.wallpaper_image.width() + extra_width,
                    height,
                    fill="#5e8ff4",
                    outline="",
                    tags="wallpaper",
                )
            if height > self.wallpaper_image.height():
                self.desktop.create_rectangle(
                    0,
                    self.wallpaper_image.height(),
                    width,
                    height,
                    fill="#5ea1f5",
                    outline="",
                    tags="wallpaper",
                )
            self.desktop.tag_lower("wallpaper")
            return
        self.desktop.create_rectangle(0, 0, width, height, fill="#5e8ff4", outline="", tags="wallpaper")
        self.desktop.create_oval(width * 0.08, 40, width * 0.82, height * 0.48, fill="#8ab1ff", outline="", tags="wallpaper")
        self.desktop.create_oval(width * 0.42, 20, width * 1.02, height * 0.52, fill="#6f9afb", outline="", tags="wallpaper")
        for x, y, w, h in (
            (100, 90, 250, 80),
            (width - 430, 120, 280, 92),
            (width * 0.3, 180, 220, 72),
            (width * 0.68, 250, 240, 84),
        ):
            self.desktop.create_oval(x, y, x + w, y + h, fill="#ffffff", outline="", tags="wallpaper")
            self.desktop.create_oval(x + 50, y - 10, x + w - 20, y + h - 8, fill="#ffffff", outline="", tags="wallpaper")
        self.desktop.create_arc(-160, height * 0.56, width + 140, height + 220, start=0, extent=180, fill="#75b84b", outline="", tags="wallpaper")
        self.desktop.create_arc(width * 0.36, height * 0.64, width + 240, height + 240, start=0, extent=180, fill="#66a63f", outline="", tags="wallpaper")
        self.desktop.tag_lower("wallpaper")

    def _build_icons(self) -> None:
        icons = [
            ("Profile", "profile", "profile"),
            ("Mail", "mail", "mail"),
            ("Bank Account", "bank", "bank"),
            ("Internet", "browser", "internet"),
            ("Save Game", "save", "save"),
            ("Leaderboard", "leaderboard", "leaderboard"),
        ]
        for label, app_id, icon_name in icons:
            icon_image = self.icon_images.get(icon_name)
            x, y = self.icon_positions[app_id]
            tag = f"desktop_icon::{app_id}"
            if icon_image is not None:
                self.desktop.create_image(x + 2, y + 2, image=icon_image, anchor="n", tags=(tag, "desktop_icon"))
                self.desktop.create_image(x, y, image=icon_image, anchor="n", tags=(tag, "desktop_icon"))
            self.desktop.create_text(
                x + 2,
                y + 60,
                text=label,
                fill="#16315f",
                font=("Tahoma", 8, "bold"),
                anchor="n",
                width=92,
                justify="center",
                tags=(tag, "desktop_icon"),
            )
            self.desktop.create_text(
                x,
                y + 59,
                text=label,
                fill="white",
                font=("Tahoma", 8, "bold"),
                anchor="n",
                width=92,
                justify="center",
                tags=(tag, "desktop_icon"),
            )
            self.icon_windows[app_id] = tag
            self.desktop.tag_bind(tag, "<ButtonPress-1>", lambda event, target=app_id: self._start_icon_drag(target, event))
            self.desktop.tag_bind(tag, "<B1-Motion>", self._on_icon_drag)
            self.desktop.tag_bind(tag, "<ButtonRelease-1>", self._end_icon_drag)
            self.desktop.tag_bind(tag, "<Double-Button-1>", lambda _event, target=app_id: self._open_desktop_icon(target))

    def _open_desktop_icon(self, app_id: str) -> None:
        if app_id == "leaderboard":
            self.show_leaderboard()
        elif app_id == "save":
            self.open_app("saves")
        else:
            self.open_app(app_id)

    def _build_start_menu(self) -> None:
        self.start_menu = tk.Frame(self.desktop, bg="#f4f6fb", bd=2, relief="solid")
        self.start_menu_id = self.desktop.create_window(0, 0, window=self.start_menu, anchor="sw", state="hidden")

        left_strip = tk.Frame(self.start_menu, bg="#0a4dbb", width=62)
        left_strip.pack(side="left", fill="y")
        left_strip.pack_propagate(False)
        tk.Label(
            left_strip,
            text="After Grad",
            bg="#0a4dbb",
            fg="white",
            font=("Tahoma", 11, "bold"),
            wraplength=28,
            justify="center",
        ).pack(side="bottom", pady=18)

        menu_body = tk.Frame(self.start_menu, bg="#f4f6fb")
        menu_body.pack(side="left", fill="both", expand=True)
        tk.Label(
            menu_body,
            text="Programs",
            bg="#dbe8fd",
            fg="#1f2937",
            anchor="w",
            padx=12,
            pady=8,
            font=("Tahoma", 10, "bold"),
        ).pack(fill="x")

        for label, app_id, icon_name in (
            ("Mail", "mail", "mail"),
            ("Bank Account", "bank", "bank"),
            ("Internet", "browser", "internet"),
            ("Profile", "profile", "profile"),
            ("Save Center", "saves", "save"),
        ):
            self._add_start_menu_button(menu_body, label, icon_name, lambda target=app_id: self._launch_from_start(target))

        self._add_start_menu_separator(menu_body)

        for label, icon_name, callback in (
            ("Tile Windows", "internet", self._start_tile_windows),
            ("Cascade Windows", "mail", self._start_cascade_windows),
        ):
            self._add_start_menu_button(menu_body, label, icon_name, callback)

        for label, icon_name, callback in (
            ("Save Snapshot", "save", self._start_save_snapshot),
            ("Load Snapshot", "save", self._start_load_snapshot),
            ("Restart Run", "leaderboard", self._start_restart_run),
            ("Exit Desktop", "paperclip", self._start_exit_desktop),
        ):
            self._add_start_menu_button(menu_body, label, icon_name, callback)

        tk.Label(
            menu_body,
            text="Recent Saves",
            bg="#dbe8fd",
            fg="#1f2937",
            anchor="w",
            padx=12,
            pady=8,
            font=("Tahoma", 10, "bold"),
        ).pack(fill="x", pady=(8, 0))
        self.start_recent_holder = tk.Frame(menu_body, bg="#f4f6fb")
        self.start_recent_holder.pack(fill="x", padx=8, pady=(0, 6))

    def _add_start_menu_button(self, parent: tk.Frame, label: str, icon_name: str, command) -> None:
        icon = self.icon_images.get(icon_name)
        button = tk.Button(
            parent,
            text=f" {label}",
            image=icon,
            compound="left",
            anchor="w",
            command=command,
            bg="#f4f6fb",
            activebackground="#d7e6ff",
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            font=("Tahoma", 10),
        )
        button.pack(fill="x", padx=8, pady=1)

    def _add_start_menu_separator(self, parent: tk.Frame) -> None:
        tk.Frame(parent, bg="#cfd9ee", height=1).pack(fill="x", padx=10, pady=6)

    def _launch_from_start(self, app_id: str) -> None:
        self.hide_start_menu()
        self.open_app(app_id)

    def _start_save_snapshot(self) -> None:
        self.hide_start_menu()
        self.save_snapshot()

    def _start_load_snapshot(self) -> None:
        self.hide_start_menu()
        self.load_snapshot_dialog()

    def _start_restart_run(self) -> None:
        self.hide_start_menu()
        self.restart_default_run()

    def _start_exit_desktop(self) -> None:
        self.hide_start_menu()
        self.root.destroy()

    def _start_tile_windows(self) -> None:
        self.hide_start_menu()
        self.tile_open_windows()

    def _start_cascade_windows(self) -> None:
        self.hide_start_menu()
        self.cascade_open_windows()

    def toggle_start_menu(self, _event=None) -> None:
        if self.start_menu_visible:
            self.hide_start_menu()
        else:
            self.show_start_menu()

    def show_start_menu(self) -> None:
        taskbar_y = self.desktop.winfo_height() or 760
        self.desktop.coords(self.start_menu_id, 0, taskbar_y)
        self.desktop.itemconfigure(self.start_menu_id, state="normal")
        self.desktop.tag_raise(self.start_menu_id)
        self.start_button.configure(bg="#5dc45a")
        self.start_menu_visible = True

    def hide_start_menu(self) -> None:
        self.desktop.itemconfigure(self.start_menu_id, state="hidden")
        self.start_button.configure(bg="#46ad42")
        self.start_menu_visible = False

    def _maybe_close_start_menu(self, _event=None) -> None:
        if self.start_menu_visible:
            self.hide_start_menu()

    def open_app(self, app_name: str) -> None:
        title = self._window_title(app_name)
        window = self.open_windows.get(app_name)
        if window is None:
            window = self._create_window(app_name, title)
            self.open_windows[app_name] = window
        else:
            window.title = title
            window.minimized = False
            window.toplevel.deiconify()
        self.active_app = app_name
        self._focus_window(app_name)
        self.refresh()

    def _start_icon_drag(self, app_id: str, event) -> None:
        self.icon_dragging = app_id
        self.icon_drag_origin = (event.x_root, event.y_root)
        self.icon_drag_moved = False

    def _on_icon_drag(self, event) -> None:
        if self.icon_dragging is None or self.icon_drag_origin is None:
            return
        app_id = self.icon_dragging
        current_x, current_y = self.icon_positions[app_id]
        delta_x = event.x_root - self.icon_drag_origin[0]
        delta_y = event.y_root - self.icon_drag_origin[1]
        width = max(self.desktop.winfo_width(), 1200)
        height = max(self.desktop.winfo_height(), 720)
        new_x = min(max(current_x + delta_x, 36), width - 80)
        new_y = min(max(current_y + delta_y, 48), height - 120)
        if abs(delta_x) > 2 or abs(delta_y) > 2:
            self.icon_drag_moved = True
        self.icon_positions[app_id] = (new_x, new_y)
        self.desktop.move(self.icon_windows[app_id], delta_x, delta_y)
        self.icon_drag_origin = (event.x_root, event.y_root)

    def _end_icon_drag(self, _event) -> None:
        if self.icon_dragging is not None:
            x, y = self.icon_positions[self.icon_dragging]
            snap_x = 52 + round((x - 52) / 88) * 88
            snap_y = 112 + round((y - 112) / 118) * 118
            width = max(self.desktop.winfo_width(), 1200)
            height = max(self.desktop.winfo_height(), 720)
            snap_x = min(max(snap_x, 36), width - 80)
            snap_y = min(max(snap_y, 48), height - 120)
            self.desktop.move(self.icon_windows[self.icon_dragging], snap_x - x, snap_y - y)
            self.icon_positions[self.icon_dragging] = (snap_x, snap_y)
            if not self.icon_drag_moved:
                self._open_desktop_icon(self.icon_dragging)
        self.icon_dragging = None
        self.icon_drag_origin = None
        self.icon_drag_moved = False

    def _window_title(self, app_id: str) -> str:
        return {
            "mail": "Inbox - Outlook Express",
            "bank": "Young Saver Bank PLC",
            "browser": "EIPS Explorer",
            "profile": "Profile",
            "saves": "Save Center",
        }.get(app_id, app_id.title())

    def _task_title(self, app_id: str) -> str:
        return {
            "mail": " Outlook Express",
            "bank": " Young Saver Bank",
            "browser": " EIPS Explorer",
            "profile": " Profile",
            "saves": " Save Center",
        }.get(app_id, f" {app_id.title()}")

    def _create_window(self, app_id: str, title: str) -> DesktopWindowState:
        self.root.update_idletasks()
        index = len(self.open_windows)
        origin_x, origin_y = self._desktop_origin()
        position = (origin_x + self.base_window_position[0] + (index * 34), origin_y + self.base_window_position[1] + (index * 28))
        size = self.base_window_size
        toplevel = tk.Toplevel(self.root)
        toplevel.overrideredirect(True)
        toplevel.configure(bg="#0a2f82")
        toplevel.attributes("-topmost", False)
        host = tk.Frame(toplevel, bg="#5e8ff4", bd=0, highlightthickness=0)
        host.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        host._desktop_focus_target = app_id
        toplevel._desktop_focus_target = app_id
        host.bind("<ButtonPress-1>", lambda _event, target=app_id: self._focus_window(target), add="+")
        toplevel.bind("<ButtonPress-1>", lambda _event, target=app_id: self._focus_window(target), add="+")
        toplevel.bind("<FocusIn>", lambda _event, target=app_id: self._mark_active_window(target), add="+")
        task_button = tk.Label(
            self.taskbar_windows,
            text=self._task_title(app_id),
            bg="#2e69db",
            fg="white",
            padx=14,
            font=("Tahoma", 9, "bold"),
            anchor="w",
            width=18,
        )
        task_button.pack(side="left", padx=3)
        task_button.bind("<Button-1>", lambda _event, target=app_id: self.toggle_task_window(target))
        window = DesktopWindowState(
            app_id=app_id,
            title=title,
            position=position,
            size=size,
            normal_position=position,
            normal_size=size,
            toplevel=toplevel,
            host=host,
            task_button=task_button,
        )
        self._apply_window_geometry(window)
        return window

    def _apply_window_geometry(self, window: DesktopWindowState) -> None:
        left = int(window.position[0] - (window.size[0] // 2))
        top = int(window.position[1] - (window.size[1] // 2))
        window.toplevel.geometry(f"{window.size[0]}x{window.size[1]}+{left}+{top}")

    def _mark_active_window(self, app_id: str) -> None:
        if app_id not in self.open_windows:
            return
        for key, window in self.open_windows.items():
            active = key == app_id and not window.minimized
            window.task_button.configure(bg="#3f86f4" if active else "#2e69db")
        self.active_app = app_id

    def _focus_window(self, app_id: str) -> None:
        if app_id not in self.open_windows:
            return
        window = self.open_windows[app_id]
        if window.minimized:
            window.minimized = False
            window.toplevel.deiconify()
        self._mark_active_window(app_id)
        try:
            window.toplevel.lift()
            window.toplevel.attributes("-topmost", True)
            window.toplevel.attributes("-topmost", False)
            window.toplevel.focus_force()
        except tk.TclError:
            return

    def _on_global_pointer_down(self, event) -> None:
        widget = getattr(event, "widget", None)
        while widget is not None:
            target = getattr(widget, "_desktop_focus_target", None)
            if target and target in self.open_windows:
                self._focus_window(target)
                return
            widget = getattr(widget, "master", None)

    def _desktop_bounds(self) -> tuple[int, int]:
        self.root.update_idletasks()
        width = self.desktop.winfo_width()
        height = self.desktop.winfo_height()
        if width <= 1:
            width = max(self.root.winfo_width(), 1360)
        if height <= 1:
            height = max(self.root.winfo_height() - self.taskbar.winfo_height() - self.top_strip.winfo_height(), 820)
        return width, height

    def _desktop_origin(self) -> tuple[int, int]:
        return self.desktop.winfo_rootx(), self.desktop.winfo_rooty()

    def _set_window_rect(self, window: DesktopWindowState, left: int, top: int, width: int, height: int) -> None:
        origin_x, origin_y = self._desktop_origin()
        center_x = left + (width // 2)
        center_y = top + (height // 2)
        window.position = (origin_x + center_x, origin_y + center_y)
        window.normal_position = window.position
        window.size = (width, height)
        window.normal_size = window.size
        window.maximized = False
        window.minimized = False
        window.toplevel.deiconify()
        self._apply_window_geometry(window)

    def _apply_snap_layout(self, window: DesktopWindowState, layout: str) -> None:
        desktop_width, desktop_height = self._desktop_bounds()
        margin = 14
        full_width = desktop_width - 2 * margin
        full_height = desktop_height - 2 * margin
        half_width = (full_width - 6) // 2
        half_height = (full_height - 6) // 2
        if layout == "maximize":
            origin_x, origin_y = self._desktop_origin()
            window.maximized = True
            window.minimized = False
            window.normal_position = window.position
            window.normal_size = window.size
            window.position = (origin_x + desktop_width // 2, origin_y + desktop_height // 2)
            window.size = (desktop_width - 150, desktop_height - 86)
            window.toplevel.deiconify()
            self._apply_window_geometry(window)
            return
        layouts = {
            "left_half": (margin, margin, half_width, full_height),
            "right_half": (margin + half_width + 6, margin, half_width, full_height),
            "top_left": (margin, margin, half_width, half_height),
            "top_right": (margin + half_width + 6, margin, half_width, half_height),
            "bottom_left": (margin, margin + half_height + 6, half_width, half_height),
            "bottom_right": (margin + half_width + 6, margin + half_height + 6, half_width, half_height),
        }
        if layout in layouts:
            self._set_window_rect(window, *layouts[layout])

    def _snap_layout_for_position(self, x_root: int, y_root: int) -> str | None:
        desktop_width, desktop_height = self._desktop_bounds()
        left_zone = 32
        top_zone = 36
        right_zone = desktop_width - 32
        bottom_zone = desktop_height - 32
        if y_root <= top_zone and x_root <= desktop_width * 0.33:
            return "top_left"
        if y_root <= top_zone and x_root >= desktop_width * 0.67:
            return "top_right"
        if y_root <= top_zone:
            return "maximize"
        if x_root <= left_zone and y_root >= desktop_height * 0.67:
            return "bottom_left"
        if x_root <= left_zone:
            return "left_half"
        if x_root >= right_zone and y_root >= desktop_height * 0.67:
            return "bottom_right"
        if x_root >= right_zone:
            return "right_half"
        if y_root >= bottom_zone and x_root <= desktop_width * 0.5:
            return "bottom_left"
        if y_root >= bottom_zone and x_root > desktop_width * 0.5:
            return "bottom_right"
        return None

    def tile_open_windows(self) -> None:
        windows = [window for window in self.open_windows.values() if not window.minimized]
        if not windows:
            return
        desktop_width, desktop_height = self._desktop_bounds()
        margin = 18
        cols = 2 if len(windows) > 1 else 1
        rows = (len(windows) + cols - 1) // cols
        slot_width = max(420, (desktop_width - margin * 2 - (cols - 1) * 8) // cols)
        slot_height = max(320, (desktop_height - margin * 2 - (rows - 1) * 8) // rows)
        max_slot_width = max(420, desktop_width - margin * 2)
        max_slot_height = max(320, desktop_height - margin * 2)
        slot_width = min(slot_width, max_slot_width)
        slot_height = min(slot_height, max_slot_height)
        for index, window in enumerate(windows):
            row = index // cols
            col = index % cols
            left = margin + col * (slot_width + 8)
            top = margin + row * (slot_height + 8)
            self._set_window_rect(window, left, top, slot_width, slot_height)
        if self.active_app in self.open_windows:
            self._focus_window(self.active_app)
        self.refresh()

    def cascade_open_windows(self) -> None:
        windows = [window for window in self.open_windows.values() if not window.minimized]
        if not windows:
            return
        desktop_width, desktop_height = self._desktop_bounds()
        width = min(920, desktop_width - 100)
        height = min(640, desktop_height - 100)
        for index, window in enumerate(windows):
            left = 120 + index * 34
            top = 82 + index * 28
            self._set_window_rect(window, left, top, width, height)
        if self.active_app in self.open_windows:
            self._focus_window(self.active_app)
        self.refresh()

    def _attach_focus_bindings(self, widget: tk.Widget, app_id: str) -> None:
        widget._desktop_focus_target = app_id
        for child in widget.winfo_children():
            self._attach_focus_bindings(child, app_id)

    def _set_active_scroll_canvas(self, canvas: tk.Canvas | None) -> None:
        self.active_scroll_canvas = canvas

    def _on_global_mousewheel(self, event) -> None:
        canvas = None
        widget = getattr(event, "widget", None)
        while widget is not None:
            canvas = getattr(widget, "_scroll_canvas_target", None)
            if canvas is not None:
                break
            widget = getattr(widget, "master", None)
        if canvas is None:
            canvas = self.active_scroll_canvas
        if canvas is None:
            return
        if getattr(event, "delta", 0):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif getattr(event, "num", None) == 4:
            canvas.yview_scroll(-1, "units")
        elif getattr(event, "num", None) == 5:
            canvas.yview_scroll(1, "units")

    def minimize_window(self, app_id: str | None = None) -> None:
        target = app_id or self.active_app
        if not target or target not in self.open_windows:
            return
        window = self.open_windows[target]
        window.minimized = True
        window.toplevel.withdraw()
        window.task_button.configure(bg="#2e69db")
        if self.active_app == target:
            remaining = [key for key, value in self.open_windows.items() if not value.minimized and key != target]
            self.active_app = remaining[-1] if remaining else ""
            if self.active_app:
                self._focus_window(self.active_app)

    def toggle_task_window(self, app_id: str) -> None:
        if app_id not in self.open_windows:
            return
        window = self.open_windows[app_id]
        if window.minimized:
            window.minimized = False
            window.toplevel.deiconify()
            self._focus_window(app_id)
            self.refresh()
            return
        if self.active_app == app_id:
            self.minimize_window(app_id)
        else:
            self._focus_window(app_id)
            self.refresh()

    def toggle_maximize_window(self, app_id: str | None = None) -> None:
        target = app_id or self.active_app
        if not target or target not in self.open_windows:
            return
        window = self.open_windows[target]
        desktop_width = max(self.desktop.winfo_width(), self.root.winfo_width(), 1360)
        desktop_height = max(self.desktop.winfo_height(), self.root.winfo_height() - self.taskbar.winfo_height() - self.top_strip.winfo_height(), 820)
        if window.maximized:
            window.maximized = False
            window.position = window.normal_position
            window.size = window.normal_size
        else:
            origin_x, origin_y = self._desktop_origin()
            window.maximized = True
            window.minimized = False
            window.normal_position = window.position
            window.normal_size = window.size
            window.position = (origin_x + desktop_width // 2, origin_y + desktop_height // 2)
            window.size = (desktop_width - 150, desktop_height - 86)
        window.toplevel.deiconify()
        self._apply_window_geometry(window)
        self._focus_window(target)
        self.refresh()

    def _start_drag(self, app_id: str, event) -> None:
        if app_id not in self.open_windows:
            return
        window = self.open_windows[app_id]
        if window.maximized:
            return
        self._focus_window(app_id)
        self.drag_origin = (event.x_root, event.y_root)
        self.window_origin = window.position
        self.dragging_app = app_id

    def _on_drag(self, event) -> None:
        if self.drag_origin is None or self.window_origin is None or self.dragging_app is None:
            return
        window = self.open_windows[self.dragging_app]
        if window.maximized:
            return
        delta_x = event.x_root - self.drag_origin[0]
        delta_y = event.y_root - self.drag_origin[1]
        width, height = self._desktop_bounds()
        origin_x, origin_y = self._desktop_origin()
        half_w = window.size[0] // 2
        half_h = window.size[1] // 2
        x = min(max(self.window_origin[0] + delta_x, origin_x + half_w + 12), origin_x + width - half_w - 12)
        y = min(max(self.window_origin[1] + delta_y, origin_y + half_h + 12), origin_y + height - half_h - 12)
        window.position = (x, y)
        window.normal_position = window.position
        self._apply_window_geometry(window)

    def _end_drag(self, event) -> None:
        if self.dragging_app is not None and event is not None:
            window = self.open_windows[self.dragging_app]
            origin_x, origin_y = self._desktop_origin()
            snap_layout = self._snap_layout_for_position(event.x_root - origin_x, event.y_root - origin_y)
            if snap_layout is not None:
                self._apply_snap_layout(window, snap_layout)
                self.refresh()
        self.drag_origin = None
        self.window_origin = None
        self.dragging_app = None

    def _start_resize(self, app_id: str, event, direction: str = "se") -> None:
        if app_id not in self.open_windows:
            return
        window = self.open_windows[app_id]
        if window.maximized:
            return
        self._focus_window(app_id)
        self.resize_origin = (event.x_root, event.y_root)
        self.resize_size_origin = window.size
        self.resize_position_origin = window.position
        self.resize_direction = direction
        self.resizing_app = app_id

    def _on_resize(self, event) -> None:
        if (
            self.resizing_app is None
            or self.resize_origin is None
            or self.resize_size_origin is None
            or self.resize_position_origin is None
            or self.resize_direction is None
        ):
            return
        window = self.open_windows[self.resizing_app]
        delta_x = event.x_root - self.resize_origin[0]
        delta_y = event.y_root - self.resize_origin[1]
        desktop_width, desktop_height = self._desktop_bounds()
        origin_x, origin_y = self._desktop_origin()
        min_width = 360
        min_height = 240
        max_left = origin_x + 8
        max_top = origin_y + 8
        max_right = origin_x + desktop_width - 8
        max_bottom = origin_y + desktop_height - 8

        start_width, start_height = self.resize_size_origin
        start_center_x, start_center_y = self.resize_position_origin
        left = start_center_x - (start_width // 2)
        top = start_center_y - (start_height // 2)
        right = left + start_width
        bottom = top + start_height

        if "e" in self.resize_direction:
            right = min(max(right + delta_x, left + min_width), max_right)
        if "s" in self.resize_direction:
            bottom = min(max(bottom + delta_y, top + min_height), max_bottom)
        if "w" in self.resize_direction:
            left = max(min(left + delta_x, right - min_width), max_left)
        if "n" in self.resize_direction:
            top = max(min(top + delta_y, bottom - min_height), max_top)

        new_width = min(max(right - left, min_width), max_right - max_left)
        new_height = min(max(bottom - top, min_height), max_bottom - max_top)
        center_x = left + (new_width // 2)
        center_y = top + (new_height // 2)

        window.position = (center_x, center_y)
        window.normal_position = window.position
        window.size = (new_width, new_height)
        window.normal_size = window.size
        self._apply_window_geometry(window)

    def _end_resize(self, _event) -> None:
        resized_app = self.resizing_app
        self.resize_origin = None
        self.resize_size_origin = None
        self.resize_position_origin = None
        self.resize_direction = None
        self.resizing_app = None
        if resized_app and resized_app in self.open_windows:
            self.refresh()

    def _build_scroll_area(self, parent: tk.Frame, *, bg: str = "#ffffff") -> tk.Frame:
        outer = tk.Frame(parent, bg=bg)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg=bg)
        window_id = canvas.create_window(0, 0, window=content, anchor="nw")

        def sync_region(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(window_id, width=max(canvas.winfo_width(), 1))

        outer._scroll_canvas_target = canvas
        canvas._scroll_canvas_target = canvas
        content._scroll_canvas_target = canvas
        content.bind("<Configure>", sync_region)
        canvas.bind("<Configure>", sync_region)
        for widget in (outer, canvas, content):
            widget.bind("<Enter>", lambda _event, current=canvas: self._set_active_scroll_canvas(current), add="+")
            widget.bind("<Leave>", lambda _event, current=canvas: self._set_active_scroll_canvas(None) if self.active_scroll_canvas == current else None, add="+")
        return content

    def recent_save_files(self) -> list[Path]:
        return sorted(self.session.paths.saves_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:8]

    def _build_window_shell(self, app_id: str, title: str) -> tuple[tk.Frame, tk.Frame]:
        window = self.open_windows[app_id]
        window.title = title
        for child in window.host.winfo_children():
            child.destroy()
        window.toplevel.deiconify()
        shell = tk.Frame(
            window.host,
            bg="#0a2f82",
            bd=0,
            highlightthickness=1,
            highlightbackground="#08307b",
            highlightcolor="#08307b",
        )
        shell.pack(fill="both", expand=True)
        frame = tk.Frame(shell, bg="#ece9d8", bd=0, highlightthickness=0)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        title_bar = tk.Frame(frame, bg="#0c57db", height=30, cursor="fleur", bd=0, highlightthickness=0)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        tk.Frame(title_bar, bg="#7fb4ff", height=1).pack(fill="x", side="top")
        tk.Frame(title_bar, bg="#1d64e2", height=1).pack(fill="x", side="bottom")
        title_bar.bind("<ButtonPress-1>", lambda event, target=app_id: self._start_drag(target, event))
        title_bar.bind("<B1-Motion>", self._on_drag)
        title_bar.bind("<ButtonRelease-1>", self._end_drag)
        title_content = tk.Frame(title_bar, bg="#0c57db", bd=0, highlightthickness=0)
        title_content.pack(fill="both", expand=True)
        title_label = tk.Label(
            title_content,
            text=title,
            bg="#0c57db",
            fg="white",
            anchor="w",
            padx=10,
            font=("Tahoma", 11, "bold"),
            cursor="fleur",
            bd=0,
            highlightthickness=0,
        )
        title_label.pack(side="left", fill="y")
        title_label.bind("<ButtonPress-1>", lambda event, target=app_id: self._start_drag(target, event))
        title_label.bind("<B1-Motion>", self._on_drag)
        title_label.bind("<ButtonRelease-1>", self._end_drag)

        button_strip = tk.Frame(title_content, bg="#0c57db", bd=0, highlightthickness=0)
        button_strip.pack(side="right", padx=6, pady=4)
        for caption, bg, active_bg, width, command in (
            ("_", "#7ea7ef", "#99b9f4", 2, lambda target=app_id: self.minimize_window(target)),
            ("\u25a1" if not window.maximized else "\u2752", "#7ea7ef", "#99b9f4", 2, lambda target=app_id: self.toggle_maximize_window(target)),
            ("\u2715", "#d86f32", "#e48a56", 2, lambda target=app_id: self.close_window(target)),
        ):
            tk.Button(
                button_strip,
                text=caption,
                command=command,
                bg=bg,
                fg="white",
                activebackground=active_bg,
                relief="flat",
                bd=1,
                width=width,
                font=("Tahoma", 8, "bold"),
                highlightthickness=0,
                padx=1,
                pady=0,
            ).pack(side="left", padx=1)

        toolbar = tk.Frame(frame, bg="#ece9d8", height=24, bd=0, highlightthickness=0)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)
        for caption in ("File", "Edit", "View", "Favorites", "Tools", "Help"):
            tk.Label(toolbar, text=caption, bg="#ece9d8", fg="#111827", padx=8, font=("Tahoma", 8)).pack(side="left", pady=3)
        tk.Frame(frame, bg="#b9b29a", height=1).pack(fill="x")

        inner = tk.Frame(frame, bg="#f5f0da")
        inner.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        def add_resize_handle(parent: tk.Widget, direction: str, cursor: str, *, bg: str, **place_kwargs) -> None:
            handle = tk.Frame(
                parent,
                bg=bg,
                cursor=cursor,
                highlightthickness=0,
                bd=0,
                relief="flat",
            )
            handle.place(**place_kwargs)
            handle.bind("<ButtonPress-1>", lambda event, target=app_id, edge=direction: self._start_resize(target, event, edge))
            handle.bind("<B1-Motion>", self._on_resize)
            handle.bind("<ButtonRelease-1>", self._end_resize)
            handle.lift()

        add_resize_handle(frame, "n", "sb_v_double_arrow", bg="#0c57db", relx=0.04, rely=0.0, relwidth=0.92, height=4)
        add_resize_handle(frame, "nw", "size_nw_se", bg="#0c57db", relx=0.0, rely=0.0, width=8, height=8)
        add_resize_handle(frame, "ne", "size_ne_sw", bg="#0c57db", relx=1.0, x=-8, rely=0.0, width=8, height=8)
        add_resize_handle(frame, "s", "sb_v_double_arrow", bg="#ece9d8", relx=0.03, rely=1.0, y=-4, relwidth=0.94, height=4)
        add_resize_handle(frame, "w", "sb_h_double_arrow", bg="#ece9d8", relx=0.0, rely=0.03, width=4, relheight=0.94)
        add_resize_handle(frame, "e", "sb_h_double_arrow", bg="#ece9d8", relx=1.0, x=-4, rely=0.03, width=4, relheight=0.94)
        add_resize_handle(frame, "sw", "size_ne_sw", bg="#ece9d8", relx=0.0, rely=1.0, y=-8, width=8, height=8)
        add_resize_handle(frame, "se", "size_nw_se", bg="#ece9d8", relx=1.0, x=-8, rely=1.0, y=-8, width=8, height=8)
        return frame, inner

    def close_window(self, app_id: str | None = None) -> None:
        target = app_id or self.active_app
        if not target or target not in self.open_windows:
            return
        window = self.open_windows.pop(target)
        window.task_button.destroy()
        window.toplevel.destroy()
        if self.active_app == target:
            remaining = [key for key, value in self.open_windows.items() if not value.minimized]
            self.active_app = remaining[-1] if remaining else ""
            if self.active_app:
                self._focus_window(self.active_app)

    def build_mail_items(self) -> list[DesktopMail]:
        state = self.controller.state
        mails: list[DesktopMail] = [
            DesktopMail(
                sender="Desktop Assistant",
                subject=f"Month {state.current_month} brief",
                received=f"Y{state.current_year} M{((state.current_month - 1) % 12) + 1:02d}",
                body="\n".join(state.recent_summary[-6:] or state.build_month_outlook() if hasattr(state, "build_month_outlook") else state.recent_summary),
                unread=bool(state.recent_summary),
            )
        ]
        if state.month_driver_notes:
            mails.append(
                DesktopMail(
                    sender="System Outlook",
                    subject="Why this month changed",
                    received=f"Y{state.current_year} M{((state.current_month - 1) % 12) + 1:02d}",
                    body="\n".join(f"- {line}" for line in state.month_driver_notes),
                    unread=True,
                )
            )
        for milestone in reversed(state.annual_milestones[-3:]):
            mails.append(
                DesktopMail(
                    sender="Life Archive",
                    subject=f"Year {milestone.year} summary",
                    received=f"Age {milestone.age}",
                    body="\n".join(milestone.summary_lines),
                    unread=False,
                )
            )
        for index, warning in enumerate(self.controller.build_crisis_warnings()[:3], start=1):
            mails.append(
                DesktopMail(
                    sender="Alert Monitor",
                    subject=f"Crisis watch {index}",
                    received=f"Month {state.current_month}",
                    body=warning,
                    unread=True,
                )
            )
        if not state.log_messages:
            mails.append(
                DesktopMail(
                    sender="Welcome Center",
                    subject="Welcome to Desktop Mode",
                    received="Today",
                    body="Use Mail, Bank Account, Internet, and Profile to manage the month. Press Next turn to advance the simulation by one month.",
                    unread=True,
                )
            )
        else:
            for entry in reversed(state.log_messages[-4:]):
                mails.append(
                    DesktopMail(
                        sender="Event Feed",
                        subject=entry[:48],
                        received=f"Month {state.current_month}",
                        body=entry,
                        unread=False,
                    )
                )
        return mails

    def _mail_toolbar_actions(self) -> list[DesktopAction]:
        return [
            DesktopAction("Mark Read", "mail", self.mark_mail_read),
            DesktopAction("Mark All As Read", "mail", self.mark_mail_read),
            DesktopAction("Open Save Center", "save", lambda: self.open_app("saves")),
            DesktopAction("Open Bank", "bank", lambda: self.open_app("bank")),
            DesktopAction("Open Profile", "profile", lambda: self.open_app("profile")),
            DesktopAction("Open Internet", "internet", lambda: self.open_app("browser")),
        ]

    def _bank_toolbar_actions(self) -> list[DesktopAction]:
        return [
            DesktopAction("Change Budget Stance", "bank", self.choose_budget),
            DesktopAction("Change Wealth Strategy", "bank", self.choose_wealth),
            DesktopAction("Change Monthly Focus", "bank", self.choose_focus),
            DesktopAction("Open Save Center", "save", lambda: self.open_app("saves")),
            DesktopAction("Open Net Worth", "profile", lambda: (self.open_app("profile"), self.set_profile_tab("net_worth"))),
        ]

    def _save_toolbar_actions(self) -> list[DesktopAction]:
        return [
            DesktopAction("Save As...", "save", self.save_snapshot),
            DesktopAction("Load...", "save", self.load_snapshot_dialog),
            DesktopAction("Quick Save", "save", self.quick_save_snapshot),
        ]

    def render_mail(self, app_id: str) -> None:
        _, inner = self._build_window_shell(app_id, "Inbox - Outlook Express")
        window = self.open_windows[app_id]
        compact = window.size[0] < 860
        very_compact = window.size[0] < 620
        mails = self.build_mail_items()
        self.mail_index = min(self.mail_index, max(0, len(mails) - 1))
        unread_count = sum(1 for mail in mails if mail.unread)

        self._build_app_banner(
            inner,
            icon_name="mail",
            title="Inbox Overview",
            subtitle=f"{unread_count} unread messages. Use Mail to follow month drivers, event fallout, and yearly life summaries.",
        )

        self._build_action_toolbar(
            inner,
            app_id=app_id,
            items=self._mail_toolbar_actions(),
            compact_threshold=780,
            compact_label="\u2630 Mail Menu",
        )

        mail_stats = tk.Frame(inner, bg="#f5f0da")
        mail_stats.pack(fill="x", pady=(0, 8))
        for label, value, color in (
            ("Unread", unread_count, "#93c5fd"),
            ("Alerts", sum(1 for mail in mails if self._mail_category(mail)[0] == "Alert"), "#fca5a5"),
            ("Archives", sum(1 for mail in mails if self._mail_category(mail)[0] == "Archive"), "#c4b5fd"),
        ):
            card = tk.Frame(mail_stats, bg="#ffffff", bd=1, relief="solid")
            card.pack(side="top" if very_compact else "left", fill="x" if very_compact else "none", padx=(0, 8), pady=(0, 6) if very_compact else 0)
            tk.Label(card, text=label, bg=color, anchor="w", padx=10, pady=4, font=("Tahoma", 8, "bold")).pack(fill="x")
            tk.Label(card, text=str(value), bg="#ffffff", anchor="w", padx=10, pady=8, font=("Tahoma", 11, "bold")).pack(fill="x")

        left = tk.Frame(inner, bg="#efead2", width=190, bd=1, relief="solid")
        left.pack(side="top" if compact else "left", fill="x" if compact else "y", pady=(0, 6) if compact else 0)
        left.pack_propagate(compact)
        tk.Label(left, text="Outlook Express", bg="#efead2", anchor="w", padx=8, pady=8, font=("Tahoma", 9)).pack(fill="x")
        folders = tk.Frame(left, bg="#ffffff", bd=1, relief="sunken")
        folders.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        for label in (f"Inbox [{unread_count}]", "Outbox", "Sent Items"):
            tk.Label(folders, text=f"\u251c {label}", bg="#ffffff", anchor="w", padx=10, pady=5, font=("Tahoma", 9, "bold" if label.startswith("Inbox") else "normal")).pack(fill="x")
        tk.Label(left, text="Archive", bg="#efead2", anchor="w", padx=8, pady=4, font=("Tahoma", 9, "bold")).pack(fill="x")
        archive = tk.Frame(left, bg="#ffffff", bd=1, relief="sunken")
        archive.pack(fill="x", padx=8, pady=(0, 8))
        for milestone in reversed(self.controller.state.annual_milestones[-4:]):
            tk.Label(archive, text=f"Year {milestone.year}  Age {milestone.age}", bg="#ffffff", anchor="w", padx=10, pady=4, font=("Tahoma", 8)).pack(fill="x")
        if not self.controller.state.annual_milestones:
            tk.Label(archive, text="No yearly archive yet", bg="#ffffff", anchor="w", padx=10, pady=6, font=("Tahoma", 8)).pack(fill="x")
        tk.Button(left, text="Mark all as read", command=self.mark_mail_read, bg="#f4f4f4", relief="raised", bd=1).pack(padx=8, pady=(0, 8), fill="x")
        tk.Button(left, text="Open Save Center", command=lambda: self.open_app("saves"), bg="#f4f4f4", relief="raised", bd=1).pack(padx=8, pady=(0, 8), fill="x")

        right = tk.Frame(inner, bg="#f5f0da")
        right.pack(side="top" if compact else "left", fill="both", expand=True, padx=(0, 0) if compact else (3, 0))
        column_widths = (8, 14, 24, 12) if compact else (10, 20, 36, 14)

        header = tk.Frame(right, bg="#efe8c8", bd=1, relief="solid")
        header.pack(fill="x")
        for text, width in (("Type", column_widths[0]), ("From", column_widths[1]), ("Subject", column_widths[2]), ("Received", column_widths[3])):
            tk.Label(header, text=text, width=width, bg="#efe8c8", anchor="w", padx=6, font=("Tahoma", 9, "bold")).pack(side="left")

        list_holder = tk.Frame(right, bg="#ffffff", bd=1, relief="sunken")
        list_holder.pack(fill="x")
        list_content = self._build_scroll_area(list_holder, bg="#ffffff")
        for idx, mail in enumerate(mails):
            bg = "#ffffff" if idx != self.mail_index else "#d8e8ff"
            row = tk.Frame(list_content, bg=bg)
            row.pack(fill="x")
            category, color = self._mail_category(mail)
            tk.Button(
                row,
                text=category,
                width=column_widths[0],
                anchor="w",
                relief="flat",
                bg=color if idx != self.mail_index else "#bcd7ff",
                activebackground="#cfe0ff",
                command=lambda selected=idx: self.select_mail(selected),
                padx=6,
                font=("Tahoma", 8, "bold"),
            ).pack(side="left")
            for text, width in ((mail.sender, column_widths[1]), (mail.subject, column_widths[2]), (mail.received, column_widths[3])):
                tk.Button(
                    row,
                    text=text,
                    width=width,
                    anchor="w",
                    relief="flat",
                    bg=bg,
                    activebackground="#cfe0ff",
                    command=lambda selected=idx: self.select_mail(selected),
                    padx=6,
                    font=("Tahoma", 9, "bold" if mail.unread else "normal"),
                ).pack(side="left")

        selected = mails[self.mail_index]
        meta = tk.Frame(right, bg="#f5f0da", bd=1, relief="solid")
        meta.pack(fill="x", pady=(6, 0))
        category, color = self._mail_category(selected)
        tk.Label(meta, text=f"Type:      {category}", bg=color, anchor="w", padx=8, pady=2, font=("Tahoma", 9, "bold")).pack(fill="x")
        for line in (
            f"From:      {selected.sender}",
            f"Date:      {selected.received}",
            f"To:        {self.controller.state.player.name}",
            f"Subject:   {selected.subject}",
        ):
            tk.Label(meta, text=line, bg="#f5f0da", anchor="w", padx=8, pady=2, font=("Tahoma", 9)).pack(fill="x")

        lower = tk.Frame(right, bg="#f5f0da")
        lower.pack(fill="both", expand=True, pady=(6, 0))
        body_panel = tk.Frame(lower, bg="#ffffff", bd=1, relief="sunken")
        body_panel.pack(side="top" if compact else "left", fill="both", expand=True, padx=(0, 0) if compact else (0, 8), pady=(0, 6) if compact else 0)
        tk.Label(body_panel, text="Message", bg="#dfe8fb", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
        body = tk.Text(body_panel, bg="#ffffff", fg="#222222", wrap="word", relief="flat", bd=0, font=("Tahoma", 10))
        body.pack(fill="both", expand=True, padx=6, pady=6)
        body.insert("1.0", selected.body)
        body.configure(state="disabled")

        side = tk.Frame(lower, bg="#ffffff", bd=1, relief="solid", width=220)
        side.pack(side="top" if compact else "left", fill="both")
        side.pack_propagate(False)
        tk.Label(side, text="Why This Matters", bg="#ffe5b4", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
        for line in self._mail_storyline(selected):
            tk.Label(side, text=f"- {line}", bg="#ffffff", anchor="w", justify="left", wraplength=190, padx=8, pady=4, font=("Tahoma", 9)).pack(fill="x")
        tk.Label(side, text="Quick Actions", bg="#dfe8fb", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(10, 0))
        for label, callback in (
            ("Open Bank", lambda: self.open_app("bank")),
            ("Open Profile", lambda: self.open_app("profile")),
            ("Open Internet", lambda: self.open_app("browser")),
        ):
            tk.Button(side, text=label, command=callback, bg="#f4f4f4", relief="raised", bd=1, padx=8, pady=6).pack(fill="x", padx=8, pady=4)

    def mark_mail_read(self) -> None:
        self.mail_index = 0
        self.refresh()

    def select_mail(self, index: int) -> None:
        self.mail_index = index
        self.refresh()

    def render_bank(self, app_id: str) -> None:
        _, inner = self._build_window_shell(app_id, "Young Saver Bank PLC")
        state = self.controller.state
        player = state.player
        window = self.open_windows[app_id]
        wrap = max(260, window.size[0] - 420)
        compact = window.size[0] < 900
        very_compact = window.size[0] < 660

        self._build_app_banner(
            inner,
            icon_name="bank",
            title="Financial Dashboard",
            subtitle="Track cash, debt, investing, and your monthly financial outlook without leaving the desktop.",
        )
        self._build_action_toolbar(
            inner,
            app_id=app_id,
            items=self._bank_toolbar_actions(),
            compact_threshold=820,
            compact_label="\u2630 Bank Menu",
        )

        badges = tk.Frame(inner, bg="#f5f0da")
        badges.pack(fill="x", pady=(0, 8))
        for label, value, color in (
            ("Budget", player.budget_stance_id.replace("_", " "), "#dbeafe"),
            ("Wealth Plan", player.wealth_strategy_id.replace("_", " "), "#dcfce7"),
            ("Monthly Focus", player.selected_focus_action_id.replace("_", " "), "#fef3c7"),
        ):
            pill = tk.Frame(badges, bg=color, bd=1, relief="solid")
            pill.pack(side="top" if very_compact else "left", fill="x" if very_compact else "none", padx=(0, 8), pady=(0, 6) if very_compact else 0)
            tk.Label(pill, text=f"{label}: {value}", bg=color, fg="#1f2937", padx=10, pady=6, font=("Tahoma", 9, "bold")).pack()

        top = tk.Frame(inner, bg="#f5f0da")
        top.pack(fill="x")
        summary = tk.Frame(top, bg="#ffffff", bd=1, relief="solid")
        summary.pack(side="top" if compact else "left", fill="both", expand=True, padx=(0, 0) if compact else (0, 8), pady=(0, 8) if compact else 0)
        summary.grid_columnconfigure(0, weight=1)
        summary.grid_columnconfigure(1, weight=1)
        rows = [
            ("Current Cash", f"${player.cash}"),
            ("Savings", f"${player.savings}"),
            ("High-Interest", f"${player.high_interest_savings}"),
            ("Index Fund", f"${player.index_fund}"),
            ("Growth Fund", f"${player.aggressive_growth_fund}"),
            ("Debt", f"${player.debt}"),
        ]
        for idx, (label, value) in enumerate(rows):
            card = tk.Frame(summary, bg="#ffffff")
            card.grid(row=idx // 2, column=idx % 2, sticky="ew", padx=10, pady=6)
            tk.Label(card, text=label, bg="#ffffff", anchor="w", fg="#4b5563", font=("Tahoma", 8, "bold")).pack(fill="x")
            tk.Label(card, text=value, bg="#ffffff", anchor="w", font=("Tahoma", 11, "bold")).pack(fill="x")

        mix = tk.Frame(summary, bg="#ffffff")
        mix.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(4, 10))
        self._build_progress_bar(mix, label="Cash Buffer", value=min(player.cash // 25, 100), color="#4ade80")
        self._build_progress_bar(mix, label="Debt Pressure", value=min(player.debt // 20, 100), color="#f97316")
        self._build_progress_bar(mix, label="Investing Base", value=min((player.index_fund + player.aggressive_growth_fund) // 20, 100), color="#60a5fa")

        actions = tk.Frame(top, bg="#efead2", bd=1, relief="solid", width=210)
        actions.pack(side="top" if compact else "left", fill="x" if compact else "y")
        actions.pack_propagate(compact)
        tk.Label(actions, text="Money tools", bg="#efead2", font=("Tahoma", 10, "bold"), pady=8).pack(fill="x")
        for label, callback in (
            ("Change Budget Stance", self.choose_budget),
            ("Change Wealth Strategy", self.choose_wealth),
            ("Change Monthly Focus", self.choose_focus),
            ("Open Save Center", lambda: self.open_app("saves")),
        ):
            tk.Button(actions, text=label, command=callback, bg="#f7f7f7", relief="raised", bd=1, padx=6, pady=6).pack(fill="x", padx=10, pady=4)

        bottom = tk.Frame(inner, bg="#f5f0da")
        bottom.pack(fill="both", expand=True, pady=(10, 0))
        notes = tk.Frame(bottom, bg="#ffffff", bd=1, relief="solid")
        notes.pack(side="top" if compact else "left", fill="both", expand=True, padx=(0, 0) if compact else (0, 8), pady=(0, 8) if compact else 0)
        tk.Label(notes, text="Financial Outlook", bg="#dfe8fb", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
        notes_content = self._build_scroll_area(notes, bg="#ffffff")
        for line in self.controller.build_month_outlook():
            tk.Label(notes_content, text=f"- {line}", bg="#ffffff", anchor="w", justify="left", wraplength=wrap, padx=10, pady=3, font=("Tahoma", 9)).pack(fill="x")

        status = tk.Frame(bottom, bg="#ffffff", bd=1, relief="solid", width=210)
        status.pack(side="top" if compact else "left", fill="both")
        status.pack_propagate(compact)
        tk.Label(status, text="Risk Watch", bg="#ffe5b4", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
        warnings = self.controller.build_crisis_warnings() or ["Stable enough for now."]
        for line in warnings:
            tk.Label(status, text=f"- {line}", bg="#ffffff", anchor="w", justify="left", wraplength=180, padx=8, pady=4, font=("Tahoma", 9)).pack(fill="x")
        tk.Label(status, text="Cashflow This Month", bg="#dfe8fb", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(10, 0))
        for label, value in (
            ("Income", player.monthly_income),
            ("Expenses", player.monthly_expenses),
            ("Surplus", player.monthly_surplus),
        ):
            tk.Label(status, text=f"{label}: ${value}", bg="#ffffff", anchor="w", padx=8, pady=4, font=("Tahoma", 9)).pack(fill="x")

    def render_browser(self, app_id: str) -> None:
        _, inner = self._build_window_shell(app_id, "EIPS Explorer")
        window = self.open_windows[app_id]
        compact = window.size[0] < 760
        self._build_app_banner(
            inner,
            icon_name="internet",
            title="EIPS Explorer",
            subtitle="Browse career boards, training options, housing, and transport like separate services inside your desktop world.",
        )
        site_name, site_blurb = self._browser_branding()
        chrome = tk.Frame(inner, bg="#ece9d8", bd=1, relief="solid")
        chrome.pack(fill="x", pady=(0, 8))
        address = tk.Frame(chrome, bg="#ece9d8")
        address.pack(fill="x", padx=6, pady=6)
        if compact:
            menu_button = tk.Menubutton(address, text="\u2630 Browser Menu", bg="#f4f4f4", relief="raised", bd=1, padx=10, pady=4, font=("Tahoma", 9, "bold"))
            popup = tk.Menu(menu_button, tearoff=False)
            popup.add_command(label="Refresh", command=self.refresh)
            popup.add_separator()
            popup.add_command(label="Open Jobs", command=lambda: self.set_browser_page("jobs"))
            popup.add_command(label="Open Education", command=lambda: self.set_browser_page("education"))
            popup.add_command(label="Open Housing", command=lambda: self.set_browser_page("housing"))
            popup.add_command(label="Open Transport", command=lambda: self.set_browser_page("transport"))
            menu_button.configure(menu=popup)
            menu_button.pack(side="left", padx=(0, 8))
        else:
            self._toolbar_button(address, icon_name="internet", label="Refresh", command=self.refresh)
        tk.Label(address, text="Address", bg="#ece9d8", font=("Tahoma", 8, "bold")).pack(side="left", padx=(8, 4))
        address_box = tk.Entry(address, bd=1, relief="sunken")
        address_box.pack(side="left", fill="x", expand=True)
        address_box.insert(0, f"https://{site_name.lower()}.local/{self.browser_page}")
        address_box.configure(state="readonly")

        nav = tk.Frame(inner, bg="#d7e4ff", bd=1, relief="solid")
        nav.pack(fill="x")
        self._build_responsive_tabs(
            nav,
            app_id=app_id,
            items=[("Jobs", "jobs"), ("Education", "education"), ("Housing", "housing"), ("Transport", "transport")],
            current_id=self.browser_page,
            on_select=self.set_browser_page,
            compact_threshold=700,
        )

        body = tk.Frame(inner, bg="#ffffff", bd=1, relief="sunken")
        body.pack(fill="both", expand=True, pady=(8, 0))
        tk.Label(body, text=self._browser_heading(), bg="#f8f2d4", anchor="w", padx=10, pady=8, font=("Tahoma", 11, "bold")).pack(fill="x")
        content = self._build_scroll_area(body, bg="#ffffff")
        content.configure(padx=10, pady=10)
        hero = tk.Frame(content, bg="#eef5ff", bd=1, relief="solid")
        hero.pack(fill="x", pady=(0, 10))
        tk.Label(hero, text=site_name, bg="#eef5ff", fg="#0f172a", anchor="w", padx=12, pady=8, font=("Tahoma", 11, "bold")).pack(fill="x")
        tk.Label(hero, text=site_blurb, bg="#eef5ff", fg="#334155", anchor="w", justify="left", wraplength=max(320, window.size[0] - 180), padx=12, pady=10, font=("Tahoma", 9)).pack(fill="x")
        self._render_browser_spotlight(content, max(320, window.size[0] - 180))

        if self.browser_page == "jobs":
            self._render_option_buttons(
                content,
                [(name, item_id, description, allowed, reason) for name, item_id, allowed, reason in self.controller.career_entry_statuses() for description in [next(track.description for track in self.controller.bundle.careers if track.id == item_id)]],
                apply_callback=self.apply_career,
                wraplength=max(280, window.size[0] - 280),
                action_label=self._browser_action_label(),
            )
        elif self.browser_page == "education":
            options = [(program.name, program.id, program.description, True, "") for program in self.controller.available_education_programs()]
            self._render_option_buttons(content, options, apply_callback=self.apply_education, wraplength=max(280, window.size[0] - 280), action_label=self._browser_action_label())
        elif self.browser_page == "housing":
            options = [(option.name, option.id, option.description, True, "") for option in self.controller.available_housing()]
            self._render_option_buttons(content, options, apply_callback=self.apply_housing, wraplength=max(280, window.size[0] - 280), action_label=self._browser_action_label())
        else:
            options = [(option.name, option.id, option.description, True, "") for option in self.controller.available_transport()]
            self._render_option_buttons(content, options, apply_callback=self.apply_transport, wraplength=max(280, window.size[0] - 280), action_label=self._browser_action_label())

    def _browser_heading(self) -> str:
        headings = {
            "jobs": "Careers & Job Boards",
            "education": "Colleges, Certificates & Training",
            "housing": "Rentals & Housing",
            "transport": "Transit, Bikes & Vehicles",
        }
        return headings[self.browser_page]

    def _profile_tab_button(self, parent: tk.Frame, label: str, tab_id: str) -> None:
        tk.Button(
            parent,
            text=label,
            command=lambda selected=tab_id: self.set_profile_tab(selected),
            bg="#fff7cf" if self.profile_tab == tab_id else "#fefefe",
            relief="raised",
            bd=1,
            padx=10,
            pady=4,
        ).pack(side="left", padx=4, pady=4)

    def _career_name(self) -> str:
        return next(track.name for track in self.controller.bundle.careers if track.id == self.controller.state.player.career.track_id)

    def _career_tier_label(self) -> str:
        player = self.controller.state.player
        track = next(track for track in self.controller.bundle.careers if track.id == player.career.track_id)
        return track.tiers[player.career.tier_index].label

    def _education_name(self) -> str:
        return next(program.name for program in self.controller.bundle.education_programs if program.id == self.controller.state.player.education.program_id)

    def _housing_name(self) -> str:
        return next(item.name for item in self.controller.bundle.housing_options if item.id == self.controller.state.player.housing_id)

    def _transport_name(self) -> str:
        return next(item.name for item in self.controller.bundle.transport_options if item.id == self.controller.state.player.transport_id)

    def set_profile_tab(self, tab_id: str) -> None:
        self.profile_tab = tab_id
        self.refresh()

    def _build_app_banner(self, parent: tk.Frame, *, icon_name: str, title: str, subtitle: str) -> None:
        banner = tk.Frame(parent, bg="#dfe8fb", bd=1, relief="solid")
        banner.pack(fill="x", pady=(0, 8))
        icon = self.icon_images.get(icon_name)
        tk.Label(banner, image=icon, bg="#dfe8fb").pack(side="left", padx=10, pady=8)
        text = tk.Frame(banner, bg="#dfe8fb")
        text.pack(side="left", fill="both", expand=True, pady=8)
        tk.Label(text, text=title, bg="#dfe8fb", fg="#0f172a", anchor="w", font=("Tahoma", 11, "bold")).pack(fill="x")
        tk.Label(text, text=subtitle, bg="#dfe8fb", fg="#334155", anchor="w", justify="left", wraplength=520, font=("Tahoma", 9)).pack(fill="x", pady=(2, 0))

    def _build_action_toolbar(
        self,
        parent: tk.Frame,
        *,
        app_id: str,
        items: list[DesktopAction],
        compact_threshold: int = 940,
        compact_label: str = "\u2630 Menu",
    ) -> tk.Frame:
        toolbar = tk.Frame(parent, bg="#ece9d8", bd=1, relief="solid")
        toolbar.pack(fill="x", pady=(0, 8))
        if self.open_windows[app_id].size[0] < compact_threshold:
            menu_button = tk.Menubutton(toolbar, text=compact_label, bg="#f4f4f4", relief="raised", bd=1, padx=12, pady=4, font=("Tahoma", 9, "bold"))
            popup = tk.Menu(menu_button, tearoff=False)
            for item in items:
                popup.add_command(label=item.label, command=item.callback)
            menu_button.configure(menu=popup)
            menu_button.pack(side="left", padx=6, pady=4)
            tk.Label(toolbar, text="Compact mode keeps tools in this window.", bg="#ece9d8", fg="#4b5563", padx=8, font=("Tahoma", 8)).pack(side="left", pady=4)
            return toolbar
        for item in items:
            self._toolbar_button(toolbar, icon_name=item.icon_name, label=item.label, command=item.callback)
        return toolbar

    def _build_responsive_tabs(
        self,
        parent: tk.Frame,
        *,
        app_id: str,
        items: list[tuple[str, str]],
        current_id: str,
        on_select,
        compact_threshold: int = 860,
    ) -> None:
        if self.open_windows[app_id].size[0] < compact_threshold:
            menu_button = tk.Menubutton(parent, text="\u2630 Sections", bg="#fff7cf", relief="raised", bd=1, padx=10, pady=4, font=("Tahoma", 9, "bold"))
            popup = tk.Menu(menu_button, tearoff=False)
            current_label = next((label for label, item_id in items if item_id == current_id), current_id.title())
            for label, item_id in items:
                popup.add_command(label=label, command=lambda selected=item_id: on_select(selected))
            menu_button.configure(menu=popup)
            menu_button.pack(side="left", padx=4, pady=4)
            tk.Label(parent, text=current_label, bg="#d7e4ff", fg="#1f2937", padx=10, font=("Tahoma", 9, "bold")).pack(side="left", pady=4)
            return
        for label, item_id in items:
            tk.Button(
                parent,
                text=label,
                command=lambda selected=item_id: on_select(selected),
                bg="#fff7cf" if current_id == item_id else "#fefefe",
                relief="raised",
                bd=1,
                padx=10,
                pady=4,
            ).pack(side="left", padx=4, pady=4)

    def _toolbar_button(self, parent: tk.Frame, *, icon_name: str, label: str, command) -> None:
        icon = self.small_icons.get(icon_name)
        tk.Button(
            parent,
            text=f" {label}",
            image=icon,
            compound="left",
            command=command,
            bg="#f4f4f4",
            activebackground="#dfe8fb",
            relief="raised",
            bd=1,
            padx=10,
            pady=4,
            font=("Tahoma", 9),
        ).pack(side="left", padx=4, pady=4)

    def _build_progress_bar(self, parent: tk.Frame, *, label: str, value: int, color: str, max_value: int = 100) -> None:
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg="#ffffff", anchor="w", width=20, font=("Tahoma", 9, "bold")).pack(side="left")
        track = tk.Canvas(row, width=180, height=14, bg="#eef2f7", highlightthickness=1, highlightbackground="#cbd5e1")
        track.pack(side="left", padx=8)
        fill_width = int(max(0, min(value, max_value)) / max_value * 176)
        track.create_rectangle(1, 1, 1 + fill_width, 13, fill=color, outline="")
        tk.Label(row, text=str(value), bg="#ffffff", anchor="e", width=5, font=("Tahoma", 9)).pack(side="left")

    def _mail_category(self, mail: DesktopMail) -> tuple[str, str]:
        sender = mail.sender.lower()
        subject = mail.subject.lower()
        if "alert" in sender or "crisis" in subject:
            return ("Alert", "#fca5a5")
        if "archive" in sender or "summary" in subject:
            return ("Archive", "#c4b5fd")
        if "assistant" in sender or "brief" in subject:
            return ("Brief", "#93c5fd")
        if "event" in sender:
            return ("Event", "#86efac")
        return ("Info", "#fde68a")

    def _mail_storyline(self, mail: DesktopMail) -> list[str]:
        category, _color = self._mail_category(mail)
        if category == "Alert":
            return [
                "This message is warning you about an active risk in the run.",
                "Use Bank, Profile, or Internet before advancing if the warning points to a weak system.",
                "Alerts usually mean your next month can get worse fast if you ignore the signal.",
            ]
        if category == "Archive":
            return [
                "This is part of your long-arc history, not just a one-month notification.",
                "Archive messages are a good way to see whether the decade is actually improving.",
                "Compare these against your current stress, cashflow, and housing stability.",
            ]
        if category == "Brief":
            return [
                "This is your month summary surface.",
                "Read it as the closest thing to a manager's note on how the simulation currently reads your life.",
                "If the brief feels unstable, the right answer is usually in Bank, Internet, or Profile.",
            ]
        if category == "Event":
            return [
                "This is a consequence or flavor event attached to the current run.",
                "Event mail is where the game becomes a story instead of pure numbers.",
                "Use the details here to decide whether to stabilize, push, or pivot.",
            ]
        return [
            "This is a general information message.",
            "Use it as context rather than a direct warning.",
            "If in doubt, compare it to your metrics bar and current outlook.",
        ]

    def _browser_branding(self) -> tuple[str, str]:
        return {
            "jobs": ("CareerWire", "Browse live boards, lane changes, and role filters tied to your actual sim constraints."),
            "education": ("CampusFinder", "Compare programs, credentials, and study tracks that shape the next few years."),
            "housing": ("HomeBoard", "Scan rentals and stability tradeoffs before your housing becomes the story."),
            "transport": ("RouteSmart", "Weigh reliability, access, and long-term transport drag before you commit."),
        }[self.browser_page]

    def _render_browser_spotlight(self, parent: tk.Frame, wraplength: int) -> None:
        player = self.controller.state.player
        cards = tk.Frame(parent, bg="#ffffff")
        cards.pack(fill="x", pady=(0, 10))
        if self.browser_page == "jobs":
            items = (
                ("Current Lane", self._career_name(), "#dbeafe"),
                ("Current Role", self._career_tier_label(), "#dcfce7"),
                ("Momentum", str(player.career.promotion_momentum), "#fef3c7"),
            )
        elif self.browser_page == "education":
            items = (
                ("Program", self._education_name(), "#dbeafe"),
                ("Standing", str(player.education.standing), "#dcfce7"),
                ("GPA", f"{player.education.college_gpa:.2f}", "#fef3c7"),
            )
        elif self.browser_page == "housing":
            items = (
                ("Current Home", self._housing_name(), "#dbeafe"),
                ("Stability", str(player.housing.housing_stability), "#dcfce7"),
                ("Months In Place", str(player.housing.months_in_place), "#fef3c7"),
            )
        else:
            items = (
                ("Current Ride", self._transport_name(), "#dbeafe"),
                ("Reliability", str(player.transport.reliability_score), "#dcfce7"),
                ("Months Owned", str(player.transport.months_owned), "#fef3c7"),
            )
        for label, value, color in items:
            card = tk.Frame(cards, bg="#ffffff", bd=1, relief="solid")
            card.pack(side="left", fill="x", expand=True, padx=(0, 8))
            tk.Label(card, text=label, bg=color, fg="#1f2937", anchor="w", padx=10, pady=5, font=("Tahoma", 8, "bold")).pack(fill="x")
            tk.Label(card, text=value, bg="#ffffff", fg="#0f172a", anchor="w", padx=10, pady=10, wraplength=wraplength // 3, font=("Tahoma", 10, "bold")).pack(fill="x")

    def _browser_action_label(self) -> str:
        return {
            "jobs": "Apply",
            "education": "Enroll",
            "housing": "Move In",
            "transport": "Switch",
        }[self.browser_page]

    def _render_option_buttons(self, parent: tk.Frame, options, *, apply_callback, wraplength: int, action_label: str) -> None:
        for label, item_id, description, allowed, reason in options:
            row = tk.Frame(parent, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4)
            text = tk.Frame(row, bg="#ffffff")
            text.pack(side="left", fill="both", expand=True, padx=10, pady=8)
            headline = tk.Frame(text, bg="#ffffff")
            headline.pack(fill="x")
            tk.Label(headline, text=label, bg="#ffffff", anchor="w", font=("Tahoma", 10, "bold")).pack(side="left")
            badge_text = "Available Now" if allowed else "Requirements Missing"
            badge_color = "#d1fae5" if allowed else "#fee2e2"
            tk.Label(headline, text=badge_text, bg=badge_color, anchor="e", padx=8, pady=2, font=("Tahoma", 8, "bold")).pack(side="right")
            tk.Label(
                text,
                text=description if allowed else f"{description}\nBlocked: {reason}",
                bg="#ffffff",
                justify="left",
                anchor="w",
                wraplength=wraplength,
                fg="#222222" if allowed else "#8b0000",
                font=("Tahoma", 9),
            ).pack(fill="x", pady=(4, 0))
            tk.Button(
                row,
                text=action_label if allowed else "Blocked",
                state="normal" if allowed else "disabled",
                command=lambda selected=item_id: apply_callback(selected),
                bg="#f4f4f4",
                relief="raised",
                bd=1,
                padx=14,
                pady=8,
            ).pack(side="right", padx=10, pady=10)

    def render_profile(self, app_id: str) -> None:
        _, inner = self._build_window_shell(app_id, "Profile")
        state = self.controller.state
        player = state.player
        nav = tk.Frame(inner, bg="#d7e4ff", bd=1, relief="solid")
        nav.pack(fill="x")
        self._build_responsive_tabs(
            nav,
            app_id=app_id,
            items=[
                ("Info", "info"),
                ("Health", "health"),
                ("Resume", "resume"),
                ("Transport", "transport"),
                ("Degrees", "degrees"),
                ("Net Worth", "net_worth"),
                ("Settings", "settings"),
            ],
            current_id=self.profile_tab,
            on_select=self.set_profile_tab,
            compact_threshold=780,
        )

        body = tk.Frame(inner, bg="#ffffff", bd=1, relief="sunken")
        body.pack(fill="both", expand=True, pady=(8, 0))
        content = self._build_scroll_area(body, bg="#ffffff")
        content.configure(padx=12, pady=12)

        if self.profile_tab == "info":
            top = tk.Frame(content, bg="#ffffff")
            top.pack(fill="x")
            avatar = tk.Frame(top, bg="#ffffff", width=170, height=200)
            avatar.pack(side="left", padx=(0, 14), pady=8)
            avatar.pack_propagate(False)
            avatar_panel = tk.Frame(avatar, bg="#dfe8fb", bd=1, relief="solid")
            avatar_panel.pack(fill="both", expand=True, padx=8, pady=8)
            profile_icon = self.icon_images.get("profile")
            if profile_icon is not None:
                self.profile_avatar_image = profile_icon.zoom(2, 2) if profile_icon.width() <= 64 else profile_icon
                tk.Label(avatar_panel, image=self.profile_avatar_image, bg="#dfe8fb").pack(pady=(18, 10))
            else:
                tk.Label(avatar_panel, text="Profile", bg="#dfe8fb", fg="#1f2937", font=("Tahoma", 12, "bold")).pack(pady=(32, 8))
            tk.Label(avatar_panel, text="Player Card", bg="#dfe8fb", fg="#334155", font=("Tahoma", 9, "bold")).pack()

            facts = tk.Frame(top, bg="#ffffff")
            facts.pack(side="left", fill="both", expand=True, pady=16)
            info_rows = (
                ("Name", player.name),
                ("Age", str(state.current_age)),
                ("Employment status", "Employed" if player.career.track_id != "unemployed" else "Unemployed"),
                ("Current job title", self._career_tier_label()),
                ("Current career", self._career_name()),
                ("Current city", player.current_city_id.replace("_", " ").title()),
                ("Housing", self._housing_name()),
                ("Transport", self._transport_name()),
            )
            for label, value in info_rows:
                row = tk.Frame(facts, bg="#ffffff")
                row.pack(fill="x", pady=5)
                tk.Label(row, text=label, bg="#ffffff", anchor="w", width=18, font=("Tahoma", 11, "bold")).pack(side="left")
                tk.Label(row, text=value, bg="#ffffff", anchor="w", font=("Tahoma", 11)).pack(side="left", fill="x", expand=True)

        elif self.profile_tab == "health":
            for label, value, hint in (
                ("Stress", player.stress, "High stress makes burnout and collapse more likely."),
                ("Energy", player.energy, "Low energy reduces resilience and work/school performance."),
                ("Life Satisfaction", player.life_satisfaction, "Captures whether this decade feels worth building."),
                ("Family Support", player.family_support, "Affects fallback options and emotional stability."),
                ("Social Stability", player.social_stability, "Makes recovery and messy months easier to survive."),
            ):
                card = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
                card.pack(fill="x", pady=5)
                tk.Label(card, text=f"{label}: {value}", bg="#dfe8fb", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
                tk.Label(card, text=hint, bg="#ffffff", anchor="w", justify="left", wraplength=620, padx=10, pady=8, font=("Tahoma", 9)).pack(fill="x")
            warnings = self.controller.build_crisis_warnings() or ["No major warning flags right now."]
            tk.Label(content, text="Current Warnings", bg="#ffe5b4", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(10, 0))
            for warning in warnings:
                tk.Label(content, text=f"- {warning}", bg="#ffffff", anchor="w", justify="left", wraplength=640, padx=12, pady=4, font=("Tahoma", 9)).pack(fill="x")

        elif self.profile_tab == "resume":
            tk.Label(content, text="Career Snapshot", bg="#dfe8fb", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
            for line in (
                f"Track: {self._career_name()}",
                f"Role: {self._career_tier_label()}",
                f"Months in track: {player.career.months_in_track}",
                f"Promotion progress: {player.career.promotion_progress}",
                f"Promotion momentum: {player.career.promotion_momentum}",
                f"Recent performance: {player.career.recent_performance_tag}",
                f"Transition drag months: {player.career.transition_penalty_months}",
            ):
                tk.Label(content, text=line, bg="#ffffff", anchor="w", padx=10, pady=4, font=("Tahoma", 9)).pack(fill="x")
            tk.Label(content, text="Recent History", bg="#ffe5b4", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(12, 0))
            for line in reversed(state.log_messages[-10:] or ["No major work history logged yet."]):
                tk.Label(content, text=f"- {line}", bg="#ffffff", anchor="w", justify="left", wraplength=650, padx=12, pady=3, font=("Tahoma", 9)).pack(fill="x")

        elif self.profile_tab == "transport":
            transport_rows = (
                ("Current transport", self._transport_name()),
                ("Months owned", str(player.transport.months_owned)),
                ("Reliability", str(player.transport.reliability_score)),
                ("Breakdown pressure", str(player.transport.breakdown_pressure)),
                ("Recent repair flag", "Yes" if player.transport.recent_repair_flag else "No"),
                ("Recent switch penalty", str(player.transport.recent_switch_penalty_months)),
            )
            for label, value in transport_rows:
                row = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
                row.pack(fill="x", pady=4)
                tk.Label(row, text=label, bg="#ffffff", anchor="w", width=22, padx=10, pady=8, font=("Tahoma", 10, "bold")).pack(side="left")
                tk.Label(row, text=value, bg="#ffffff", anchor="w", padx=10, pady=8, font=("Tahoma", 10)).pack(side="left")

        elif self.profile_tab == "degrees":
            tk.Label(content, text="Education Status", bg="#dfe8fb", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
            for line in (
                f"Program: {self._education_name()}",
                f"Active: {'Yes' if player.education.is_active else 'No'}",
                f"Paused: {'Yes' if player.education.is_paused else 'No'}",
                f"Months completed: {player.education.months_completed}",
                f"Standing: {player.education.standing}",
                f"GPA: {player.education.college_gpa:.2f}",
                f"Education momentum: {player.education.education_momentum}",
            ):
                tk.Label(content, text=line, bg="#ffffff", anchor="w", padx=10, pady=4, font=("Tahoma", 9)).pack(fill="x")
            tk.Label(content, text="Credentials", bg="#ffe5b4", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(12, 0))
            credentials = player.education.earned_credential_ids or ["No credentials earned yet."]
            for credential in credentials:
                tk.Label(content, text=f"- {credential.replace('_', ' ')}", bg="#ffffff", anchor="w", padx=12, pady=3, font=("Tahoma", 9)).pack(fill="x")
            completed = player.education.completed_program_ids or ["No completed programs yet."]
            tk.Label(content, text="Completed Programs", bg="#dfe8fb", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(12, 0))
            for program in completed:
                tk.Label(content, text=f"- {program.replace('_', ' ')}", bg="#ffffff", anchor="w", padx=12, pady=3, font=("Tahoma", 9)).pack(fill="x")

        elif self.profile_tab == "net_worth":
            summary = self.controller.final_score_summary()
            total_assets = player.cash + player.savings + player.high_interest_savings + player.index_fund + player.aggressive_growth_fund
            net_worth = total_assets - player.debt
            for label, value in (
                ("Cash", player.cash),
                ("Savings", player.savings),
                ("High-Interest Savings", player.high_interest_savings),
                ("Index Fund", player.index_fund),
                ("Growth Fund", player.aggressive_growth_fund),
                ("Debt", -player.debt),
                ("Net Worth", net_worth),
                ("Monthly Surplus", player.monthly_surplus),
            ):
                row = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
                row.pack(fill="x", pady=4)
                tk.Label(row, text=label, bg="#ffffff", anchor="w", width=22, padx=10, pady=8, font=("Tahoma", 10, "bold")).pack(side="left")
                tk.Label(row, text=f"${value}", bg="#ffffff", anchor="e", padx=10, pady=8, font=("Tahoma", 10)).pack(side="right")
            tk.Label(content, text="Projected Ending", bg="#ffe5b4", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(12, 0))
            tk.Label(content, text=f"{summary.ending_label}\nScore: {summary.final_score}", bg="#ffffff", anchor="w", justify="left", padx=12, pady=8, font=("Tahoma", 10)).pack(fill="x")

        else:
            tk.Label(content, text="Settings", bg="#dfe8fb", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
            for label, callback in (
                ("Open Save Center", lambda: self.open_app("saves")),
                ("Show Score Details", self.show_score_projection),
                ("Restart Run", self.restart_default_run),
            ):
                tk.Button(content, text=label, command=callback, bg="#f4f4f4", relief="raised", bd=1, padx=10, pady=8).pack(fill="x", padx=8, pady=4)
            tk.Label(content, text="Recent Milestones", bg="#ffe5b4", anchor="w", padx=10, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x", pady=(12, 0))
            milestones = state.annual_milestones[-5:] or []
            if not milestones:
                tk.Label(content, text="No annual milestones yet.", bg="#ffffff", anchor="w", padx=12, pady=6, font=("Tahoma", 9)).pack(fill="x")
            for milestone in reversed(milestones):
                tk.Label(content, text=f"Age {milestone.age}: {milestone.career_tier_label} | Net worth ${milestone.net_worth}", bg="#ffffff", anchor="w", padx=12, pady=4, font=("Tahoma", 9)).pack(fill="x")

    def render_saves(self, app_id: str) -> None:
        _, inner = self._build_window_shell(app_id, "Save Center")
        self._build_action_toolbar(
            inner,
            app_id=app_id,
            items=self._save_toolbar_actions(),
            compact_threshold=640,
            compact_label="\u2630 Save Menu",
        )

        body = tk.Frame(inner, bg="#ffffff", bd=1, relief="sunken")
        body.pack(fill="both", expand=True, padx=6, pady=6)
        tk.Label(body, text="Recent Saves", bg="#dfe8fb", anchor="w", padx=10, pady=8, font=("Tahoma", 10, "bold")).pack(fill="x")
        split = tk.Frame(body, bg="#ffffff")
        split.pack(fill="both", expand=True)
        left = tk.Frame(split, bg="#ffffff")
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(split, bg="#f8fbff", bd=1, relief="solid", width=230)
        right.pack(side="left", fill="y", padx=(8, 0), pady=8)
        right.pack_propagate(False)
        content = self._build_scroll_area(left, bg="#ffffff")
        recent = self.recent_save_files()
        if not recent:
            tk.Label(content, text="No save files found yet.", bg="#ffffff", anchor="w", padx=10, pady=10).pack(fill="x")
        if self.selected_recent_save is None and recent:
            self.selected_recent_save = recent[0].name
        for path in recent:
            selected = path.name == self.selected_recent_save
            row = tk.Frame(content, bg="#dce9ff" if selected else "#ffffff", bd=1, relief="solid")
            row.pack(fill="x", padx=8, pady=4)
            text = tk.Frame(row, bg="#dce9ff" if selected else "#ffffff")
            text.pack(side="left", fill="both", expand=True, padx=10, pady=8)
            tk.Label(text, text=path.name, bg="#dce9ff" if selected else "#ffffff", anchor="w", font=("Tahoma", 10, "bold")).pack(fill="x")
            tk.Label(text, text=str(path), bg="#dce9ff" if selected else "#ffffff", anchor="w", fg="#4b5563", font=("Tahoma", 8)).pack(fill="x")
            tk.Button(row, text="Select", command=lambda selected=path.name: self.select_recent_save(selected), bg="#f4f4f4", relief="raised", bd=1, padx=14, pady=8).pack(side="right", padx=10, pady=10)

        selected_path = next((path for path in recent if path.name == self.selected_recent_save), None)
        tk.Label(right, text="Selection", bg="#dfe8fb", anchor="w", padx=8, pady=6, font=("Tahoma", 10, "bold")).pack(fill="x")
        if selected_path is None:
            tk.Label(right, text="Choose a save to inspect.", bg="#f8fbff", anchor="w", justify="left", wraplength=200, padx=10, pady=10).pack(fill="x")
        else:
            tk.Label(right, text=selected_path.name, bg="#f8fbff", anchor="w", justify="left", wraplength=200, padx=10, pady=8, font=("Tahoma", 10, "bold")).pack(fill="x")
            modified = datetime.fromtimestamp(selected_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            tk.Label(right, text=f"Modified:\n{modified}", bg="#f8fbff", anchor="w", justify="left", wraplength=200, padx=10, pady=6, font=("Tahoma", 8)).pack(fill="x")
            tk.Label(right, text=str(selected_path), bg="#f8fbff", anchor="w", justify="left", wraplength=200, padx=10, pady=6, fg="#4b5563", font=("Tahoma", 8)).pack(fill="x")
            tk.Button(right, text="Load Selected Save", command=lambda selected=selected_path: self.load_recent_save(selected), bg="#fff6d6", relief="raised", bd=1, padx=10, pady=8, font=("Tahoma", 9, "bold")).pack(fill="x", padx=10, pady=(10, 6))
            tk.Button(right, text="Open Save Folder", command=self.open_save_folder, bg="#f4f4f4", relief="raised", bd=1, padx=10, pady=6).pack(fill="x", padx=10, pady=(0, 10))

    def render_windows(self) -> None:
        for app_id, window in list(self.open_windows.items()):
            if window.minimized:
                window.toplevel.withdraw()
                continue
            if not window.toplevel.winfo_exists():
                self.open_windows.pop(app_id, None)
                continue
            if app_id == "mail":
                self.render_mail(app_id)
            elif app_id == "bank":
                self.render_bank(app_id)
            elif app_id == "browser":
                self.render_browser(app_id)
            elif app_id == "profile":
                self.render_profile(app_id)
            elif app_id == "saves":
                self.render_saves(app_id)
            self._attach_focus_bindings(window.host, app_id)

    def helper_message(self) -> str:
        state = self.controller.state
        warnings = self.controller.build_crisis_warnings()
        if state.game_over_reason:
            return "This run is over. Check Profile or Mail, then restart when you're ready."
        if warnings:
            return f"Heads up. {warnings[0]} Click Mail or Bank Account before you hit Next turn."
        if state.player.education.is_active and state.player.education.standing < 60:
            return "School is wobbling. Open Internet and review your education options before the next month."
        return "When you're ready, click Next turn to advance the simulation by 1 month."

    def refresh(self) -> None:
        state = self.controller.state
        self.controller = self.session.require_controller()
        self.render_windows()
        self.helper_label.configure(text=self.helper_message())
        unread = sum(1 for mail in self.build_mail_items() if mail.unread)
        self._refresh_recent_saves()
        self.taskbar_status.configure(text=f"{self.active_app.title() if self.active_app else 'Desktop'}   |   {state.player.name}   |   Month {state.current_month}")
        warnings = self.controller.build_crisis_warnings()
        unread = sum(1 for mail in self.build_mail_items() if mail.unread)
        self.tray_label.configure(text=f"Mail {unread}  |  Alerts {len(warnings)}")
        self.clock_label.configure(text=f"Y{state.current_year} M{((state.current_month - 1) % 12) + 1:02d}")
        self.root.title(f"{state.game_title} - Desktop - {state.player.name} ({unread} unread)")
        if self.active_app and self.active_app in self.open_windows:
            self._focus_window(self.active_app)
        player = state.player
        self.metrics_labels["cash"].configure(text=f"${player.cash}")
        self.metrics_labels["stress"].configure(text=str(player.stress))
        self.metrics_labels["energy"].configure(text=str(player.energy))
        self.metrics_labels["housing"].configure(text=str(player.housing.housing_stability))
        self.metrics_labels["career"].configure(text=str(player.career.promotion_momentum))
        toast_text = warnings[0] if warnings else (state.recent_summary[-1] if state.recent_summary else "Everything is stable enough right now.")
        self.toast_label.configure(text=toast_text[:180])

    def _refresh_recent_saves(self) -> None:
        if not hasattr(self, "start_recent_holder"):
            return
        for child in self.start_recent_holder.winfo_children():
            child.destroy()
        recent = self.recent_save_files()[:4]
        if not recent:
            tk.Label(self.start_recent_holder, text="No recent saves", bg="#f4f6fb", fg="#6b7280", anchor="w", padx=10, pady=6).pack(fill="x")
            return
        for path in recent:
            tk.Button(
                self.start_recent_holder,
                text=path.name,
                command=lambda selected=path: self.load_recent_save(selected),
                bg="#f4f6fb",
                activebackground="#d7e6ff",
                relief="flat",
                bd=0,
                anchor="w",
                padx=10,
                pady=5,
                font=("Tahoma", 9),
            ).pack(fill="x")

    def choose_budget(self) -> None:
        self._choose_from_records(
            "Budget Stance",
            [(stance.name, stance.id, stance.description) for stance in self.controller.available_budget_stances()],
            self.controller.change_budget_stance,
        )

    def choose_wealth(self) -> None:
        self._choose_from_records(
            "Wealth Strategy",
            [(strategy.name, strategy.id, strategy.description) for strategy in self.controller.available_wealth_strategies()],
            self.controller.change_wealth_strategy,
        )

    def choose_focus(self) -> None:
        self._choose_from_records(
            "Monthly Focus",
            [(focus.name, focus.id, focus.description) for focus in self.controller.available_focus_actions()],
            self.controller.change_focus_action,
        )

    def apply_career(self, career_id: str) -> None:
        self._attempt_action(lambda: self.controller.change_career(career_id))

    def apply_education(self, program_id: str) -> None:
        self._attempt_action(lambda: self.controller.change_education(program_id))

    def apply_housing(self, housing_id: str) -> None:
        self._attempt_action(lambda: self.controller.change_housing(housing_id))

    def apply_transport(self, transport_id: str) -> None:
        self._attempt_action(lambda: self.controller.change_transport(transport_id))

    def _attempt_action(self, callback) -> None:
        try:
            callback()
            self.session.autosave()
            self.refresh()
        except ValueError as exc:
            messagebox.showerror("Action failed", str(exc))

    def _choose_record_from_window(self, title: str, options: list[tuple[str, str, str]], apply_callback) -> None:
        picker = tk.Toplevel(self.root)
        picker.title(title)
        picker.transient(self.root)
        picker.geometry("520x420")
        picker.minsize(420, 320)
        picker.configure(bg="#ece9d8")
        picker.lift()
        picker.attributes("-topmost", True)
        picker.after(150, lambda: picker.attributes("-topmost", False))
        picker.focus_force()
        picker.grab_set()

        header = tk.Frame(picker, bg="#dfe8fb")
        header.pack(fill="x")
        tk.Label(header, text=title, bg="#dfe8fb", fg="#1f2937", anchor="w", padx=12, pady=10, font=("Tahoma", 11, "bold")).pack(fill="x")

        selected_id = tk.StringVar(value=options[0][1] if options else "")
        selected_label = tk.Label(picker, text="", bg="#fffbe8", fg="#222222", justify="left", wraplength=470, padx=12, pady=10, anchor="w")
        selected_label.pack(fill="x", padx=10, pady=(8, 4))

        content = self._build_scroll_area(picker, bg="#ffffff")
        content.pack_configure(fill="both", expand=True, padx=10, pady=(0, 8))

        def refresh_selection() -> None:
            for label, item_id, desc in options:
                if item_id == selected_id.get():
                    selected_label.configure(text=f"{label}\n\n{desc}\n\nID: {item_id}")
                    break

        for label, item_id, description in options:
            row = tk.Frame(content, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4, padx=6)
            radio = tk.Radiobutton(
                row,
                text=label,
                variable=selected_id,
                value=item_id,
                bg="#ffffff",
                anchor="w",
                command=refresh_selection,
                font=("Tahoma", 10, "bold"),
            )
            radio.pack(fill="x", padx=8, pady=(8, 2))
            tk.Label(row, text=description, bg="#ffffff", anchor="w", justify="left", wraplength=420, padx=14, pady=0, font=("Tahoma", 9)).pack(fill="x", pady=(0, 8))
            row.bind("<Double-Button-1>", lambda _event, selected=item_id: selected_id.set(selected))

        buttons = tk.Frame(picker, bg="#ece9d8")
        buttons.pack(fill="x", padx=10, pady=(0, 10))

        def apply_selected() -> None:
            choice = selected_id.get().strip()
            if not choice:
                return
            picker.destroy()
            self._attempt_action(lambda: apply_callback(choice))

        tk.Button(buttons, text="Apply", command=apply_selected, bg="#fff6d6", relief="raised", bd=1, padx=18, pady=6, font=("Tahoma", 9, "bold")).pack(side="right", padx=(6, 0))
        tk.Button(buttons, text="Cancel", command=picker.destroy, bg="#f4f4f4", relief="raised", bd=1, padx=18, pady=6).pack(side="right")
        refresh_selection()

    def _choose_from_records(self, title: str, options: list[tuple[str, str, str]], apply_callback) -> None:
        if not options:
            return
        self._choose_record_from_window(title, options, apply_callback)

    def set_browser_page(self, page: str) -> None:
        self.browser_page = page
        self.refresh()

    def resolve_month(self) -> None:
        try:
            self.session.resolve_month()
            self.session.autosave()
            self.refresh()
            if self.session.is_finished():
                summary = self.session.final_score_summary()
                messagebox.showinfo("Run Finished", f"{summary.ending_label}\nScore: {summary.final_score}")
        except ValueError as exc:
            messagebox.showerror("Advance failed", str(exc))

    def save_snapshot(self) -> None:
        default_name = f"{self.session.mode}_snapshot.json"
        save_path = filedialog.asksaveasfilename(
            title="Save Snapshot",
            parent=self.root,
            initialdir=str(self.session.paths.saves_dir),
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON Save", "*.json")],
        )
        if not save_path:
            return
        self.session.save_to_path(Path(save_path))
        self.refresh()
        messagebox.showinfo("Saved", f"Saved to {Path(save_path).name}")

    def quick_save_snapshot(self) -> None:
        self.session.autosave()
        self.refresh()
        messagebox.showinfo("Saved", f"Saved to {self.session.bundle.config.autosave_name}")

    def load_snapshot_dialog(self) -> None:
        load_path = filedialog.askopenfilename(
            title="Load Snapshot",
            parent=self.root,
            initialdir=str(self.session.paths.saves_dir),
            filetypes=[("JSON Save", "*.json")],
        )
        if not load_path:
            return
        self._load_save_path(Path(load_path))

    def load_recent_save(self, path: Path) -> None:
        self.hide_start_menu()
        self._load_save_path(path)

    def _load_save_path(self, path: Path) -> None:
        new_session = GameSession.load_from_path(path, mode=self.session.mode, root=self.session.paths.root)
        self.session = new_session
        self.controller = self.session.ensure_started(default_player_name=self.startup_options.player_name or "DesktopPlayer")
        self.refresh()
        messagebox.showinfo("Loaded", f"Loaded {path.name}")

    def select_recent_save(self, save_name: str) -> None:
        self.selected_recent_save = save_name
        self.refresh()

    def open_save_folder(self) -> None:
        os.startfile(self.session.paths.saves_dir)  # type: ignore[attr-defined]

    def restart_default_run(self) -> None:
        self.session.start_new_game(self.startup_options.completed_with_defaults(self.session.bundle, default_player_name="DesktopPlayer"))
        self.controller = self.session.require_controller()
        for app_id in list(self.open_windows):
            self.close_window(app_id)
        self.active_app = "mail"
        self.mail_index = 0
        self.open_app("mail")

    def show_leaderboard(self) -> None:
        summary = self.controller.final_score_summary()
        messagebox.showinfo(
            "Leaderboard",
            "This shell does not have an online leaderboard yet.\n\n"
            f"Current projected label: {summary.ending_label}\n"
            f"Current projected score: {summary.final_score}",
        )

    def show_score_projection(self) -> None:
        summary = self.controller.final_score_summary()
        breakdown = "\n".join(f"{key.replace('_', ' ').title()}: {value:.2f}" for key, value in summary.breakdown.items())
        messagebox.showinfo(
            "Projected Ending",
            f"{summary.ending_label}\nScore: {summary.final_score}\n\n{summary.outcome}\n\n{breakdown}",
        )

    def run(self) -> None:
        self.root.mainloop()
