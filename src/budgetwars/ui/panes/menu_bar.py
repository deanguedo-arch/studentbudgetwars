from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


def build_menu_bar(root: tk.Tk, callbacks: dict[str, Callable[[], None]]) -> tk.Menu:
    menu_bar = tk.Menu(root, tearoff=False, bg="#c0c0c0", fg="black")

    game_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    game_menu.add_command(label="New Game", command=callbacks["new_game"])
    game_menu.add_command(label="Save", command=callbacks["save"])
    game_menu.add_separator()
    game_menu.add_command(label="Exit", command=callbacks["exit"])
    menu_bar.add_cascade(label="Game", menu=game_menu)

    travel_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    travel_menu.add_command(label="Travel", command=callbacks["travel"])
    menu_bar.add_cascade(label="Travel", menu=travel_menu)

    market_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    market_menu.add_command(label="Buy", command=callbacks["buy"])
    market_menu.add_command(label="Sell", command=callbacks["sell"])
    market_menu.add_command(label="Drop", command=callbacks["drop"])
    menu_bar.add_cascade(label="Market", menu=market_menu)

    bank_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    bank_menu.add_command(label="Bank Actions", command=callbacks["bank"])
    menu_bar.add_cascade(label="Bank", menu=bank_menu)

    school_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    school_menu.add_command(label="Study", command=callbacks["study"])
    school_menu.add_command(label="Rest", command=callbacks["rest"])
    menu_bar.add_cascade(label="School", menu=school_menu)

    info_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    info_menu.add_command(label="Projected Score", command=callbacks["score"])
    menu_bar.add_cascade(label="Info", menu=info_menu)

    help_menu = tk.Menu(menu_bar, tearoff=False, bg="#c0c0c0", fg="black")
    help_menu.add_command(label="Controls", command=callbacks["help"])
    menu_bar.add_cascade(label="Help", menu=help_menu)
    return menu_bar
