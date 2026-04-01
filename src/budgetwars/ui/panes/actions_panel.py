from __future__ import annotations

import tkinter as tk


class ActionsPanel(tk.LabelFrame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, text="Actions", bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self._buttons: list[tk.Button] = []
        self._normal_font = ("Segoe UI", 10, "bold")
        self._large_font = ("Segoe UI", 12, "bold")
        self._large_text_enabled = False

    def set_actions(self, actions: list[tuple[str, object]]) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()
        for index, (label, callback) in enumerate(actions):
            button = tk.Button(
                self,
                text=label,
                command=callback,
                width=14,
                bg="#d9d9d9",
                activebackground="#e8e8e8",
                relief="raised",
                font=self._large_font if self._large_text_enabled else self._normal_font,
            )
            button.grid(row=0, column=index, padx=4, pady=7, sticky="ew")
            self._buttons.append(button)
            self.grid_columnconfigure(index, weight=1)

    def set_large_text(self, enabled: bool) -> None:
        self._large_text_enabled = enabled
        for button in self._buttons:
            button.configure(font=self._large_font if enabled else self._normal_font)
