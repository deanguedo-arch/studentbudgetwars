from __future__ import annotations

import tkinter as tk

from budgetwars.models import ContentBundle, GameState


class InventoryPanel(tk.Frame):
    def __init__(self, master: tk.Misc):
        super().__init__(master, bg="#c0c0c0", bd=2, relief="sunken")
        tk.Label(self, text="Inventory Carried", bg="#c0c0c0", font=("Courier New", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.goods = tk.Listbox(self, bg="white", fg="black", font=("Courier New", 10), height=10)
        self.goods.pack(fill="both", expand=True, padx=4, pady=(4, 2))
        tk.Label(self, text="Support Items", bg="#c0c0c0", font=("Courier New", 10, "bold")).pack(anchor="w", padx=4, pady=(2, 0))
        self.items = tk.Listbox(self, bg="white", fg="black", font=("Courier New", 10), height=4)
        self.items.pack(fill="both", expand=False, padx=4, pady=(4, 4))
        self._commodity_ids: list[str] = []
        self._item_ids: list[str] = []

    def render(self, state: GameState, bundle: ContentBundle) -> None:
        self.goods.delete(0, "end")
        self.items.delete(0, "end")
        self._commodity_ids = []
        self._item_ids = []
        local_market = state.current_markets.get(state.player.current_district_id)
        for entry in state.player.commodity_inventory:
            commodity = next(commodity for commodity in bundle.commodities if commodity.id == entry.commodity_id)
            local_price = local_market.listings.get(entry.commodity_id) if local_market else entry.average_price
            self.goods.insert(
                "end",
                f"{commodity.name:<20} qty:{entry.quantity:<3} avg:${entry.average_price:<4} now:${local_price:<4}",
            )
            self._commodity_ids.append(entry.commodity_id)
        for entry in state.player.item_inventory:
            item = next(item for item in bundle.items if item.id == entry.item_id)
            self.items.insert("end", f"{item.name:<20} x{entry.quantity}")
            self._item_ids.append(entry.item_id)

    def selected_commodity_id(self) -> str | None:
        if not self.goods.curselection():
            return None
        return self._commodity_ids[self.goods.curselection()[0]]

    def selected_item_id(self) -> str | None:
        if not self.items.curselection():
            return None
        return self._item_ids[self.items.curselection()[0]]
