from __future__ import annotations

import tkinter as tk

from budgetwars.models import ContentBundle, GameState


class StatusBar(tk.LabelFrame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, text="Status", bg="#c0c0c0", fg="black", bd=2, relief="groove")
        self.label = tk.Label(self, anchor="w", justify="left", bg="#c0c0c0", font=("Courier New", 10, "bold"))
        self.label.pack(fill="x", padx=6, pady=6)

    def render(self, state: GameState, bundle: ContentBundle) -> None:
        player = state.player
        status_text = (
            f"Month {state.current_month:>3} / {state.total_months}   "
            f"Year {state.current_year:>2}   Age {state.current_age:>2}   "
            f"Cash ${player.cash:>5}   Savings ${player.savings:>5}   Debt ${player.debt:>6}   "
            f"Stress {player.stress:>3}/{state.max_stress}   Energy {player.energy:>3}/{state.max_energy}   "
            f"Life {player.life_satisfaction:>3}/{state.max_life_satisfaction}"
        )
        self.label.configure(text=status_text)
