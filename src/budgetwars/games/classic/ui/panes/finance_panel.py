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

        body = tk.Frame(self._content, bg=BG_CARD)
        body.pack(fill="x", pady=(0, PAD_S))
        self._widgets.append(body)

        tk.Label(body, text="RUN DIAGNOSIS", bg=BG_CARD, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", anchor="w")
        tk.Label(
            body,
            text=f"Risk: {summary.biggest_risk}",
            bg=BG_CARD,
            fg=COLOR_WARNING,
            font=FONT_SMALL if not self._large else ("Segoe UI", 11, "bold"),
            anchor="w",
            justify="left",
            wraplength=320,
        ).pack(fill="x", anchor="w", pady=(PAD_S, 0))
        if getattr(summary, "run_killer", ""):
            tk.Label(
                body,
                text=summary.run_killer,
                bg=BG_CARD,
                fg=COLOR_NEGATIVE,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=320,
            ).pack(fill="x", anchor="w", pady=(1, 0))
        if getattr(summary, "fastest_fix", ""):
            tk.Label(
                body,
                text=summary.fastest_fix,
                bg=BG_CARD,
                fg=TEXT_SECONDARY,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=320,
            ).pack(fill="x", anchor="w")
        if getattr(summary, "recovery_route", None):
            tk.Label(
                body,
                text=summary.recovery_route,
                bg=BG_CARD,
                fg=COLOR_POSITIVE,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=320,
            ).pack(fill="x", anchor="w", pady=(1, 0))

        rank_card = tk.Frame(body, bg=BG_ELEVATED, highlightbackground=BORDER, highlightthickness=2)
        rank_card.pack(fill="x", pady=(PAD_S, 0))
        tk.Label(rank_card, text="NEXT RANK", bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(
            rank_card,
            text=summary.progress_label,
            bg=BG_ELEVATED,
            fg=TEXT_HEADING,
            font=FONT_SUBHEADING,
            anchor="w",
        ).pack(fill="x", padx=PAD_S)
        tk.Label(
            rank_card,
            text=summary.progress_detail,
            bg=BG_ELEVATED,
            fg=TEXT_SECONDARY,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=320,
        ).pack(fill="x", padx=PAD_S)
        if delta is not None:
            delta_color = COLOR_POSITIVE if delta.delta >= 0 else COLOR_NEGATIVE
            tk.Label(
                rank_card,
                text=f"Delta {delta.delta:+.2f} | Best {delta.strongest_category} | Worst {delta.weakest_category}",
                bg=BG_ELEVATED,
                fg=delta_color,
                font=FONT_SMALL,
                anchor="w",
                justify="left",
                wraplength=320,
            ).pack(fill="x", padx=PAD_S, pady=(2, PAD_S))
        else:
            tk.Label(
                rank_card,
                text=f"Projected score {summary.projected_score:.1f} | {summary.score_tier}",
                bg=BG_ELEVATED,
                fg=TEXT_SECONDARY,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x", padx=PAD_S, pady=(2, PAD_S))

        access_card = tk.Frame(body, bg=BG_ELEVATED, highlightbackground=BORDER, highlightthickness=2)
        access_card.pack(fill="x", pady=(PAD_S, 0))
        tk.Label(access_card, text="ACCESS", bg=BG_ELEVATED, fg=TEXT_MUTED, font=FONT_TINY, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
        tk.Label(
            access_card,
            text=f"{summary.credit_score} {summary.credit_tier}",
            bg=BG_ELEVATED,
            fg=TEXT_PRIMARY,
            font=FONT_SUBHEADING,
            anchor="w",
        ).pack(fill="x", padx=PAD_S)
        tk.Label(
            access_card,
            text=f"{summary.credit_progress_label} | {summary.credit_progress_detail}",
            bg=BG_ELEVATED,
            fg=TEXT_SECONDARY,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
            wraplength=320,
        ).pack(fill="x", padx=PAD_S)
        _progress_bar(access_card, summary.credit_progress_fraction, COLOR_WARNING).pack(anchor="w", padx=PAD_S, pady=(PAD_S, 0))
        if credit_delta is not None:
            tk.Label(
                access_card,
                text=f"Trend: {credit_delta:+d}",
                bg=BG_ELEVATED,
                fg=COLOR_POSITIVE if credit_delta >= 0 else COLOR_NEGATIVE,
                font=FONT_SMALL,
                anchor="w",
            ).pack(fill="x", padx=PAD_S, pady=(1, 0))

        if getattr(summary, "blocked_doors", None):
            tk.Label(access_card, text="Blocked Doors", bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
            for line in summary.blocked_doors[: (1 if compact else 2)]:
                tk.Label(
                    access_card,
                    text=line,
                    bg=BG_ELEVATED,
                    fg=COLOR_WARNING,
                    font=FONT_SMALL,
                    anchor="w",
                    justify="left",
                    wraplength=320,
                ).pack(fill="x", padx=PAD_S, pady=(1, 0))

        watch_lines: list[str] = []
        if getattr(summary, "pending_fallout_count", 0):
            watch_lines.append(f"Pending fallout: {summary.pending_fallout_count}")
        if getattr(summary, "pending_decisions", None):
            watch_lines.extend(summary.pending_decisions[: (1 if compact else 2)])
        if summary.crisis_watch:
            watch_lines.extend(summary.crisis_watch[:1])
        if watch_lines:
            tk.Label(access_card, text="Watch", bg=BG_ELEVATED, fg=TEXT_HEADING, font=FONT_SMALL, anchor="w").pack(fill="x", padx=PAD_S, pady=(PAD_S, 0))
            for line in watch_lines:
                tk.Label(
                    access_card,
                    text=line,
                    bg=BG_ELEVATED,
                    fg=COLOR_WARNING if "pending" in line.lower() else TEXT_SECONDARY,
                    font=FONT_SMALL,
                    anchor="w",
                    justify="left",
                    wraplength=320,
                ).pack(fill="x", padx=PAD_S, pady=(1, 0))
        tk.Label(access_card, text="", bg=BG_ELEVATED).pack(fill="x", pady=(0, PAD_S))

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
