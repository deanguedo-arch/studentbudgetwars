"""Right column — finances, wellbeing bars, modifiers, and crisis watch."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING, COLOR_NEUTRAL,
    COLOR_STRESS, COLOR_ENERGY, COLOR_LIFE, COLOR_FAMILY, COLOR_SOCIAL,
    COLOR_MONEY_POS, COLOR_MONEY_NEG,
    ACCENT_HOUSING, ACCENT_TRANSPORT,
    FONT_SUBHEADING, FONT_BODY, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M, CARD_BORDER_W,
)


def _mini_bar(parent: tk.Misc, value: int, max_val: int, color: str,
              width: int = 70) -> tk.Frame:
    """Labeled mini progress bar."""
    frame = tk.Frame(parent, bg=BG_ELEVATED)
    canvas = tk.Canvas(frame, width=width, height=8, bg=BG_DARK, bd=0, highlightthickness=0)
    canvas.pack(side="left")
    fill = max(0, min(width, int(width * value / max(1, max_val))))
    canvas.create_rectangle(0, 0, fill, 8, fill=color, outline="")
    return frame


class FinancePanel(tk.Frame):
    def __init__(self, master: tk.Misc, title: str = "Score & Pressure"):
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

            # Section headers
            if line in ("Active Modifiers:", "Crisis Watch:"):
                fg = TEXT_HEADING
                font = FONT_SMALL if not self._large else ("Segoe UI", 11, "bold")
            # Score/tier
            elif lower.startswith("projected score") or lower.startswith("tier:"):
                fg = TEXT_HEADING
            # Money lines
            elif lower.startswith("cash:") or lower.startswith("income:"):
                fg = COLOR_MONEY_POS
            elif lower.startswith("debt:") or lower.startswith("expenses:"):
                fg = COLOR_MONEY_NEG
            elif lower.startswith("savings:"):
                fg = COLOR_MONEY_POS
            elif "monthly swing" in lower:
                # Parse the value to color it
                fg = COLOR_POSITIVE if "+" in line or "$0" not in line else TEXT_SECONDARY
                if "-$" in line:
                    fg = COLOR_NEGATIVE
            # Vitals
            elif lower.startswith("stress:"):
                fg = COLOR_STRESS
            elif lower.startswith("energy:"):
                fg = COLOR_ENERGY
            elif lower.startswith("life:"):
                fg = COLOR_LIFE
            elif lower.startswith("family:"):
                fg = COLOR_FAMILY
            elif lower.startswith("social:"):
                fg = COLOR_SOCIAL
            # Housing/transport
            elif "housing stability" in lower:
                fg = ACCENT_HOUSING
            elif "transport reliability" in lower:
                fg = ACCENT_TRANSPORT
            # Crisis
            elif lower.startswith("stable enough") or lower.startswith("no major"):
                fg = COLOR_POSITIVE
            elif any(kw in lower for kw in ["close to", "dangerously", "wobbling", "sliding", "threatening"]):
                fg = COLOR_WARNING
            # Modifiers
            elif "(" in line and ")" in line and "remaining" not in lower:
                fg = COLOR_WARNING

            lbl = tk.Label(self._content, text=line, bg=bg, fg=fg, font=font,
                           anchor="w", justify="left", wraplength=340)
            lbl.pack(fill="x", anchor="w", pady=1)
            self._widgets.append(lbl)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
