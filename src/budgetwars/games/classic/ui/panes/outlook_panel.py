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

    def render_forecast(self, forecast) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()

        grid = tk.Frame(self._content, bg=BG_CARD)
        grid.pack(fill="x")
        self._widgets.append(grid)

        cards = [
            ("Main Threat", forecast.main_threat, COLOR_NEGATIVE),
            ("Best Opportunity", forecast.best_opportunity, COLOR_POSITIVE),
            ("Chosen Focus", forecast.chosen_focus, ACCENT_FOCUS),
            ("Expected Swing", forecast.expected_swing, TEXT_HEADING),
        ]
        for i, (title, value, accent) in enumerate(cards):
            card = tk.Frame(grid, bg=BG_ELEVATED, highlightbackground=accent, highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=3, pady=3)
            tk.Label(card, text=title, bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x")
            tk.Label(card, text=value, bg=BG_ELEVATED, fg=TEXT_PRIMARY, font=FONT_SMALL if not self._large else ("Segoe UI", 11), anchor="w", justify="left", wraplength=200).pack(fill="x")

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        focus = tk.Label(
            self._content,
            text=forecast.monthly_focus,
            bg=BG_CARD,
            fg=ACCENT_FOCUS,
            font=FONT_SMALL if not self._large else ("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left",
            wraplength=420,
        )
        focus.pack(fill="x", pady=(PAD_S, 0))
        self._widgets.append(focus)

        if forecast.driver_notes:
            notes_header = tk.Label(self._content, text="Why this month matters", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w")
            notes_header.pack(fill="x", pady=(PAD_S, 0))
            self._widgets.append(notes_header)
            for note in forecast.driver_notes[:3]:
                note_lbl = tk.Label(self._content, text=note, bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left", wraplength=420)
                note_lbl.pack(fill="x", anchor="w", pady=1)
                self._widgets.append(note_lbl)

        if forecast.recent_summary:
            recap_header = tk.Label(self._content, text="Last month", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w")
            recap_header.pack(fill="x", pady=(PAD_S, 0))
            self._widgets.append(recap_header)
            for line in forecast.recent_summary[:3]:
                recap = tk.Label(self._content, text=line, bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left", wraplength=420)
                recap.pack(fill="x", anchor="w", pady=1)
                self._widgets.append(recap)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
