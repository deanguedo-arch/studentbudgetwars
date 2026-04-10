"""Left column — structured life cards with accent borders."""
from __future__ import annotations

import tkinter as tk

from ..theme import (
    BG_CARD, BG_DARK, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    ACCENT_CAREER, ACCENT_EDUCATION, ACCENT_HOUSING, ACCENT_TRANSPORT,
    ACCENT_BUDGET, ACCENT_WEALTH, ACCENT_FOCUS,
    COLOR_ENERGY, COLOR_STRESS, COLOR_NEUTRAL,
    FONT_SUBHEADING, FONT_BODY, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M, CARD_BORDER_W,
)


def _card(parent: tk.Misc, accent: str) -> tuple[tk.Frame, tk.Frame]:
    """Return (outer_frame, inner_frame) for a card with colored left border."""
    outer = tk.Frame(parent, bg=accent, bd=0)
    inner = tk.Frame(outer, bg=BG_ELEVATED, bd=0, padx=PAD_M, pady=PAD_M)
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

    def __init__(self, master: tk.Misc, title: str = "Build", on_action: callable | None = None):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False
        self._on_action = on_action

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

        self._scroll_frame = tk.Frame(self._canvas, bg=BG_CARD)
        self._canvas_window = self._canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        self._scroll_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)

        # We'll store card widgets for dynamic rebuild
        self._cards: list[tk.Frame] = []

    def render(self, lines: list[str]) -> None:
        """Backward-compatible line renderer."""
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

    def render_snapshot(self, snapshot, *, compact: bool = False) -> None:
        """Render a structured build snapshot view-model."""
        for card in self._cards:
            card.destroy()
        self._cards.clear()

        headline = tk.Label(
            self._scroll_frame,
            text=snapshot.headline,
            bg=BG_CARD,
            fg=TEXT_HEADING,
            font=FONT_SUBHEADING if not self._large else ("Segoe UI", 12, "bold"),
            anchor="w",
        )
        headline.pack(fill="x", pady=(0, PAD_S))
        self._cards.append(headline)
        subtitle = tk.Label(
            self._scroll_frame,
            text=snapshot.identity_line or "Build identity and pressure anchors",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_TINY,
            anchor="w",
        )
        subtitle.pack(fill="x", pady=(0, PAD_S))
        self._cards.append(subtitle)

        commitments = list(getattr(snapshot, "persistent_commitments", []) or [])
        if commitments:
            commits_wrap = tk.Frame(self._scroll_frame, bg=BG_CARD)
            commits_wrap.pack(fill="x", pady=(0, PAD_S))
            self._cards.append(commits_wrap)
            tk.Label(
                commits_wrap,
                text="Committed Lanes",
                bg=BG_CARD,
                fg=TEXT_MUTED,
                font=FONT_TINY,
                anchor="w",
            ).pack(fill="x", anchor="w", pady=(0, 2))
            chip_row = tk.Frame(commits_wrap, bg=BG_CARD)
            chip_row.pack(fill="x", anchor="w")
            self._cards.append(chip_row)
            for label in commitments[:4]:
                chip = tk.Label(
                    chip_row,
                    text=label,
                    bg=BG_DARK,
                    fg=TEXT_PRIMARY,
                    font=FONT_TINY,
                    padx=6,
                    pady=2,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                )
                chip.pack(side="left", padx=(0, 4))
                self._cards.append(chip)

        for system in snapshot.systems:
            accent = BORDER
            tone = getattr(system, "tone", "neutral")
            if tone == "career":
                accent = ACCENT_CAREER
            elif tone == "education":
                accent = ACCENT_EDUCATION
            elif tone == "housing":
                accent = ACCENT_HOUSING
            elif tone == "transport":
                accent = ACCENT_TRANSPORT
            elif tone == "budget":
                accent = ACCENT_BUDGET
            elif tone == "wealth":
                accent = ACCENT_WEALTH
            elif tone == "focus":
                accent = ACCENT_FOCUS
            elif tone == "credit":
                accent = COLOR_NEUTRAL

            outer, inner = _card(self._scroll_frame, accent)
            outer.pack(fill="x", pady=2)
            self._cards.append(outer)

            tk.Label(
                inner,
                text=system.system.upper(),
                bg=BG_ELEVATED,
                fg=TEXT_HEADING,
                font=FONT_SMALL if not self._large else ("Segoe UI", 11, "bold"),
                anchor="w",
            ).pack(fill="x")
            tk.Label(
                inner,
                text=system.primary,
                bg=BG_ELEVATED,
                fg=TEXT_PRIMARY,
                font=FONT_SMALL if not self._large else ("Segoe UI", 11),
                anchor="w",
            ).pack(fill="x")
            if system.detail:
                tk.Label(
                    inner,
                    text=system.detail,
                    bg=BG_ELEVATED,
                    fg=TEXT_SECONDARY,
                    font=FONT_TINY if not self._large else ("Segoe UI", 10),
                    anchor="w",
                    wraplength=260 if compact else 280,
                ).pack(fill="x")
            if getattr(system, "progress", None) and (not compact or system.system in {"Career", "Education", "Focus", "Credit"}):
                tk.Label(
                    inner,
                    text=system.progress,
                    bg=BG_ELEVATED,
                    fg=TEXT_MUTED,
                    font=FONT_TINY if not self._large else ("Segoe UI", 10),
                    anchor="w",
                    wraplength=260 if compact else 280,
                ).pack(fill="x")

            action_key = system.system.lower().strip()
            if self._on_action is not None and action_key in {"career", "education", "housing", "transport", "wealth", "focus"}:
                self._bind_click_action(outer, action_key)
                self._bind_click_action(inner, action_key)
                for child in inner.winfo_children():
                    self._bind_click_action(child, action_key)

    def set_large_text(self, enabled: bool) -> None:
        self._large = enabled

    def _on_frame_configure(self, _event=None) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        delta = int(-1 * (event.delta / 120))
        self._canvas.yview_scroll(delta, "units")

    def _bind_mousewheel(self, _event=None) -> None:
        self.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event=None) -> None:
        self.unbind_all("<MouseWheel>")

    def _bind_click_action(self, widget: tk.Widget, action_key: str) -> None:
        widget.configure(cursor="hand2")
        widget.bind("<Button-1>", lambda _e, key=action_key: self._on_action(key))
