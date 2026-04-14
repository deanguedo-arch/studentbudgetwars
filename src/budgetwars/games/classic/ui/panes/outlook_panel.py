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

        viewport = tk.Frame(self, bg=BG_CARD)
        viewport.pack(fill="both", expand=True, padx=PAD_S, pady=PAD_S)
        self._canvas = tk.Canvas(viewport, bg=BG_CARD, bd=0, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(viewport, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        self._scrollbar.pack(side="right", fill="y")

        self._content = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._content, anchor="nw")
        self._content.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

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

    def render_forecast(self, forecast, *, compact: bool = False, show_resolve_button: bool = True) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()

        hero_arc = forecast.active_status_arcs[0] if getattr(forecast, "active_status_arcs", None) else None
        if hero_arc is not None:
            hero = tk.Frame(
                self._content,
                bg=BG_ELEVATED,
                highlightbackground=COLOR_WARNING if hero_arc.tone == "negative" else ACCENT_FOCUS,
                highlightthickness=2,
            )
            hero.pack(fill="x", pady=(0, PAD_S))
            self._widgets.append(hero)
            tk.Label(hero, text="ACTIVE ARC", bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(
                fill="x", padx=PAD_S, pady=(PAD_S, 0)
            )
            tk.Label(
                hero,
                text=f"{hero_arc.name} | S{hero_arc.severity} | {hero_arc.months_remaining} mo",
                bg=BG_ELEVATED,
                fg=COLOR_WARNING if hero_arc.tone == "negative" else TEXT_HEADING,
                font=FONT_SMALL if not self._large else ("Trebuchet MS", 11, "bold"),
                anchor="w",
                justify="left",
                wraplength=420,
            ).pack(fill="x", padx=PAD_S, pady=(2, 0))
            tk.Label(
                hero,
                text=hero_arc.summary,
                bg=BG_ELEVATED,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL if not self._large else ("Trebuchet MS", 11),
                anchor="w",
                justify="left",
                wraplength=420,
            ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S // 2))
            if hero_arc.resolution_hint:
                tk.Label(
                    hero,
                    text=hero_arc.resolution_hint,
                    bg=BG_ELEVATED,
                    fg=TEXT_SECONDARY,
                    font=FONT_TINY,
                    anchor="w",
                    justify="left",
                    wraplength=420,
                ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S))

        play_card = tk.Frame(self._content, bg=BG_ELEVATED, highlightbackground=ACCENT_FOCUS, highlightthickness=3)
        play_card.pack(fill="x", pady=(PAD_S if hero_arc is not None else 0, 0))
        self._widgets.append(play_card)
        tk.Label(play_card, text="THIS MONTH'S PLAY", bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(
            fill="x", padx=PAD_S, pady=(PAD_S, 0)
        )
        tk.Label(
            play_card,
            text=forecast.chosen_focus,
            bg=BG_ELEVATED,
            fg=ACCENT_FOCUS,
            font=("Trebuchet MS", 12 if not self._large else 13, "bold"),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=PAD_S, pady=(2, 0))
        tk.Label(
            play_card,
            text=forecast.monthly_focus,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            font=FONT_SMALL if not self._large else ("Trebuchet MS", 11),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S // 2))
        tk.Label(
            play_card,
            text=forecast.expected_swing,
            bg=BG_ELEVATED,
            fg=TEXT_HEADING,
            font=FONT_SMALL if not self._large else ("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left",
            wraplength=420,
        ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S // 2))
        tk.Label(
            play_card,
            text="COMMIT",
            bg=BG_ELEVATED,
            fg=TEXT_HEADING,
            font=FONT_TINY,
            anchor="w",
            justify="left",
        ).pack(fill="x", padx=PAD_S, pady=(0, 0))
        tk.Label(
            play_card,
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
                play_card,
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
                play_card,
                text="Use the bottom Resolve Month control to lock the turn.",
                bg=BG_ELEVATED,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL if not self._large else ("Trebuchet MS", 11),
                anchor="w",
                justify="left",
                wraplength=420,
            ).pack(fill="x", padx=PAD_S, pady=(0, PAD_S))

        grid = tk.Frame(self._content, bg=BG_CARD)
        grid.pack(fill="x", pady=(PAD_S, 0))
        self._widgets.append(grid)
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        for col, (title, value, accent) in enumerate(
            (
                ("Main Threat", forecast.main_threat, COLOR_NEGATIVE),
                ("Best Opportunity", forecast.best_opportunity, COLOR_POSITIVE),
            )
        ):
            card = tk.Frame(grid, bg=BG_ELEVATED, highlightbackground=accent, highlightthickness=2)
            card.grid(row=0, column=col, sticky="nsew", padx=3, pady=3)
            tk.Label(card, text=title.upper(), bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(
                fill="x", padx=PAD_S, pady=(PAD_S, 0)
            )
            tk.Label(
                card,
                text=value,
                bg=BG_ELEVATED,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL if not self._large else ("Trebuchet MS", 11),
                anchor="w",
                justify="left",
                wraplength=180 if compact else 200,
            ).pack(fill="x", padx=PAD_S, pady=(2, PAD_S))

        if forecast.driver_notes:
            notes_header = tk.Label(self._content, text="Why the turn matters", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w")
            notes_header.pack(fill="x", pady=(PAD_S, 0))
            self._widgets.append(notes_header)
            for note in forecast.driver_notes[:2]:
                note_lbl = tk.Label(
                    self._content,
                    text=note,
                    bg=BG_CARD,
                    fg=TEXT_SECONDARY,
                    font=FONT_SMALL,
                    anchor="w",
                    justify="left",
                    wraplength=420,
                )
                note_lbl.pack(fill="x", anchor="w", pady=1)
                self._widgets.append(note_lbl)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled

    def _on_frame_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scrollbar_visibility()

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfigure(self._canvas_window, width=event.width)
        self._update_scrollbar_visibility()

    def _on_mousewheel(self, event) -> None:
        delta = int(-1 * (event.delta / 120))
        self._canvas.yview_scroll(delta, "units")

    def _bind_mousewheel(self, _event=None) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None) -> None:
        self.unbind_all("<MouseWheel>")

    def _update_scrollbar_visibility(self) -> None:
        bbox = self._canvas.bbox("all")
        if not bbox:
            self._scrollbar.pack_forget()
            return
        content_height = bbox[3] - bbox[1]
        viewport_height = max(1, self._canvas.winfo_height())
        if content_height > viewport_height + 4:
            if not self._scrollbar.winfo_ismapped():
                self._scrollbar.pack(side="right", fill="y")
        else:
            if self._scrollbar.winfo_ismapped():
                self._scrollbar.pack_forget()
