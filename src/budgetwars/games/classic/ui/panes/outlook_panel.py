"""Center column — outlook panel showing focus, pressure, driver notes, and last month recap."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_WARNING, COLOR_NEGATIVE, COLOR_POSITIVE,
    ACCENT_FOCUS,
    FONT_SUBHEADING, FONT_BODY, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M, CARD_BORDER_W,
)


class OutlookPanel(tk.Frame):
    """Focus + pressure + driver notes + last-month recap."""

    def __init__(self, master: tk.Misc, title: str = "This Month"):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False

        header = tk.Label(self, text=f"  {title}  ", bg=BG_CARD, fg=TEXT_HEADING,
                          font=FONT_SUBHEADING, anchor="w")
        header.pack(fill="x", padx=PAD_S, pady=(PAD_S, 2))

        self._content = tk.Frame(self, bg=BG_CARD)
        self._content.pack(fill="both", expand=True, padx=PAD_S, pady=PAD_S)

        self._widgets: list[tk.Widget] = []

    def render(self, lines: list[str]) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()

        for line in lines:
            lower = line.lower()
            fg = TEXT_PRIMARY
            font = FONT_SMALL if not self._large else ("Segoe UI", 11)
            bg = BG_CARD

            if lower.startswith("warning:"):
                fg = COLOR_WARNING
                line = "  " + line
                if "energy is capping" in lower or "social isolation" in lower:
                    fg = COLOR_NEGATIVE
                elif "network can bail" in lower:
                    fg = COLOR_POSITIVE
                elif "consequence" in lower or "something is building" in lower:
                    fg = COLOR_NEGATIVE
            elif lower.startswith("career lockout") or lower.startswith("promotion gate"):
                fg = COLOR_NEGATIVE
            elif "focus" in lower and ":" in line:
                fg = ACCENT_FOCUS
            elif lower.startswith("last month:") or lower.startswith("why this month"):
                fg = TEXT_HEADING
                font = FONT_SMALL if not self._large else ("Segoe UI", 11, "bold")
            elif "quiet month" in lower or "stable" in lower:
                fg = COLOR_POSITIVE
            elif "$" in line and ("income" in lower or "expenses" in lower):
                fg = TEXT_SECONDARY

            lbl = tk.Label(self._content, text=line, bg=bg, fg=fg, font=font,
                           anchor="w", justify="left", wraplength=420)
            lbl.pack(fill="x", anchor="w", pady=1)
            self._widgets.append(lbl)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
