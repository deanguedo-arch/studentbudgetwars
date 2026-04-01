from __future__ import annotations

import tkinter as tk


class FinancePanel(tk.LabelFrame):
    def __init__(self, master: tk.Misc, title: str = "Finances & Progress"):
        super().__init__(master, text=title, bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self.text = tk.Text(self, height=22, width=34, wrap="word", bg="#efefef", relief="sunken", bd=1)
        self.text.pack(fill="both", expand=True, padx=6, pady=6)
        self.text.configure(state="disabled")

    def render(self, lines: list[str]) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(lines))
        self.text.configure(state="disabled")
