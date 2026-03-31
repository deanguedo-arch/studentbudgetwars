from __future__ import annotations

import tkinter as tk
from collections.abc import Callable


class ActionsPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg="#c0c0c0", bd=2, relief="raised")
        tk.Label(self, text="Actions", bg="#c0c0c0", font=("Courier New", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.button_frame = tk.Frame(self, bg="#c0c0c0")
        self.button_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.buttons: dict[str, tk.Button] = {}

    def set_actions(self, actions: list[tuple[str, Callable[[], None]]]) -> None:
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        self.buttons.clear()
        for index, (label, command) in enumerate(actions):
            button = tk.Button(
                self.button_frame,
                text=label,
                command=command,
                width=16,
                bg="#d4d0c8",
                relief="raised",
                font=("Courier New", 10),
            )
            button.grid(row=index // 2, column=index % 2, padx=4, pady=4, sticky="ew")
            self.buttons[label] = button
        for column in range(2):
            self.button_frame.grid_columnconfigure(column, weight=1)
