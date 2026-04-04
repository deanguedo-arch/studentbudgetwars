from __future__ import annotations

import tkinter as tk

from budgetwars.models import ContentBundle, GameState, LiveScoreSnapshot


class StatusBar(tk.LabelFrame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, text="Status", bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self._summary = tk.Label(self, anchor="w", justify="left", bg="#c0c0c0", font=("Consolas", 10, "bold"))
        self._summary.pack(fill="x", padx=6, pady=(6, 1))
        self._detail = tk.Label(self, anchor="w", justify="left", bg="#c0c0c0", font=("Consolas", 10))
        self._detail.pack(fill="x", padx=6, pady=(0, 6))
        self._normal_font = ("Consolas", 11, "bold")
        self._large_font = ("Consolas", 13, "bold")

    def render(self, state: GameState, bundle: ContentBundle, snapshot: LiveScoreSnapshot) -> None:
        player = state.player
        summary_text = (
            f"Month {state.current_month:>3}/{state.total_months}  "
            f"Age {state.current_age:>2}  "
            f"Cash ${player.cash:,}  Savings ${player.savings:,}  Debt ${player.debt:,}"
        )
        detail_text = (
            f"Score {snapshot.projected_score:.2f} ({snapshot.score_tier})  "
            f"Risk: {snapshot.biggest_risk}  "
            f"Stress {player.stress}/{state.max_stress}  Energy {player.energy}/{state.max_energy}"
        )
        self._summary.configure(text=summary_text)
        self._detail.configure(text=detail_text)

    def set_large_text(self, enabled: bool) -> None:
        self._summary.configure(font=("Consolas", 12, "bold") if enabled else ("Consolas", 10, "bold"))
        self._detail.configure(font=("Consolas", 12) if enabled else ("Consolas", 10))
