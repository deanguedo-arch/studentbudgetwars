from __future__ import annotations

import tkinter as tk

from budgetwars.engine.outlook import build_outlook_lines
from budgetwars.engine.inventory import inventory_slots_used
from budgetwars.models import ContentBundle, GameState


class StatusBar(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg="#c0c0c0", bd=2, relief="raised")
        self.summary_var = tk.StringVar()
        self.outlook_var = tk.StringVar()
        tk.Label(
            self,
            textvariable=self.summary_var,
            anchor="w",
            bg="#c0c0c0",
            fg="black",
            font=("Courier New", 10, "bold"),
        ).pack(fill="x", padx=6, pady=(4, 2))
        tk.Label(
            self,
            textvariable=self.outlook_var,
            anchor="w",
            justify="left",
            bg="#c0c0c0",
            fg="black",
            font=("Courier New", 9),
        ).pack(fill="x", padx=6, pady=(0, 4))

    def render(self, state: GameState, bundle: ContentBundle) -> None:
        used_slots = inventory_slots_used(state, bundle)
        summary = (
            f"District {state.player.current_district_id} | Day {state.current_day}/{state.total_days} | "
            f"Week {state.current_week} | Cash ${state.player.cash} | Debt ${state.player.debt} | "
            f"Bank ${state.player.bank_balance} | Space {used_slots}/{state.player.backpack_capacity} | "
            f"Energy {state.player.energy} | Stress {state.player.stress} | GPA {state.player.gpa:.2f} | Heat {state.player.heat}"
        )
        outlook = "\n".join(build_outlook_lines(state, bundle))
        self.summary_var.set(summary)
        self.outlook_var.set(outlook)
