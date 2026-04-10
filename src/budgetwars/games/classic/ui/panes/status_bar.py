from __future__ import annotations

import tkinter as tk

from budgetwars.models import ContentBundle, GameState, LiveScoreSnapshot

from ..theme import (
    BG_CARD, BG_DARK, BG_DARKEST, BORDER, TEXT_HEADING, TEXT_PRIMARY, TEXT_SECONDARY,
    COLOR_STRESS, COLOR_ENERGY, COLOR_LIFE, COLOR_MONEY_POS, COLOR_MONEY_NEG,
    FONT_HEADING, FONT_SUBHEADING, FONT_BODY, FONT_MONO, FONT_SMALL,
    FONT_SCORE_TIER, PAD_S, PAD_M,
    tier_color, money_str, stat_bar,
)

_CATEGORY_COLORS = {
    "net_worth": "#48d878",
    "monthly_surplus": "#60b0f0",
    "debt_ratio": "#e85050",
    "career_tier": "#f05f5f",
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


class StatusBar(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg=BG_DARKEST, bd=0)

        self._normal_fonts = {
            "heading": FONT_SUBHEADING,
            "body": FONT_BODY,
            "mono": FONT_MONO,
            "small": FONT_SMALL,
        }
        self._large_fonts = {
            "heading": ("Georgia", 13, "bold"),
            "body": ("Trebuchet MS", 12),
            "mono": ("Consolas", 12),
            "small": ("Trebuchet MS", 10),
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

        # ── Category bars (top row info moved from score strip) ──
        category_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        category_frame.pack(side="right", fill="y", padx=(PAD_S, PAD_S), pady=2)
        self._category_canvases: dict[str, tk.Canvas] = {}
        for i, (key, label) in enumerate(_CATEGORY_LABELS.items()):
            row = i // 4
            col = i % 4
            item = tk.Frame(category_frame, bg=BG_DARK)
            item.grid(row=row, column=col, padx=(5, 4), pady=1, sticky="w")
            tk.Label(item, text=label, bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL).pack(side="left", padx=(0, 2))
            canvas = tk.Canvas(item, width=54, height=7, bg=BG_DARKEST, bd=0, highlightthickness=0)
            canvas.pack(side="left")
            self._category_canvases[key] = canvas

        # ── Score badge (right-aligned) ──
        score_frame = tk.Frame(self, bg=BG_DARK, bd=1, relief="solid", highlightbackground=BORDER, highlightthickness=1)
        score_frame.pack(side="right", fill="y", padx=(PAD_S, 0), pady=2)
        tk.Label(score_frame, text="RANK", bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SMALL, padx=PAD_S, pady=2).pack(side="left")
        self._score_label = tk.Label(score_frame, bg=BG_DARK, fg=TEXT_HEADING, font=self._fonts["heading"], padx=PAD_M, pady=2)
        self._score_label.pack(side="left")
        self._tier_label = tk.Label(score_frame, bg=BG_DARK, fg=TEXT_SECONDARY, font=FONT_SCORE_TIER, padx=PAD_S, pady=2)
        self._tier_label.pack(side="left")

    def render(self, state: GameState, bundle: ContentBundle, snapshot: LiveScoreSnapshot) -> None:
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

        # Vitals
        self._stress_val.configure(text=f"{player.stress}/{state.max_stress}")
        self._energy_val.configure(text=f"{player.energy}/{state.max_energy}")
        self._life_val.configure(text=f"{player.life_satisfaction}/{state.max_life_satisfaction}")

        # Score
        tc = tier_color(snapshot.score_tier)
        self._score_label.configure(text=f"{snapshot.projected_score:.1f}", fg=tc)
        self._tier_label.configure(text=snapshot.score_tier, fg=tc)
        for key, canvas in self._category_canvases.items():
            canvas.delete("all")
            value = snapshot.breakdown.get(key, 0)
            fill_w = max(0, min(54, int(54 * value / 100)))
            color = _CATEGORY_COLORS.get(key, TEXT_SECONDARY)
            canvas.create_rectangle(0, 0, 54, 7, fill=BG_CARD, outline="")
            canvas.create_rectangle(0, 0, fill_w, 7, fill=color, outline="")

    def set_large_text(self, enabled: bool) -> None:
        self._fonts = self._large_fonts if enabled else self._normal_fonts
        self._month_label.configure(font=self._fonts["heading"])
        self._age_label.configure(font=self._fonts["body"])
        self._cash_label.configure(font=self._fonts["mono"])
        self._savings_label.configure(font=self._fonts["mono"])
        self._debt_label.configure(font=self._fonts["mono"])
        self._stress_val.configure(font=self._fonts["small"])
        self._energy_val.configure(font=self._fonts["small"])
        self._life_val.configure(font=self._fonts["small"])
        self._score_label.configure(font=self._fonts["heading"])
