"""Custom dark-themed modal popups for milestones, end-game, and events."""
from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog

from ..theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BG_ELEVATED, BORDER,
    TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING,
    FONT_HEADING, FONT_HEADING_LG, FONT_BODY, FONT_SMALL, FONT_MONO,
    FONT_SCORE, FONT_SCORE_TIER, FONT_SUBHEADING,
    PAD_S, PAD_M, PAD_L, PAD_XL,
    tier_color,
)

_BAR_COLORS = {
    "net_worth": "#48d878",
    "monthly_surplus": "#60b0f0",
    "debt_ratio": "#e85050",
    "career_tier": "#f0a030",
    "credentials_education": "#4ea8de",
    "housing_stability": "#48b880",
    "life_satisfaction": "#60b0f0",
    "stress_burnout": "#e87040",
}

_BAR_LABELS = {
    "net_worth": "Net Worth",
    "monthly_surplus": "Cash Flow",
    "debt_ratio": "Debt Ratio",
    "career_tier": "Career",
    "credentials_education": "Education",
    "housing_stability": "Housing",
    "life_satisfaction": "Life",
    "stress_burnout": "Wellness",
}


def preview_choice_detail(detail: str, stat_effects: dict[str, float] | None = None) -> str:
    effects = stat_effects or {}
    if not effects:
        return detail
    pieces: list[str] = []
    for key in ("cash", "savings", "debt", "stress", "energy", "life_satisfaction", "family_support", "social_stability", "credit_score"):
        if key not in effects:
            continue
        value = effects[key]
        if value == 0:
            continue
        if key == "credit_score":
            pieces.append(f"credit {value:+.0f}")
        else:
            pieces.append(f"{key.replace('_', ' ')} {value:+.0f}")
    if not pieces:
        return detail
    return f"{detail} Likely changes: {', '.join(pieces)}."


