from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from budgetwars.engine import GameController
from budgetwars.loaders import load_all_content
from budgetwars.saves import default_paths, load_game, load_named_game, save_named_game

from .panes import ActionsPanel, InventoryPanel, LogPanel, MarketPanel, StatusBar, build_menu_bar


class SelectionDialog(simpledialog.Dialog):
    def __init__(self, parent: tk.Misc, title: str, prompt: str, options: list[tuple[str, str]]):
        self.prompt = prompt
        self.options = options
        self.result: str | None = None
        super().__init__(parent, title)

    def body(self, master: tk.Misc):
        tk.Label(master, text=self.prompt, justify="left").pack(anchor="w", padx=6, pady=(6, 2))
        self.listbox = tk.Listbox(master, width=52, height=min(10, max(4, len(self.options))))
        self.listbox.pack(fill="both", expand=True, padx=6, pady=6)
        for label, _ in self.options:
            self.listbox.insert("end", label)
        if self.options:
            self.listbox.selection_set(0)
        return self.listbox

    def apply(self):
        if self.listbox.curselection():
            self.result = self.options[self.listbox.curselection()[0]][1]


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk, controller: GameController):
        super().__init__(master, bg="#c0c0c0")
        self.master = master
        self.controller = controller
        self.paths = default_paths()
        self.pack(fill="both", expand=True)
        self._build_layout()
        self.refresh()

    def _build_layout(self) -> None:
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill="x", padx=6, pady=(6, 4))

        self.log_panel = LogPanel(self)
        self.log_panel.pack(fill="both", expand=True, padx=6, pady=(0, 4))

        bottom = tk.Frame(self, bg="#c0c0c0")
        bottom.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.market_panel = MarketPanel(bottom)
        self.market_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        self.actions_panel = ActionsPanel(bottom)
        self.actions_panel.grid(row=0, column=1, sticky="nsew", padx=4)

        self.inventory_panel = InventoryPanel(bottom)
        self.inventory_panel.grid(row=0, column=2, sticky="nsew", padx=(4, 0))

        bottom.grid_columnconfigure(0, weight=3)
        bottom.grid_columnconfigure(1, weight=2)
        bottom.grid_columnconfigure(2, weight=3)
        bottom.grid_rowconfigure(0, weight=1)

        actions = [
            ("Buy", self.buy_commodity),
            ("Sell", self.sell_commodity),
            ("Travel", self.travel),
            ("Work Gig", self.work_gig),
            ("Rest", self.rest),
            ("Study", self.study),
            ("Bank", self.bank_action),
            ("Use Item", self.use_item),
            ("Drop", self.drop_inventory),
            ("Save", self.save_game),
        ]
        self.actions_panel.set_actions(actions)

        self.master.config(
            menu=build_menu_bar(
                self.master,
                {
                    "new_game": self.restart_new_game,
                    "save": self.save_game,
                    "exit": self.master.destroy,
                    "travel": self.travel,
                    "buy": self.buy_commodity,
                    "sell": self.sell_commodity,
                    "drop": self.drop_inventory,
                    "bank": self.bank_action,
                    "study": self.study,
                    "rest": self.rest,
                    "score": self.show_score_projection,
                    "help": self.show_help,
                },
            )
        )

    def _auto_save(self) -> None:
        save_named_game(self.controller.state, self.controller.bundle.config.autosave_name, root=self.paths.root)

    def _choose(self, title: str, prompt: str, options: list[tuple[str, str]]) -> str | None:
        if not options:
            messagebox.showinfo(title, "No valid options right now.")
            return None
        dialog = SelectionDialog(self.master, title, prompt, options)
        return dialog.result

    def _after_action(self) -> None:
        self._auto_save()
        self.refresh()
        self._check_end_state()

    def _run_action(self, callback) -> None:
        try:
            callback()
            self._after_action()
        except ValueError as exc:
            messagebox.showerror("Action failed", str(exc))
            self.refresh()

    def refresh(self) -> None:
        state = self.controller.state
        bundle = self.controller.bundle
        self.status_bar.render(state, bundle)
        self.log_panel.render(state.log_messages)
        self.market_panel.render(state, bundle)
        self.inventory_panel.render(state, bundle)
        self.master.title(f"{state.game_title} - {state.player.name}")

    def _check_end_state(self) -> None:
        state = self.controller.state
        if state.game_over_reason:
            summary = self.controller.final_score_summary()
            messagebox.showinfo("Run over", f"{state.game_over_reason}\n\nScore: {summary.final_score}")
        elif state.current_day > state.total_days:
            summary = self.controller.final_score_summary()
            messagebox.showinfo("Term finished", f"{summary.outcome}\n\nScore: {summary.final_score}")

    def restart_new_game(self) -> None:
        bundle = load_all_content(self.paths.root)
        preset_options = [(preset.name, preset.id) for preset in bundle.presets]
        difficulty_options = [(difficulty.name, difficulty.id) for difficulty in bundle.difficulties]
        preset_id = self._choose("New Game", "Choose a starting preset:", preset_options)
        if not preset_id:
            return
        difficulty_id = self._choose("Difficulty", "Choose a difficulty:", difficulty_options)
        if not difficulty_id:
            return
        name = simpledialog.askstring("Player Name", "Player name:", initialvalue="Player", parent=self.master) or "Player"
        self.controller = GameController.new_game(bundle, name, preset_id, difficulty_id)
        self._after_action()

    def travel(self) -> None:
        options = [(district.name, district.id) for district in self.controller.bundle.districts if district.id != self.controller.state.player.current_district_id]
        district_id = self._choose("Travel", "Pick a district to move to:", options)
        if district_id:
            self._run_action(lambda: self.controller.travel(district_id))

    def buy_commodity(self) -> None:
        selected = self.market_panel.selected_id()
        options = [(commodity.name, commodity.id) for commodity in self.controller.bundle.commodities]
        commodity_id = selected or self._choose("Buy", "Pick a commodity to buy:", options)
        if not commodity_id:
            return
        quantity = simpledialog.askinteger("Buy Quantity", "How many units?", minvalue=1, parent=self.master)
        if quantity:
            self._run_action(lambda: self.controller.buy(commodity_id, quantity))

    def sell_commodity(self) -> None:
        selected = self.inventory_panel.selected_commodity_id()
        options = []
        for entry in self.controller.state.player.commodity_inventory:
            commodity = next(commodity for commodity in self.controller.bundle.commodities if commodity.id == entry.commodity_id)
            options.append((f"{commodity.name} (x{entry.quantity})", commodity.id))
        commodity_id = selected or self._choose("Sell", "Pick a commodity to sell:", options)
        if not commodity_id:
            return
        quantity = simpledialog.askinteger("Sell Quantity", "How many units?", minvalue=1, parent=self.master)
        if quantity:
            self._run_action(lambda: self.controller.sell(commodity_id, quantity))

    def work_gig(self) -> None:
        gigs = self.controller.available_gigs()
        gig_id = self._choose(
            "Work Gig",
            "Choose a gig for the day:",
            [(f"{gig.name} | pay ${gig.pay} | energy {gig.energy_cost}", gig.id) for gig in gigs],
        )
        if gig_id:
            self._run_action(lambda: self.controller.work_gig(gig_id))

    def rest(self) -> None:
        self._run_action(self.controller.rest)

    def study(self) -> None:
        self._run_action(self.controller.study)

    def bank_action(self) -> None:
        choice = self._choose(
            "Bank",
            "Choose a bank action:",
            [("Deposit", "deposit"), ("Withdraw", "withdraw"), ("Borrow", "borrow"), ("Repay", "repay")],
        )
        if not choice:
            return
        amount = simpledialog.askinteger("Bank Amount", "Amount:", minvalue=1, parent=self.master)
        if not amount:
            return
        action_map = {
            "deposit": lambda: self.controller.bank_deposit(amount),
            "withdraw": lambda: self.controller.bank_withdraw(amount),
            "borrow": lambda: self.controller.bank_borrow(amount),
            "repay": lambda: self.controller.bank_repay(amount),
        }
        self._run_action(action_map[choice])

    def use_item(self) -> None:
        selected = self.inventory_panel.selected_item_id()
        options = []
        for entry in self.controller.state.player.item_inventory:
            item = next(item for item in self.controller.bundle.items if item.id == entry.item_id)
            options.append((f"{item.name} (x{entry.quantity})", item.id))
        item_id = selected or self._choose("Use Item", "Choose an item to use:", options)
        if item_id:
            self._run_action(lambda: self.controller.use_support_item(item_id))

    def drop_inventory(self) -> None:
        choice = self._choose("Drop", "Drop a commodity or support item?", [("Commodity", "commodity"), ("Support Item", "item")])
        if not choice:
            return
        if choice == "commodity":
            options = []
            for entry in self.controller.state.player.commodity_inventory:
                commodity = next(commodity for commodity in self.controller.bundle.commodities if commodity.id == entry.commodity_id)
                options.append((f"{commodity.name} (x{entry.quantity})", commodity.id))
            commodity_id = self._choose("Drop Commodity", "Choose what to drop:", options)
            if not commodity_id:
                return
            quantity = simpledialog.askinteger("Drop Quantity", "How many units?", minvalue=1, parent=self.master)
            if quantity:
                self.controller.drop_commodity(commodity_id, quantity)
                self.refresh()
        else:
            options = []
            for entry in self.controller.state.player.item_inventory:
                item = next(item for item in self.controller.bundle.items if item.id == entry.item_id)
                options.append((f"{item.name} (x{entry.quantity})", item.id))
            item_id = self._choose("Drop Item", "Choose what to drop:", options)
            if not item_id:
                return
            quantity = simpledialog.askinteger("Drop Quantity", "How many units?", minvalue=1, parent=self.master)
            if quantity:
                self.controller.drop_item(item_id, quantity)
                self.refresh()

    def save_game(self) -> None:
        default_name = self.controller.bundle.config.autosave_name
        save_name = simpledialog.askstring("Save Game", "Save file name:", initialvalue=default_name, parent=self.master)
        if not save_name:
            return
        save_named_game(self.controller.state, save_name, root=self.paths.root)
        messagebox.showinfo("Saved", f"Saved to {save_name}")

    def show_score_projection(self) -> None:
        summary = self.controller.final_score_summary()
        breakdown = "\n".join(f"{key}: {value:+.2f}" for key, value in summary.breakdown.items())
        messagebox.showinfo("Projected Score", f"{summary.outcome}\nScore: {summary.final_score}\n\n{breakdown}")

    def show_help(self) -> None:
        messagebox.showinfo(
            "How To Play",
            "Each day you take one main action.\n\n"
            "Travel to rotate districts, buy low, sell high, grind gigs for fast cash, and keep enough study pace to survive exam weeks.\n"
            "Weekly housing, utilities, phone, and debt interest hit every 7th day.",
        )
