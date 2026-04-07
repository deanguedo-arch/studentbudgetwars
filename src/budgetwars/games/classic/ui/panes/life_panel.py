"""Left column — structured life cards with accent borders."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_CAREER, ACCENT_EDUCATION, ACCENT_HOUSING, ACCENT_TRANSPORT,
    ACCENT_BUDGET, ACCENT_WEALTH, ACCENT_FOCUS,
    COLOR_ENERGY, COLOR_STRESS,
    FONT_SUBHEADING, FONT_BODY, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M, CARD_BORDER_W,
)


def _card(parent: tk.Misc, accent: str) -> tuple[tk.Frame, tk.Frame]:
    """Return (outer_frame, inner_frame) for a card with colored left border."""
    outer = tk.Frame(parent, bg=accent, bd=0)
    inner = tk.Frame(outer, bg=BG_ELEVATED, bd=0, padx=PAD_M, pady=PAD_S)
    inner.pack(side="right", fill="both", expand=True, padx=(CARD_BORDER_W, 0))
    return outer, inner


def _label(parent: tk.Misc, text: str = "", fg: str = TEXT_PRIMARY,
           font=FONT_SMALL, **kw) -> tk.Label:
    return tk.Label(parent, text=text, bg=BG_ELEVATED, fg=fg, font=font,
                    anchor="w", justify="left", **kw)


def _mini_bar(parent: tk.Misc, value: int, max_val: int, color: str,
              width: int = 60) -> tk.Canvas:
    c = tk.Canvas(parent, width=width, height=6, bg=BG_DARK, bd=0, highlightthickness=0)
    fill = max(0, min(width, int(width * value / max(1, max_val))))
    c.create_rectangle(0, 0, fill, 6, fill=color, outline="")
    return c


class LifePanel(tk.Frame):
    """Structured left-column panel with colored cards for each life system."""

    def __init__(self, master: tk.Misc, title: str = "Build"):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False

        header = tk.Label(self, text=f"  {title}  ", bg=BG_CARD, fg=TEXT_HEADING,
                          font=FONT_SUBHEADING, anchor="w")
        header.pack(fill="x", padx=PAD_S, pady=(PAD_S, 2))

        self._scroll_frame = tk.Frame(self, bg=BG_CARD)
        self._scroll_frame.pack(fill="both", expand=True, padx=PAD_S, pady=PAD_S)

        # We'll store card widgets for dynamic rebuild
        self._cards: list[tk.Frame] = []

    def render(self, lines: list[str]) -> None:
        """Accept structured lines and render as cards.

        Expected line format (from main_window): plain text lines grouped by blank lines.
        We parse these into card groups and render with accent colors.
        """
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        # Parse lines into groups separated by blank lines
        groups: list[list[str]] = []
        current: list[str] = []
        for line in lines:
            if not line.strip():
                if current:
                    groups.append(current)
                    current = []
            else:
                current.append(line)
        if current:
            groups.append(current)

        # Map groups to accent colors based on content
        accent_map = [
            (["career", "lane", "momentum"], ACCENT_CAREER),
            (["education", "progress", "standing", "gpa"], ACCENT_EDUCATION),
            (["housing"], ACCENT_HOUSING),
            (["transport"], ACCENT_TRANSPORT),
            (["budget"], ACCENT_BUDGET),
            (["wealth"], ACCENT_WEALTH),
            (["focus"], ACCENT_FOCUS),
        ]

        for group in groups:
            group_text = " ".join(group).lower()
            accent = BORDER
            for keywords, color in accent_map:
                if any(kw in group_text for kw in keywords):
                    accent = color
                    break

            outer, inner = _card(self._scroll_frame, accent)
            outer.pack(fill="x", pady=2)
            self._cards.append(outer)

            for i, line in enumerate(group):
                font = FONT_SMALL
                fg = TEXT_PRIMARY
                if i == 0 and ":" in line:
                    fg = TEXT_HEADING
                    font = FONT_SMALL if not self._large else ("Segoe UI", 11)
                elif ":" in line:
                    fg = TEXT_SECONDARY
                lbl = _label(inner, text=line, fg=fg, font=font)
                lbl.pack(fill="x", anchor="w")

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
