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


def _progress_bar(parent: tk.Misc, fraction: float) -> tk.Frame:
    frame = tk.Frame(parent, bg=BG_ELEVATED)
    canvas = tk.Canvas(frame, width=140, height=10, bg=BG_DARK, bd=0, highlightthickness=0)
    canvas.pack(side="left")
    fill = max(0, min(140, int(140 * max(0.0, min(1.0, fraction)))))
    canvas.create_rectangle(0, 0, 140, 10, fill=BG_DARK, outline="")
    canvas.create_rectangle(0, 0, fill, 10, fill=ACCENT_FOCUS, outline="")
    return frame


class OutlookPanel(tk.Frame):
    """Focus + pressure + driver notes + last-month recap."""

    def __init__(self, master: tk.Misc, title: str = "This Month", resolve_callback=None):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False
        self._resolve_callback = resolve_callback

        header = tk.Label(self, text=f"  {title}  ", bg=BG_CARD, fg=TEXT_HEADING,
                          font=FONT_SUBHEADING, anchor="w")
        header.pack(fill="x", padx=PAD_S, pady=(PAD_S, 2))

        scroll_host = tk.Frame(self, bg=BG_CARD)
        scroll_host.pack(fill="both", expand=True, padx=PAD_S, pady=PAD_S)
        self._canvas = tk.Canvas(scroll_host, bg=BG_CARD, highlightthickness=0, bd=0)
        self._scrollbar = tk.Scrollbar(scroll_host, orient="vertical", command=self._canvas.yview)
        self._content = tk.Frame(self._canvas, bg=BG_CARD)
        self._content.bind("<Configure>", lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._content_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfigure(self._content_window, width=e.width))
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")
        self._bind_mousewheel()

        self._widgets: list[tk.Widget] = []

    def _bind_mousewheel(self) -> None:
        def _on_mousewheel(event):
            delta = 0
            if hasattr(event, "delta") and event.delta:
                delta = -1 if event.delta > 0 else 1
            elif getattr(event, "num", None) == 4:
                delta = -1
            elif getattr(event, "num", None) == 5:
                delta = 1
            if delta:
                self._canvas.yview_scroll(delta, "units")

        self._canvas.bind("<MouseWheel>", _on_mousewheel)
        self._content.bind("<MouseWheel>", _on_mousewheel)
        self._canvas.bind("<Button-4>", _on_mousewheel)
        self._canvas.bind("<Button-5>", _on_mousewheel)
        self._content.bind("<Button-4>", _on_mousewheel)
        self._content.bind("<Button-5>", _on_mousewheel)

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

    def render_forecast(self, forecast, *, compact: bool = False, show_resolve_button: bool = True) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()

        grid = tk.Frame(self._content, bg=BG_CARD)
        grid.pack(fill="x")
        self._widgets.append(grid)

        cards = [
            ("Main Threat", forecast.main_threat, COLOR_NEGATIVE),
            ("Best Opportunity", forecast.best_opportunity, COLOR_POSITIVE),
            ("Chosen Play", forecast.chosen_focus, ACCENT_FOCUS),
            ("Expected Swing", forecast.expected_swing, TEXT_HEADING),
        ]
        for i, (title, value, accent) in enumerate(cards):
            card = tk.Frame(grid, bg=BG_ELEVATED, highlightbackground=accent, highlightthickness=2)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=3, pady=3)
            tk.Label(card, text=title.upper(), bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
            tk.Label(card, text=value, bg=BG_ELEVATED, fg=TEXT_PRIMARY, font=FONT_SMALL if not self._large else ("Trebuchet MS", 11), anchor="w", justify="left", wraplength=180 if compact else 200).pack(fill="x", padx=PAD_S, pady=(2, PAD_S))

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        progress = tk.Frame(self._content, bg=BG_ELEVATED, highlightbackground=ACCENT_FOCUS, highlightthickness=2)
        progress.pack(fill="x", pady=(PAD_S, 0))
        self._widgets.append(progress)
        tk.Label(progress, text=forecast.progress_label.upper(), bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(progress, text=forecast.progress_detail, bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", padx=PAD_S)
        _progress_bar(progress, forecast.progress_fraction).pack(anchor="w", padx=PAD_S, pady=(PAD_S, PAD_S))

        focus_frame = tk.Frame(self._content, bg=BG_CARD)
        focus_frame.pack(fill="x", pady=(PAD_S, 0))
        self._widgets.append(focus_frame)
        tk.Label(
            focus_frame,
            text=f"SITUATION FAMILY  {forecast.situation_family}",
            bg=BG_CARD,
            fg=TEXT_HEADING,
            font=FONT_SMALL if not self._large else ("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            focus_frame,
            text=forecast.credit_status,
            bg=BG_CARD,
            fg=ACCENT_FOCUS,
            font=FONT_SMALL if not self._large else ("Segoe UI", 11),
            anchor="w",
            wraplength=420,
            justify="left",
        ).pack(fill="x", pady=(1, 0))
        if getattr(forecast, "recovery_route", None):
            tk.Label(
                focus_frame,
                text=forecast.recovery_route,
                bg=BG_CARD,
                fg=COLOR_POSITIVE,
                font=FONT_SMALL if not self._large else ("Segoe UI", 11),
                anchor="w",
                wraplength=420,
                justify="left",
            ).pack(fill="x", pady=(2, 0))
        if getattr(forecast, "blocked_doors", None):
            tk.Label(
                focus_frame,
                text="Blocked doors: " + " | ".join(forecast.blocked_doors[: (1 if compact else 2)]),
                bg=BG_CARD,
                fg=COLOR_WARNING,
                font=FONT_SMALL if not self._large else ("Segoe UI", 11),
                anchor="w",
                wraplength=420,
                justify="left",
            ).pack(fill="x", pady=(2, 0))

        resolve_frame = tk.Frame(self._content, bg=BG_ELEVATED, highlightbackground=ACCENT_FOCUS, highlightthickness=2)
        resolve_frame.pack(fill="x", pady=(PAD_S, 0))
        self._widgets.append(resolve_frame)
        tk.Label(
            resolve_frame,
            text="COMMIT THE MONTH",
            bg=BG_ELEVATED,
            fg=TEXT_HEADING,
            font=FONT_TINY,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(
            resolve_frame,
            text="Lock the play once the threat, edge, and swing make sense.",
            bg=BG_ELEVATED,
            fg=TEXT_SECONDARY,
            font=FONT_TINY if not self._large else ("Segoe UI", 10),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S // 2))
        if show_resolve_button:
            resolve_btn = tk.Button(
                resolve_frame,
                text="Resolve Month",
                command=self._resolve_callback,
                bg="#60451f",
                fg=ACCENT_FOCUS,
                activebackground="#75572a",
                activeforeground="#fff8d0",
                relief="flat",
                bd=0,
                font=FONT_SUBHEADING if not self._large else ("Segoe UI", 11, "bold"),
                padx=PAD_M,
                pady=PAD_S,
                cursor="hand2",
                highlightbackground=ACCENT_FOCUS,
                highlightthickness=2,
            )
            resolve_btn.pack(fill="x", padx=PAD_S, pady=(0, PAD_S))
        else:
            tk.Label(
                resolve_frame,
                text="Use the bottom Resolve Month control to lock the turn.",
                bg=BG_ELEVATED,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL if not self._large else ("Trebuchet MS", 11),
                anchor="w",
                justify="left",
                wraplength=420,
            ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S))

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
            for note in forecast.driver_notes[: (2 if compact else 3)]:
                note_lbl = tk.Label(self._content, text=note, bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left", wraplength=420)
                note_lbl.pack(fill="x", anchor="w", pady=1)
                self._widgets.append(note_lbl)

        if forecast.recent_summary and not compact:
            recap_header = tk.Label(self._content, text="Last month", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w")
            recap_header.pack(fill="x", pady=(PAD_S, 0))
            self._widgets.append(recap_header)
            for line in forecast.recent_summary[:3]:
                recap = tk.Label(self._content, text=line, bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left", wraplength=420)
                recap.pack(fill="x", anchor="w", pady=1)
                self._widgets.append(recap)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled
