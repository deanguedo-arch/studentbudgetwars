"""Prominent score strip with tier badge and category breakdown mini-bars."""
from __future__ import annotations

import tkinter as tk

from budgetwars.models import LiveScoreSnapshot

from ..theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_WARNING,
    FONT_SCORE, FONT_SCORE_TIER, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M,
    tier_color,
)

_CATEGORY_COLORS = {
    "net_worth": "#48d878",
    "monthly_surplus": "#60b0f0",
    "debt_ratio": "#e85050",
    "career_tier": "#f0a030",
    "credentials_education": "#4ea8de",
    "housing_stability": "#48b880",
    "life_satisfaction": "#60b0f0",
    "stress_burnout": "#e87040",
}

_CATEGORY_LABELS = {
    "net_worth": "Net Worth",
    "monthly_surplus": "Cash Flow",
    "debt_ratio": "Debt",
    "career_tier": "Career",
    "credentials_education": "Education",
    "housing_stability": "Housing",
    "life_satisfaction": "Life",
    "stress_burnout": "Wellness",
}


class ScoreStrip(tk.Frame):
    def __init__(self, master: tk.Misc, on_click=None):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._on_click = on_click

        left = tk.Frame(self, bg=BG_CARD)
        left.pack(side="left", fill="y", padx=PAD_M, pady=PAD_S)

        self._score_label = tk.Label(left, text="0.0", bg=BG_CARD, fg=TEXT_HEADING,
                                     font=FONT_SCORE, anchor="w")
        self._score_label.pack(side="left")
        self._tier_label = tk.Label(left, text="Bronze", bg=BG_CARD, fg=TEXT_SECONDARY,
                                    font=FONT_SCORE_TIER, anchor="w", padx=PAD_S)
        self._tier_label.pack(side="left")

        # Risk label
        self._risk_label = tk.Label(self, text="", bg=BG_CARD, fg=COLOR_WARNING,
                                    font=FONT_SMALL, anchor="w", wraplength=300, justify="left")
        self._risk_label.pack(side="left", fill="both", expand=True, padx=PAD_M)

        # Category mini-bars on the right
        self._bars_frame = tk.Frame(self, bg=BG_CARD)
        self._bars_frame.pack(side="right", fill="y", padx=PAD_M, pady=PAD_S)
        self._bar_canvases: dict[str, tk.Canvas] = {}
        self._bar_labels: dict[str, tk.Label] = {}

        for i, (key, label) in enumerate(_CATEGORY_LABELS.items()):
            row_frame = tk.Frame(self._bars_frame, bg=BG_CARD)
            row_frame.grid(row=i // 4, column=(i % 4) * 2, padx=(0, 2), pady=1, sticky="w")
            lbl = tk.Label(row_frame, text=label, bg=BG_CARD, fg=TEXT_MUTED,
                           font=FONT_TINY, anchor="w", width=8)
            lbl.pack(side="left")
            canvas = tk.Canvas(row_frame, width=40, height=6, bg=BG_DARKEST,
                               bd=0, highlightthickness=0)
            canvas.pack(side="left", padx=(2, 0))
            self._bar_canvases[key] = canvas
            self._bar_labels[key] = lbl

        if on_click:
            for widget in [self, self._score_label, self._tier_label, self._risk_label]:
                widget.bind("<Button-1>", lambda e: on_click())
                widget.configure(cursor="hand2")

    def render(self, snapshot: LiveScoreSnapshot) -> None:
        tc = tier_color(snapshot.score_tier)
        self._score_label.configure(text=f"{snapshot.projected_score:.1f}", fg=tc)
        self._tier_label.configure(text=snapshot.score_tier, fg=tc)
        self._risk_label.configure(text=snapshot.biggest_risk)

        for key, canvas in self._bar_canvases.items():
            canvas.delete("all")
            value = snapshot.breakdown.get(key, 0)
            fill_w = max(0, min(40, int(40 * value / 100)))
            color = _CATEGORY_COLORS.get(key, TEXT_SECONDARY)
            canvas.create_rectangle(0, 0, fill_w, 6, fill=color, outline="")

    def set_large_text(self, enabled: bool) -> None:
        pass  # Score strip stays fixed size
