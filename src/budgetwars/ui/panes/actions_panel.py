from __future__ import annotations

import tkinter as tk


class ActionsPanel(tk.LabelFrame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, text="Actions", bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self._buttons: list[tk.Button] = []

    def set_actions(self, actions: list[tuple[str, object]]) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        for index, (label, callback) in enumerate(actions):
            button = tk.Button(
                self,
                text=label,
                command=callback,
                width=16,
                bg="#d9d9d9",
                activebackground="#e8e8e8",
                relief="raised",
            )
            button.grid(row=0, column=index, padx=4, pady=6, sticky="ew")
            self._buttons.append(button)
            self.grid_columnconfigure(index, weight=1)
