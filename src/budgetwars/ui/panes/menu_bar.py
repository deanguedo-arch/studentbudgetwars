from __future__ import annotations

import tkinter as tk


def build_menu_bar(root: tk.Tk, callbacks: dict[str, object]) -> tk.Menu:
    menu = tk.Menu(root, tearoff=False)

    game_menu = tk.Menu(menu, tearoff=False)
    game_menu.add_command(label="New Game", command=callbacks["new_game"])
    game_menu.add_command(label="Save", command=callbacks["save"])
    game_menu.add_separator()
    game_menu.add_command(label="Exit", command=callbacks["exit"])
    menu.add_cascade(label="Game", menu=game_menu)

    actions_menu = tk.Menu(menu, tearoff=False)
    actions_menu.add_command(label="Career", command=callbacks["career"])
    actions_menu.add_command(label="Education", command=callbacks["education"])
    actions_menu.add_command(label="Housing", command=callbacks["housing"])
    actions_menu.add_command(label="Transport", command=callbacks["transport"])
    actions_menu.add_command(label="Budget", command=callbacks["budget"])
    actions_menu.add_command(label="Focus", command=callbacks["focus"])
    actions_menu.add_command(label="Resolve Month", command=callbacks["resolve"])
    menu.add_cascade(label="Actions", menu=actions_menu)

    info_menu = tk.Menu(menu, tearoff=False)
    info_menu.add_command(label="Projected Ending", command=callbacks["score"])
    info_menu.add_command(label="Help", command=callbacks["help"])
    menu.add_cascade(label="Info", menu=info_menu)

    return menu