class _DarkDialog(tk.Toplevel):
    """Base class for dark-themed modal dialogs."""

    def __init__(self, parent: tk.Misc, title: str, width: int = 500, height: int = 400):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG_DARKEST)
        self._center_over_parent(parent, width, height)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self._content = tk.Frame(self, bg=BG_DARKEST, padx=PAD_XL, pady=PAD_L)
        self._content.pack(fill="both", expand=True)

        self._button_frame = tk.Frame(self, bg=BG_DARKEST)
        self._button_frame.pack(fill="x", padx=PAD_XL, pady=(0, PAD_L))

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Return>", lambda e: self._close())
        self.bind("<Escape>", lambda e: self._close())

    def _close(self) -> None:
        self.grab_release()
        self.destroy()

    def _center_over_parent(self, parent: tk.Misc, width: int, height: int) -> None:
        self.update_idletasks()
        try:
            parent.update_idletasks()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
        except tk.TclError:
            px = py = 0
            pw = self.winfo_screenwidth()
            ph = self.winfo_screenheight()

        if pw <= 1 or ph <= 1:
            pw = self.winfo_screenwidth()
            ph = self.winfo_screenheight()
            px = py = 0

        x = px + max(0, (pw - width) // 2)
        y = py + max(0, (ph - height) // 2)
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, min(x, screen_w - width))
        y = max(0, min(y, screen_h - height))
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _add_ok_button(self) -> None:
        btn = tk.Button(
            self._button_frame, text="OK", command=self._close,
            bg=BG_ELEVATED, fg=TEXT_PRIMARY, activebackground=BG_DARK,
            font=FONT_BODY, relief="flat", bd=0, padx=PAD_XL, pady=PAD_S,
            cursor="hand2", highlightbackground=BORDER, highlightthickness=1,
        )
        btn.pack(side="right")


def show_event_choice_popup(
    parent: tk.Misc,
    *,
    title: str,
    prompt: str,
    choices: list[tuple[str, str, str] | tuple[str, str, str, dict[str, float]]],
) -> str | None:
    """Show a modal dialog with 2-3 choices and return the chosen choice_id."""
    if not choices:
        return None

    dialog = _DarkDialog(parent, title, width=560, height=420)
    dialog.result: str | None = None  # type: ignore[attr-defined]

    tk.Label(dialog._content, text=title, bg=BG_DARKEST, fg=TEXT_HEADING, font=FONT_HEADING_LG).pack(
        anchor="w", pady=(0, PAD_S)
    )
    tk.Label(
        dialog._content,
        text=prompt,
        bg=BG_DARKEST,
        fg=TEXT_PRIMARY,
        font=FONT_BODY,
        wraplength=500,
        justify="left",
        anchor="w",
    ).pack(fill="x", pady=(0, PAD_M))

    for choice in choices[:3]:
        if len(choice) == 4:
            label, choice_id, detail, stat_effects = choice
            detail = preview_choice_detail(detail, stat_effects)
        else:
            label, choice_id, detail = choice

        def _choose(_choice_id: str = choice_id) -> None:
            dialog.result = _choice_id  # type: ignore[attr-defined]
            dialog._close()

        card = tk.Frame(dialog._content, bg=BG_ELEVATED, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x", pady=4)
        card.configure(cursor="hand2")
        title_label = tk.Label(card, text=label, bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_SUBHEADING, anchor="w", cursor="hand2")
        title_label.pack(
            fill="x", padx=PAD_M, pady=(PAD_S, 0)
        )
        detail_label: tk.Label | None = None
        if detail:
            detail_label = tk.Label(
                card,
                text=detail,
                bg=BG_ELEVATED,
                fg=TEXT_SECONDARY,
                font=FONT_SMALL,
                wraplength=500,
                justify="left",
                anchor="w",
                cursor="hand2",
            )
            detail_label.pack(fill="x", padx=PAD_M, pady=(2, PAD_S))

        card.bind("<Button-1>", lambda _event, fn=_choose: fn())
        title_label.bind("<Button-1>", lambda _event, fn=_choose: fn())
        if detail_label is not None:
            detail_label.bind("<Button-1>", lambda _event, fn=_choose: fn())

        btn = tk.Button(
            dialog._button_frame,
            text=label,
            command=_choose,
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            activebackground=BG_DARK,
            font=FONT_BODY,
            relief="flat",
            bd=0,
            padx=PAD_L,
            pady=PAD_S,
            cursor="hand2",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        btn.pack(side="left", padx=(0, PAD_S))

    cancel = tk.Button(
        dialog._button_frame,
        text="Cancel",
        command=dialog._close,
        bg=BG_DARK,
        fg=TEXT_SECONDARY,
        activebackground=BG_ELEVATED,
        font=FONT_BODY,
        relief="flat",
        bd=0,
        padx=PAD_L,
        pady=PAD_S,
        cursor="hand2",
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    cancel.pack(side="right")

    dialog.wait_window()
    return getattr(dialog, "result", None)


def show_milestone_popup(parent: tk.Misc, summary_lines: list[str]) -> None:
    """Show annual milestone in a styled dark modal."""
    dialog = _DarkDialog(parent, "Annual Milestone", width=460, height=300)

    tk.Label(dialog._content, text="Year Complete", bg=BG_DARKEST,
             fg=TEXT_HEADING, font=FONT_HEADING_LG).pack(anchor="w", pady=(0, PAD_M))

    for line in summary_lines:
        fg = TEXT_PRIMARY
        lower = line.lower()
        if "net worth" in lower:
            fg = COLOR_POSITIVE if "+" in line else COLOR_NEGATIVE
        elif "stress" in lower:
            fg = COLOR_WARNING

        tk.Label(dialog._content, text=line, bg=BG_DARKEST, fg=fg,
                 font=FONT_BODY, anchor="w", justify="left"
                 ).pack(fill="x", anchor="w", pady=1)

    dialog._add_ok_button()
    dialog.wait_window()


def show_endgame_popup(
    parent: tk.Misc,
    ending_label: str,
    outcome: str,
    final_score: float,
    breakdown: dict[str, float],
) -> None:
    """Show end-of-game results in a full styled dark modal."""
    tier = "Elite" if final_score >= 80 else "Gold" if final_score >= 60 else "Silver" if final_score >= 40 else "Bronze"
    tc = tier_color(tier)

    dialog = _DarkDialog(parent, "Life Position", width=520, height=480)

    # Title
    tk.Label(dialog._content, text=ending_label, bg=BG_DARKEST,
             fg=tc, font=FONT_HEADING_LG).pack(anchor="w", pady=(0, PAD_S))

    # Score
    score_frame = tk.Frame(dialog._content, bg=BG_DARKEST)
    score_frame.pack(fill="x", pady=PAD_S)
    tk.Label(score_frame, text=f"{final_score:.1f}", bg=BG_DARKEST,
             fg=tc, font=FONT_SCORE).pack(side="left")
    tk.Label(score_frame, text=tier, bg=BG_DARKEST,
             fg=tc, font=FONT_SCORE_TIER).pack(side="left", padx=PAD_M)

    # Outcome
    tk.Label(dialog._content, text=outcome, bg=BG_DARKEST, fg=TEXT_PRIMARY,
             font=FONT_BODY, wraplength=460, justify="left", anchor="w"
             ).pack(fill="x", pady=PAD_M)

    # Breakdown bars
    tk.Label(dialog._content, text="Category Breakdown", bg=BG_DARKEST,
             fg=TEXT_HEADING, font=FONT_SUBHEADING).pack(anchor="w", pady=(PAD_S, PAD_S))

    for key, value in breakdown.items():
        row = tk.Frame(dialog._content, bg=BG_DARKEST)
        row.pack(fill="x", pady=2)
        label = _BAR_LABELS.get(key, key.replace("_", " ").title())
        tk.Label(row, text=label, bg=BG_DARKEST, fg=TEXT_SECONDARY,
                 font=FONT_SMALL, width=12, anchor="w").pack(side="left")
        bar_color = _BAR_COLORS.get(key, TEXT_SECONDARY)
        canvas = tk.Canvas(row, width=200, height=12, bg=BG_DARK, bd=0, highlightthickness=0)
        canvas.pack(side="left", padx=PAD_S)
        fill_w = max(0, min(200, int(200 * value / 100)))
        canvas.create_rectangle(0, 0, fill_w, 12, fill=bar_color, outline="")
        tk.Label(row, text=f"{value:.1f}", bg=BG_DARKEST, fg=TEXT_MUTED,
                 font=FONT_SMALL).pack(side="left", padx=PAD_S)

    dialog._add_ok_button()
    dialog.wait_window()
