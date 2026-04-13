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


def _progress_bar(parent: tk.Misc, fraction: float, color: str) -> tk.Frame:
    return _mini_bar(parent, int(max(0.0, min(1.0, fraction)) * 100), 100, color, width=120)


class FinancePanel(tk.Frame):
    def __init__(self, master: tk.Misc, title: str = "Score & Pressure"):
        super().__init__(master, bg=BG_CARD, bd=1, relief="solid",
                         highlightbackground=BORDER, highlightthickness=1)
        self._large = False

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

    def render_summary(self, summary, delta=None, *, credit_delta: int | None = None, compact: bool = False) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()

        top = tk.Frame(self._content, bg=BG_CARD)
        top.pack(fill="x", pady=(0, PAD_S))
        self._widgets.append(top)

        left = tk.Frame(top, bg=BG_CARD)
        left.pack(side="left" if not compact else "top", fill="y" if not compact else "x", padx=(0, PAD_M) if not compact else (0, 0))
        tk.Label(left, text="RUN DIAGNOSIS", bg=BG_CARD, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(anchor="w")
        tk.Label(
            left,
            text=f"Risk: {summary.biggest_risk}",
            bg=BG_CARD,
            fg=COLOR_WARNING,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=300,
        ).pack(anchor="w", pady=(PAD_S, 0))
        if getattr(summary, "run_killer", ""):
            tk.Label(
                left,
                text=summary.run_killer,
                bg=BG_CARD,
                fg=COLOR_NEGATIVE,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(anchor="w", pady=(1, 0))
        if getattr(summary, "fastest_fix", ""):
            tk.Label(
                left,
                text=summary.fastest_fix,
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(anchor="w")
        if getattr(summary, "recovery_route", None):
            tk.Label(
                left,
                text=summary.recovery_route,
                bg=BG_CARD,
                fg=COLOR_POSITIVE,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(anchor="w", pady=(1, 0))

        commitments = list(getattr(summary, "persistent_commitments", []) or [])
        if commitments:
            commits_wrap = tk.Frame(left, bg=BG_CARD)
            commits_wrap.pack(fill="x", pady=(PAD_S, 0))
            tk.Label(
                commits_wrap,
                text="Committed Lanes",
                bg=BG_CARD,
                fg=TEXT_MUTED,
                font=FONT_TINY,
                anchor="w",
            ).pack(fill="x", anchor="w", pady=(0, 2))

            max_visible = 2 if compact else 4
            visible = commitments[:max_visible]
            chip_grid = tk.Frame(commits_wrap, bg=BG_CARD)
            chip_grid.pack(fill="x", anchor="w")
            for index, label in enumerate(visible):
                chip = tk.Label(
                    chip_grid,
                    text=label,
                    bg=BG_DARK,
                    fg=TEXT_PRIMARY,
                    font=FONT_TINY,
                    padx=6,
                    pady=2,
                    highlightbackground=BORDER,
                    highlightthickness=1,
                )
                chip.grid(
                    row=index // 2,
                    column=index % 2,
                    sticky="w",
                    padx=(0, 4),
                    pady=(0, 2),
                )

            hidden_count = max(0, len(commitments) - max_visible)
            if hidden_count:
                tk.Label(
                    commits_wrap,
                    text=f"+{hidden_count} more",
                    bg=BG_CARD,
                    fg=TEXT_MUTED,
                    font=FONT_TINY,
                    anchor="w",
                ).pack(fill="x", anchor="w", pady=(0, 1))

        if delta is not None:
            delta_color = COLOR_POSITIVE if delta.delta >= 0 else COLOR_NEGATIVE
            tk.Label(
                left,
                text=f"Delta: {delta.delta:+.2f}",
                bg=BG_CARD,
                fg=delta_color,
                font=FONT_SUBHEADING,
                anchor="w",
            ).pack(anchor="w", pady=(PAD_S, 0))
            tk.Label(
                left,
                text=f"Best: {delta.strongest_category}  Worst: {delta.weakest_category}",
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=300,
            ).pack(anchor="w")

        credit_frame = tk.Frame(left, bg=BG_ELEVATED, highlightbackground=BORDER, highlightthickness=2)
        credit_frame.pack(fill="x", pady=(PAD_S, 0))
        tk.Label(credit_frame, text="CREDIT POSITION", bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(
            credit_frame,
            text=f"{summary.credit_score} {summary.credit_tier}",
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            font=FONT_SUBHEADING,
            anchor="w",
        ).pack(fill="x", padx=PAD_S)
        tk.Label(
            credit_frame,
            text=summary.credit_progress_label,
            bg=BG_ELEVATED,
            fg=TEXT_SECONDARY,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=PAD_S)
        tk.Label(
            credit_frame,
            text=summary.credit_progress_detail,
            bg=BG_ELEVATED,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
            anchor="w",
        ).pack(fill="x", padx=PAD_S)
        _progress_bar(credit_frame, summary.credit_progress_fraction, COLOR_WARNING).pack(anchor="w", padx=PAD_S, pady=(PAD_S, 0))
        if credit_delta is not None:
            tk.Label(
                credit_frame,
                text=f"Trend: {credit_delta:+d}",
                bg=BG_ELEVATED,
                fg=COLOR_POSITIVE if credit_delta >= 0 else COLOR_NEGATIVE,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x", padx=PAD_S, pady=(1, PAD_S))

        progress_frame = tk.Frame(left, bg=BG_CARD)
        progress_frame.pack(fill="x", pady=(PAD_S, 0))
        tk.Label(progress_frame, text=summary.progress_label.upper(), bg=BG_CARD, fg=TEXT_HEADING, font=FONT_TINY, anchor="w").pack(fill="x")
        tk.Label(progress_frame, text=summary.progress_detail, bg=BG_CARD, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(fill="x")
        _progress_bar(progress_frame, summary.progress_fraction, COLOR_WARNING).pack(anchor="w", pady=(PAD_S, 0))

        right = tk.Frame(top, bg=BG_CARD)
        right.pack(
            side="left" if not compact else "top",
            fill="both" if not compact else "x",
            expand=not compact,
            pady=(0, 0) if not compact else (PAD_S, 0),
        )
        self._widgets.append(right)

        tk.Label(right, text="Pressure Cards", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SUBHEADING, anchor="w").pack(fill="x")
        primary_row = tk.Frame(right, bg=BG_CARD)
        primary_row.pack(fill="x", pady=(PAD_S, PAD_S))
        for metric in summary.primary_metrics[: (3 if compact else len(summary.primary_metrics))]:
            card = tk.Frame(primary_row, bg=BG_ELEVATED, bd=0, highlightbackground=BORDER, highlightthickness=2)
            card.pack(side="left", fill="both", expand=True, padx=(0, PAD_S))
            tk.Label(card, text=metric.label.upper(), bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
            tk.Label(card, text=metric.primary, bg=BG_ELEVATED, fg=TEXT_PRIMARY, font=FONT_BODY, anchor="w").pack(fill="x", padx=PAD_S, pady=(0, PAD_S))

        progress_card = tk.Frame(right, bg=BG_ELEVATED, highlightbackground=BORDER, highlightthickness=2)
        progress_card.pack(fill="x", pady=(0, PAD_S))
        tk.Label(progress_card, text=summary.progress_label.upper(), bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(progress_card, text=summary.progress_detail, bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_SMALL, anchor="w").pack(fill="x", padx=PAD_S)
        _progress_bar(progress_card, summary.progress_fraction, COLOR_WARNING).pack(anchor="w", padx=PAD_S, pady=(PAD_S, PAD_S))

        secondary = tk.Frame(right, bg=BG_CARD)
        secondary.pack(fill="x", pady=(PAD_S, 0))
        for metric in summary.secondary_metrics[: (4 if compact else 6)]:
            row = tk.Frame(secondary, bg=BG_CARD)
            row.pack(fill="x", pady=1)
            fg = TEXT_SECONDARY
            if metric.tone == "positive":
                fg = COLOR_POSITIVE
            elif metric.tone == "negative":
                fg = COLOR_NEGATIVE
            elif metric.label in {"Stress", "Energy"}:
                fg = COLOR_WARNING
            tk.Label(row, text=f"{metric.label}:", bg=BG_CARD, fg=TEXT_MUTED, font=FONT_TINY, anchor="w", width=16).pack(side="left")
            tk.Label(row, text=metric.primary, bg=BG_CARD, fg=fg, font=FONT_SMALL, anchor="w").pack(side="left")

        if summary.active_modifiers and not compact:
            tk.Label(right, text="Active Modifiers", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", pady=(PAD_S, 0))
            tk.Label(right, text=", ".join(summary.active_modifiers), bg=BG_CARD, fg=TEXT_SECONDARY, font=FONT_SMALL, anchor="w", justify="left", wraplength=320).pack(fill="x")

        if getattr(summary, "blocked_doors", None):
            tk.Label(right, text="Blocked Doors", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", pady=(PAD_S, 0))
            for line in summary.blocked_doors[: (1 if compact else 2)]:
                tk.Label(right, text=line, bg=BG_CARD, fg=COLOR_WARNING, font=FONT_SMALL, anchor="w", justify="left", wraplength=320).pack(fill="x")

        consequence_signals: list[str] = []
        if getattr(summary, "pressure_family", ""):
            consequence_signals.append(f"Pressure family: {summary.pressure_family}")
        if getattr(summary, "month_driver", ""):
            consequence_signals.append(f"Month driver: {summary.month_driver}")
        if getattr(summary, "pending_fallout_count", 0):
            consequence_signals.append(f"Pending fallout: {summary.pending_fallout_count} unresolved consequence(s)")
        if getattr(summary, "pending_decisions", None):
            consequence_signals.extend(summary.pending_decisions[: (1 if compact else 2)])
        if consequence_signals:
            tk.Label(right, text="Consequence Signals", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", pady=(PAD_S, 0))
            for line in consequence_signals:
                line_lower = line.lower()
                line_fg = TEXT_SECONDARY
                if "pending" in line_lower:
                    line_fg = COLOR_WARNING
                elif "driver" in line_lower:
                    line_fg = TEXT_MUTED
                tk.Label(
                    right,
                    text=line,
                    bg=BG_CARD,
                    fg=line_fg,
                    font=FONT_SMALL,
                    anchor="w",
                    justify="left",
                    wraplength=320,
                ).pack(fill="x")

        if summary.crisis_watch:
            tk.Label(right, text="Crisis Watch", bg=BG_CARD, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", pady=(PAD_S, 0))
            for warning in summary.crisis_watch[: (2 if compact else 3)]:
                tk.Label(right, text=warning, bg=BG_CARD, fg=COLOR_WARNING, font=FONT_SMALL, anchor="w", justify="left", wraplength=320).pack(fill="x", anchor="w")

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
