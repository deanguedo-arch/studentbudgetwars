from __future__ import annotations

import tkinter as tk

from budgetwars.engine import GameController

from .main_window import MainWindow


class BudgetWarsTkApp:
    def __init__(self, controller: GameController):
        self.root = tk.Tk()
        self.root.configure(bg="#c0c0c0")
        self.root.geometry("1240x760")
        self.root.minsize(1080, 680)
        self.window = MainWindow(self.root, controller)

    def run(self) -> None:
        self.root.mainloop()
