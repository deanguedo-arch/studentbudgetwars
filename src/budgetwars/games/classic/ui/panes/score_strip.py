"""Prominent score strip with score delta, risk, and tier progress."""
from __future__ import annotations

import tkinter as tk

from budgetwars.models import LiveScoreSnapshot
from budgetwars.engine.scoring import credit_progress_summary, credit_tier_label

from ..theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_WARNING,
    FONT_SCORE, FONT_SCORE_TIER, FONT_SMALL, FONT_TINY,
    PAD_S, PAD_M,
    tier_color,
)

def _next_tier(score: float) -> tuple[str | None, float | None]:
    if score < 40:
        return "Silver", 40 - score
    if score < 60:
        return "Gold", 60 - score
    if score < 80:
        return "Elite", 80 - score
    return None, None


class ScoreStrip(tk.Frame):
    def __init__(self, master: tk.Misc, on_click=None):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._on_click = on_click

        left = tk.Frame(self, bg=BG_CARD)
        left.pack(side="left", fill="y", padx=PAD_M, pady=PAD_S)

        tk.Label(left, text="SEASON SCORE", bg=BG_CARD, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(anchor="w")

        self._score_label = tk.Label(left, text="0.0", bg=BG_CARD, fg=TEXT_HEADING,
                                     font=FONT_SCORE, anchor="w")
        self._score_label.pack(side="left")
        self._tier_label = tk.Label(left, text="Bronze", bg=BG_CARD, fg=TEXT_SECONDARY,
                                    font=FONT_SCORE_TIER, anchor="w", padx=PAD_S)
        self._tier_label.pack(side="left")

        self._detail_frame = tk.Frame(left, bg=BG_CARD)
        self._detail_frame.pack(fill="x", pady=(PAD_S, 0))
        self._delta_label = tk.Label(self._detail_frame, text="", bg=BG_CARD, fg=TEXT_SECONDARY,
                                     font=FONT_SMALL, anchor="w")
        self._delta_label.pack(side="left")
        self._category_label = tk.Label(self._detail_frame, text="", bg=BG_CARD, fg=TEXT_SECONDARY,
                                        font=FONT_SMALL, anchor="w", padx=PAD_S)
        self._category_label.pack(side="left")
        self._tier_progress_label = tk.Label(self._detail_frame, text="", bg=BG_CARD, fg=TEXT_MUTED,
                                             font=FONT_SMALL, anchor="w", padx=PAD_S)
        self._tier_progress_label.pack(side="left")
        self._credit_label = tk.Label(self._detail_frame, text="", bg=BG_CARD, fg=TEXT_SECONDARY,
                                      font=FONT_SMALL, anchor="w", padx=PAD_S)
        self._credit_label.pack(side="left")

        # Risk label
        self._risk_label = tk.Label(self, text="", bg=BG_CARD, fg=COLOR_WARNING,
                                    font=FONT_SMALL, anchor="w", wraplength=620, justify="left")
        self._risk_label.pack(side="left", fill="both", expand=True, padx=PAD_M)
        self._flash_job: str | None = None

        if on_click:
            for widget in [self, self._score_label, self._tier_label, self._risk_label]:
                widget.bind("<Button-1>", lambda e: on_click())
                widget.configure(cursor="hand2")

    def render(self, snapshot: LiveScoreSnapshot, delta=None, *, credit_score: int | None = None, credit_delta: int | None = None) -> None:
        tc = tier_color(snapshot.score_tier)
        self._score_label.configure(text=f"{snapshot.projected_score:.1f}", fg=tc)
        self._tier_label.configure(text=snapshot.score_tier, fg=tc)
        self._risk_label.configure(text=snapshot.biggest_risk)

        if delta is not None:
            delta_fg = "#48d878" if delta.delta >= 0 else "#e85050"
            self._delta_label.configure(text=f"Delta {delta.delta:+.2f}", fg=delta_fg)
            self._category_label.configure(
                text=f"Best {delta.strongest_category} | Weakest {delta.weakest_category}",
                fg=TEXT_SECONDARY,
            )
        else:
            self._delta_label.configure(text="")
            self._category_label.configure(text="")

        next_tier, points = _next_tier(snapshot.projected_score)
        if next_tier is None:
            self._tier_progress_label.configure(text="Top tier reached", fg=TEXT_MUTED)
        else:
            self._tier_progress_label.configure(text=f"{points:.1f} to {next_tier}", fg=TEXT_MUTED)
        if credit_score is not None:
            credit_label = credit_tier_label(credit_score)
            credit_progress_label, credit_progress_detail, _ = credit_progress_summary(credit_score)
            credit_text = f"Credit {credit_score} {credit_label} | {credit_progress_label}: {credit_progress_detail}"
            if credit_delta is not None:
                credit_text += f" | Trend {credit_delta:+d}"
            self._credit_label.configure(text=credit_text, fg=TEXT_SECONDARY)
        else:
            self._credit_label.configure(text="")

        if delta is not None and abs(delta.delta) >= 0.25:
            self._flash(delta.delta)

    def set_large_text(self, enabled: bool) -> None:
        pass  # Score strip stays fixed size

    def _flash(self, delta: float) -> None:
        if self._flash_job is not None:
            try:
                self.after_cancel(self._flash_job)
            except tk.TclError:
                pass
        flash_color = "#284032" if delta >= 0 else "#4a2222"
        self.configure(highlightbackground=flash_color)

        def _reset() -> None:
            self.configure(highlightbackground=BORDER)
            self._flash_job = None

        self._flash_job = self.after(180, _reset)
