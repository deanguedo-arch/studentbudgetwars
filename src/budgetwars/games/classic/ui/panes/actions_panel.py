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
        regular_actions = [action for action in actions if action[0].lower() != "resolve month"]
        resolve_action = next((action for action in actions if action[0].lower() == "resolve month"), None)
        for index, (label, callback) in enumerate(regular_actions):
            row = index // 3
            column = index % 3
            button = tk.Button(
                self,
                text=label,
                command=callback,
                width=18,
                bg="#d9d9d9",
                activebackground="#e8e8e8",
                relief="raised",
                font=self._large_font if self._large_text_enabled else self._normal_font,
            )
            button.grid(row=row, column=column, padx=4, pady=4, sticky="ew")
            self._buttons.append(button)
        if resolve_action is not None:
            label, callback = resolve_action
            resolve_button = tk.Button(
                self,
                text=label,
                command=callback,
                bg="#ffd966",
                activebackground="#ffeb99",
                fg="#111111",
                relief="raised",
                font=("Segoe UI", 12, "bold") if not self._large_text_enabled else ("Segoe UI", 14, "bold"),
                height=2,
            )
            resolve_button.grid(row=3, column=0, columnspan=3, padx=8, pady=(8, 8), sticky="ew")
            self._buttons.append(resolve_button)
        for index in range(3):
            self.grid_columnconfigure(index, weight=1)

    def set_large_text(self, enabled: bool) -> None:
        self._large_text_enabled = enabled
        for button in self._buttons:
            if button.cget("text").lower() == "resolve month":
                button.configure(font=("Segoe UI", 14, "bold") if enabled else ("Segoe UI", 12, "bold"))
            else:
                button.configure(font=self._large_font if enabled else self._normal_font)
