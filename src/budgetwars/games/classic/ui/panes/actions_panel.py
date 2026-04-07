"""Bottom action bar with accent-colored system buttons and prominent Resolve."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BG_HOVER, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_CAREER, ACCENT_EDUCATION, ACCENT_HOUSING, ACCENT_TRANSPORT,
    ACCENT_BUDGET, ACCENT_WEALTH, ACCENT_FOCUS, ACCENT_RESOLVE,
    FONT_BUTTON, FONT_BUTTON_LG, FONT_RESOLVE, FONT_RESOLVE_LG,
    PAD_S, PAD_M,
)

_SYSTEM_ACCENTS = {
    "career": ACCENT_CAREER,
    "education": ACCENT_EDUCATION,
    "housing": ACCENT_HOUSING,
    "transport": ACCENT_TRANSPORT,
    "budget": ACCENT_BUDGET,
    "wealth": ACCENT_WEALTH,
    "focus": ACCENT_FOCUS,
}


def _button_bg(label: str) -> str:
    """Get subtle background tint for a system button."""
    key = label.lower().replace(" ", "_")
    accent = _SYSTEM_ACCENTS.get(key)
    if accent:
        # Create a darkened version of the accent for the button bg
        return BG_ELEVATED
    return BG_ELEVATED


def _button_fg(label: str) -> str:
    key = label.lower().replace(" ", "_")
    return _SYSTEM_ACCENTS.get(key, TEXT_PRIMARY)


class ActionsPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._buttons: list[tk.Button] = []
        self._large_text_enabled = False

    def set_actions(self, actions: list[tuple[str, object]]) -> None:
        for button in self._buttons:
            button.destroy()
        self._buttons.clear()

        regular_actions = [a for a in actions if a[0].lower() != "resolve month"]
        resolve_action = next((a for a in actions if a[0].lower() == "resolve month"), None)

        for index, (label, callback) in enumerate(regular_actions):
            row = index // 4
            column = index % 4

            accent = _button_fg(label)
            font = FONT_BUTTON_LG if self._large_text_enabled else FONT_BUTTON

            btn = tk.Button(
                self, text=label, command=callback,
                bg=BG_ELEVATED, fg=accent,
                activebackground=BG_HOVER, activeforeground=TEXT_HEADING,
                relief="flat", bd=0, font=font,
                padx=PAD_M, pady=PAD_S,
                cursor="hand2",
                highlightbackground=BORDER, highlightthickness=1,
            )
            btn.grid(row=row, column=column, padx=3, pady=3, sticky="ew")
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=BG_HOVER))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=BG_ELEVATED))
            self._buttons.append(btn)

        if resolve_action:
            label, callback = resolve_action
            resolve_font = FONT_RESOLVE_LG if self._large_text_enabled else FONT_RESOLVE
            resolve_btn = tk.Button(
                self, text=label, command=callback,
                bg="#4a4520", fg=ACCENT_RESOLVE,
                activebackground="#5a5528", activeforeground="#fff8d0",
                relief="flat", bd=0, font=resolve_font,
                pady=PAD_M, cursor="hand2",
                highlightbackground=ACCENT_RESOLVE, highlightthickness=2,
            )
            resolve_row = (len(regular_actions) - 1) // 4 + 1
            resolve_btn.grid(row=resolve_row, column=0, columnspan=4,
                             padx=PAD_S, pady=(PAD_M, PAD_S), sticky="ew")
            resolve_btn.bind("<Enter>", lambda e: resolve_btn.configure(bg="#5a5528"))
            resolve_btn.bind("<Leave>", lambda e: resolve_btn.configure(bg="#4a4520"))
            self._buttons.append(resolve_btn)

        for i in range(4):
            self.grid_columnconfigure(i, weight=1)

    def set_large_text(self, enabled: bool) -> None:
        self._large_text_enabled = enabled
        for btn in self._buttons:
            if btn.cget("text").lower() == "resolve month":
                btn.configure(font=FONT_RESOLVE_LG if enabled else FONT_RESOLVE)
            else:
                btn.configure(font=FONT_BUTTON_LG if enabled else FONT_BUTTON)
