from __future__ import annotations

import tkinter as tk


class LogPanel(tk.LabelFrame):
    def __init__(self, master: tk.Misc, title: str = "Recent Activity"):
        super().__init__(master, text=title, bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self.text = tk.Text(
            self,
            height=1,
            wrap="word",
            bg="#efefef",
            relief="sunken",
            bd=1,
            font=("Consolas", 11),
            spacing1=1,
            spacing3=2,
        )
        self.text.pack(fill="both", expand=True, padx=6, pady=6)
        self.text.configure(state="disabled")
        self._normal_font = ("Consolas", 11)
        self._large_font = ("Consolas", 13)

    def render(self, messages: list[str], limit: int = 14) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(messages[-limit:]))
        self.text.configure(state="disabled")

    def set_large_text(self, enabled: bool) -> None:
        self.text.configure(font=self._large_font if enabled else self._normal_font)
