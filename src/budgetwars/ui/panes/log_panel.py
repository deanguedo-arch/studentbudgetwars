from __future__ import annotations

import tkinter as tk


class LogPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg="#c0c0c0", bd=2, relief="sunken")
        tk.Label(self, text="Activity Log", bg="#c0c0c0", font=("Courier New", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        frame = tk.Frame(self, bg="#c0c0c0")
        frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.text = tk.Text(
            frame,
            height=12,
            bg="white",
            fg="black",
            font=("Courier New", 10),
            wrap="word",
            state="disabled",
        )
        scrollbar = tk.Scrollbar(frame, command=self.text.yview)
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def render(self, messages: list[str]) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.insert("1.0", "\n".join(messages[-20:]))
        self.text.configure(state="disabled")
        self.text.see("end")
