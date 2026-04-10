from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..theme import BG_DARK, BG_DARKEST, BG_ELEVATED, BORDER, TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, ACCENT_RESOLVE


def configure_dark_menu_style(menu: tk.Menu) -> None:
    windowing = menu.tk.call("tk", "windowingsystem") if hasattr(menu, "tk") else None
    if windowing == "win32":
        menu.configure(
            bg="#f1f3f8",
            fg="#151a24",
            activebackground="#dfe7ff",
            activeforeground="#0f1624",
            bd=0,
            tearoff=False,
            relief="flat",
        )
        return
    menu.configure(
        bg=BG_DARKEST,
        fg=TEXT_PRIMARY,
        activebackground=BG_ELEVATED,
        activeforeground=TEXT_PRIMARY,
        bd=0,
        tearoff=False,
        relief="flat",
    )


def configure_dark_combobox_style(master: tk.Misc) -> str:
    top = master.winfo_toplevel() if hasattr(master, "winfo_toplevel") else master
    style = ttk.Style(top)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style_name = "ClassicDark.TCombobox"
    style.configure(
        style_name,
        foreground=TEXT_PRIMARY,
        fieldbackground=BG_ELEVATED,
        background=BG_ELEVATED,
        arrowcolor=TEXT_PRIMARY,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        insertcolor=TEXT_PRIMARY,
    )
    style.map(
        style_name,
        foreground=[("readonly", TEXT_PRIMARY), ("focus", TEXT_PRIMARY)],
        fieldbackground=[("readonly", BG_ELEVATED), ("disabled", BG_DARK)],
        background=[("readonly", BG_ELEVATED), ("disabled", BG_DARK)],
        selectforeground=[("readonly", BG_DARKEST)],
        selectbackground=[("readonly", ACCENT_RESOLVE)],
    )
    for target in (top, master):
        target.option_add("*TCombobox*Listbox.background", BG_DARKEST)
        target.option_add("*TCombobox*Listbox.foreground", TEXT_PRIMARY)
        target.option_add("*TCombobox*Listbox.selectBackground", ACCENT_RESOLVE)
        target.option_add("*TCombobox*Listbox.selectForeground", TEXT_HEADING)
        target.option_add("*TCombobox*Listbox.font", "Segoe UI 10")
    return style_name


def build_menu_bar(root: tk.Tk, callbacks: dict[str, object]) -> tk.Menu:
    menu = tk.Menu(root, tearoff=False)
    configure_dark_menu_style(menu)

    game_menu = tk.Menu(menu, tearoff=False)
    configure_dark_menu_style(game_menu)
    game_menu.add_command(label="New Game", command=callbacks["new_game"])
    game_menu.add_command(label="Save", command=callbacks["save"])
    game_menu.add_separator()
    game_menu.add_command(label="Exit", command=callbacks["exit"])
    menu.add_cascade(label="Game", menu=game_menu)

    actions_menu = tk.Menu(menu, tearoff=False)
    configure_dark_menu_style(actions_menu)
    actions_menu.add_command(label="Career", command=callbacks["career"])
    actions_menu.add_command(label="Education", command=callbacks["education"])
    actions_menu.add_command(label="Housing", command=callbacks["housing"])
    actions_menu.add_command(label="Transport", command=callbacks["transport"])
    actions_menu.add_command(label="Budget", command=callbacks["budget"])
    actions_menu.add_command(label="Wealth", command=callbacks["wealth"])
    actions_menu.add_command(label="Focus", command=callbacks["focus"])
    actions_menu.add_command(label="Resolve Month", command=callbacks["resolve"])
    menu.add_cascade(label="Actions", menu=actions_menu)

    view_menu = tk.Menu(menu, tearoff=False)
    configure_dark_menu_style(view_menu)
    view_menu.add_command(label="Toggle Large Text", command=callbacks["text_size"])
    view_menu.add_command(label="Toggle Compact Layout", command=callbacks["compact_layout"])
    menu.add_cascade(label="View", menu=view_menu)

    info_menu = tk.Menu(menu, tearoff=False)
    configure_dark_menu_style(info_menu)
    info_menu.add_command(label="Projected Ending", command=callbacks["score"])
    info_menu.add_command(label="Learn", command=callbacks["learn"])
    info_menu.add_command(label="Help", command=callbacks["help"])
    menu.add_cascade(label="Info", menu=info_menu)

    return menu
