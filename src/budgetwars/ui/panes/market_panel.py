from __future__ import annotations

import tkinter as tk

from budgetwars.engine.inventory import commodity_quantity
from budgetwars.engine.market import current_market
from budgetwars.models import ContentBundle, GameState


class MarketPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg="#c0c0c0", bd=2, relief="sunken")
        tk.Label(self, text="Goods Here", bg="#c0c0c0", font=("Courier New", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.listbox = tk.Listbox(self, bg="white", fg="black", font=("Courier New", 10), height=14)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=4)
        self._ids: list[str] = []

    def render(self, state: GameState, bundle: ContentBundle) -> None:
        market = current_market(state)
        self.listbox.delete(0, "end")
        self._ids = []
        for commodity in bundle.commodities:
            price = market.listings[commodity.id]
            carrying = commodity_quantity(state, commodity.id)
            self.listbox.insert("end", f"{commodity.name:<22} ${price:>4}  held:{carrying}")
            self._ids.append(commodity.id)

    def selected_id(self) -> str | None:
        if not self.listbox.curselection():
            return None
        return self._ids[self.listbox.curselection()[0]]
