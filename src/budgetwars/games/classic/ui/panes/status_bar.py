from __future__ import annotations

import tkinter as tk

from budgetwars.models import ContentBundle, GameState, LiveScoreSnapshot

from ..theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BORDER, TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY,
    COLOR_STRESS, COLOR_ENERGY, COLOR_LIFE, COLOR_MONEY_POS, COLOR_MONEY_NEG,
    FONT_HEADING, FONT_SUBHEADING, FONT_BODY, FONT_MONO, FONT_SMALL, FONT_SCORE,
    FONT_SCORE_TIER, PAD_S, PAD_M,
    delta_str, money_color, tier_color, money_str, stat_bar,
)

class StatusBar(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=BG_DARKEST, bd=0)

        self._normal_fonts = {
            "heading": FONT_SUBHEADING,
            "body": FONT_BODY,
            "mono": FONT_MONO,
            "small": FONT_SMALL,
            "score": ("Georgia", 22, "bold"),
        }
        self._large_fonts = {
            "heading": ("Georgia", 13, "bold"),
            "body": ("Trebuchet MS", 12),
            "mono": ("Consolas", 12),
            "small": ("Trebuchet MS", 10),
            "score": ("Georgia", 24, "bold"),
        }
        self._fonts = self._normal_fonts

        # ── Timeline section ──
        time_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        time_frame.pack(side="left", fill="y", padx=(0, PAD_S), pady=2)
        tk.Label(time_frame, text="RUN", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL, padx=PAD_S, pady=2).pack(side="left")
        self._month_label = tk.Label(time_frame, bg=BG_DARK, fg=TEXT_HEADING, font=self._fonts["heading"], padx=PAD_M, pady=2)
        self._month_label.pack(side="left")
        self._age_label = tk.Label(time_frame, bg=BG_DARK, fg=TEXT_SECONDARY, font=self._fonts["body"], padx=PAD_S, pady=2)
        self._age_label.pack(side="left")
        self._progress_canvas = tk.Canvas(time_frame, width=92, height=10, bg=BG_DARKEST, bd=0, highlightthickness=0)
        self._progress_canvas.pack(side="left", padx=PAD_S, pady=6)

        # ── Money section ──
        money_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        money_frame.pack(side="left", fill="y", padx=PAD_S, pady=2)
        tk.Label(money_frame, text="BANK", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL, padx=PAD_S, pady=2).pack(side="left")
        self._cash_label = tk.Label(money_frame, bg=BG_DARK, fg=COLOR_MONEY_POS, font=self._fonts["mono"], padx=PAD_S, pady=2)
        self._cash_label.pack(side="left")
        self._savings_label = tk.Label(money_frame, bg=BG_DARK, fg=COLOR_MONEY_POS, font=self._fonts["mono"], padx=PAD_S, pady=2)
        self._savings_label.pack(side="left")
        self._debt_label = tk.Label(money_frame, bg=BG_DARK, fg=COLOR_MONEY_NEG, font=self._fonts["mono"], padx=PAD_S, pady=2)
        self._debt_label.pack(side="left")
        self._cash_flow_label = tk.Label(money_frame, bg=BG_DARK, fg=TEXT_SECONDARY, font=self._fonts["mono"], padx=PAD_S, pady=2)
        self._cash_flow_label.pack(side="left")

        # ── Vitals section ──
        vitals_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        vitals_frame.pack(side="left", fill="y", padx=PAD_S, pady=2)
        tk.Label(vitals_frame, text="PRESSURE", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL, padx=PAD_S, pady=2).pack(side="left")
        self._vitals_container = vitals_frame

        self._stress_frame = tk.Frame(vitals_frame, bg=BG_DARK)
        self._stress_frame.pack(side="left", padx=PAD_S, pady=2)
        tk.Label(self._stress_frame, text="STR", bg=BG_DARK, fg=COLOR_STRESS, font=self._fonts["small"]).pack(side="left")
        self._stress_val = tk.Label(self._stress_frame, bg=BG_DARK, fg=TEXT_PRIMARY, font=self._fonts["small"])
        self._stress_val.pack(side="left", padx=(2, 0))

        self._energy_frame = tk.Frame(vitals_frame, bg=BG_DARK)
        self._energy_frame.pack(side="left", padx=PAD_S, pady=2)
        tk.Label(self._energy_frame, text="NRG", bg=BG_DARK, fg=COLOR_ENERGY, font=self._fonts["small"]).pack(side="left")
        self._energy_val = tk.Label(self._energy_frame, bg=BG_DARK, fg=TEXT_PRIMARY, font=self._fonts["small"])
        self._energy_val.pack(side="left", padx=(2, 0))

        self._life_frame = tk.Frame(vitals_frame, bg=BG_DARK)
        self._life_frame.pack(side="left", padx=PAD_S, pady=2)
        tk.Label(self._life_frame, text="LIFE", bg=BG_DARK, fg=COLOR_LIFE, font=self._fonts["small"]).pack(side="left")
        self._life_val = tk.Label(self._life_frame, bg=BG_DARK, fg=TEXT_PRIMARY, font=self._fonts["small"])
        self._life_val.pack(side="left", padx=(2, 0))

        # ── Season score detail ──
        self._season_detail = tk.Label(
            self,
            text="",
            bg=BG_DARKEST,
            fg=TEXT_SECONDARY,
            font=FONT_SMALL,
            anchor="w",
            justify="left",
        )
        self._season_detail.pack(side="bottom", fill="x", expand=False, padx=(PAD_S, PAD_S), pady=(1, 0))

        # ── Category bars (top row info moved from score strip) ──
        self._category_canvases: dict[str, tk.Canvas] = {}

        # ── Score badge (right-aligned) ──
        score_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1, width=250)
        score_frame.pack(side="right", fill="y", padx=(PAD_S, 0), pady=2)
        score_frame.pack_propagate(False)
        self._score_frame = score_frame
        tk.Label(score_frame, text="RANK", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL, padx=PAD_S, pady=2).pack(side="left")
        self._score_label = tk.Label(score_frame, bg=BG_DARK, fg=TEXT_HEADING, font=self._fonts["score"], padx=6, pady=1)
        self._score_label.pack(side="left")
        self._tier_label = tk.Label(score_frame, bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SCORE_TIER, padx=4, pady=2)
        self._tier_label.pack(side="left")

    def render(
        self,
        state: GameState,
        bundle: ContentBundle,
        snapshot: LiveScoreSnapshot,
        delta=None,
        *,
        credit_score: int | None = None,
        credit_delta: int | None = None,
    ) -> None:
        player = state.player
        # Timeline
        self._month_label.configure(text=f"Month {state.current_month}/{state.total_months}")
        self._age_label.configure(text=f"Age {state.current_age}  Yr {state.current_year}")
        self._progress_canvas.delete("all")
        pct = state.current_month / max(1, state.total_months)
        fill_w = int(92 * pct)
        bar_color = COLOR_MONEY_POS if pct < 0.8 else "#f0a840"
        self._progress_canvas.create_rectangle(0, 0, 92, 10, fill=BG_CARD, outline="")
        self._progress_canvas.create_rectangle(0, 0, fill_w, 10, fill=bar_color, outline="")

        # Money
        cash_color = COLOR_MONEY_POS if player.cash >= 0 else COLOR_MONEY_NEG
        self._cash_label.configure(text=f"Cash {money_str(player.cash)}", fg=cash_color)
        self._savings_label.configure(text=f"Sav {money_str(player.savings)}", fg=COLOR_MONEY_POS)
        debt_color = COLOR_MONEY_NEG if player.debt > 0 else TEXT_SECONDARY
        self._debt_label.configure(text=f"Debt {money_str(player.debt)}", fg=debt_color)
        self._cash_flow_label.configure(
            text=f"Flow {delta_str(player.monthly_surplus)}",
            fg=money_color(player.monthly_surplus),
        )

        # Vitals
        self._stress_val.configure(text=f"{player.stress}/{state.max_stress}")
        self._energy_val.configure(text=f"{player.energy}/{state.max_energy}")
        self._life_val.configure(text=f"{player.life_satisfaction}/{state.max_life_satisfaction}")

        # Score
        tc = tier_color(snapshot.score_tier)
        self._score_label.configure(text=f"{snapshot.projected_score:.1f}", fg=tc)
        self._tier_label.configure(text=snapshot.score_tier, fg=tc)
        detail_parts: list[str] = []
        if delta is not None:
            detail_parts.append(f"Delta {delta.delta:+.2f}")
            detail_parts.append(f"Best {delta.strongest_category}")
            detail_parts.append(f"Weakest {delta.weakest_category}")
        if snapshot.projected_score < 40:
            detail_parts.append(f"{40 - snapshot.projected_score:.1f} to Silver")
        elif snapshot.projected_score < 60:
            detail_parts.append(f"{60 - snapshot.projected_score:.1f} to Gold")
        elif snapshot.projected_score < 80:
            detail_parts.append(f"{80 - snapshot.projected_score:.1f} to Elite")
        if credit_score is not None:
            credit_text = f"Credit {credit_score}"
            if credit_delta is not None:
                credit_text += f" | Trend {credit_delta:+d}"
            detail_parts.append(credit_text)
        self._season_detail.configure(text="   ".join(detail_parts))

    def set_large_text(self, enabled: bool) -> None:
        self._fonts = self._large_fonts if enabled else self._normal_fonts
        self._month_label.configure(font=self._fonts["heading"])
        self._age_label.configure(font=self._fonts["body"])
        self._cash_label.configure(font=self._fonts["mono"])
        self._savings_label.configure(font=self._fonts["mono"])
        self._debt_label.configure(font=self._fonts["mono"])
        self._cash_flow_label.configure(font=self._fonts["mono"])
        self._stress_val.configure(font=self._fonts["small"])
        self._energy_val.configure(font=self._fonts["small"])
        self._life_val.configure(font=self._fonts["small"])
        self._score_label.configure(font=self._fonts["score"])
        self._score_frame.configure(width=280 if enabled else 250)
        self._season_detail.configure(font=self._fonts["small"])
