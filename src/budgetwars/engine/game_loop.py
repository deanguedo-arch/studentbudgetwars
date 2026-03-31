from __future__ import annotations

from pathlib import Path

from budgetwars.models import ContentBundle, FinalScoreSummary, GameState

from .banking import borrow_cash, deposit_cash, repay_debt, withdraw_cash
from .gigs import available_gigs, perform_gig
from .inventory import (
    buy_commodity,
    buy_item,
    drop_commodity,
    drop_item,
    estimated_inventory_value,
    inventory_slots_used,
    remaining_capacity,
    sell_commodity,
    use_item,
)
from .lookups import get_district, get_item
from .market import current_market
from .scoring import calculate_final_score
from .study import rest_for_day, study_for_day
from .travel import move_to_district
from .turn_resolution import advance_after_action, initialize_new_game


class GameController:
    def __init__(self, bundle: ContentBundle, state: GameState):
        self.bundle = bundle
        self.state = state

    @classmethod
    def new_game(
        cls,
        bundle: ContentBundle,
        player_name: str,
        preset_id: str | None = None,
        difficulty_id: str = "normal",
        seed: int | None = None,
    ) -> "GameController":
        return cls(bundle, initialize_new_game(bundle, player_name, preset_id, difficulty_id, seed))

    def current_market(self):
        return current_market(self.state)

    def current_district(self):
        return get_district(self.bundle, self.state.player.current_district_id)

    def available_gigs(self):
        return available_gigs(self.state, self.bundle)

    def inventory_slots_used(self) -> int:
        return inventory_slots_used(self.state, self.bundle)

    def remaining_capacity(self) -> int:
        return remaining_capacity(self.state, self.bundle)

    def estimated_inventory_value(self) -> int:
        return estimated_inventory_value(self.state, self.bundle)

    def final_score_summary(self) -> FinalScoreSummary:
        return calculate_final_score(self.state, self.bundle)

    def _run_turn(self, action) -> GameState:
        if self.state.game_over_reason or self.state.current_day > self.state.total_days:
            raise ValueError("The run is already over")
        prior_log_length = len(self.state.log_messages)
        self.state = action(self.state)
        self.state = advance_after_action(self.state, self.bundle, prior_log_length)
        return self.state

    def travel(self, district_id: str) -> GameState:
        return self._run_turn(lambda state: move_to_district(state, self.bundle, district_id))

    def buy(self, commodity_id: str, quantity: int) -> GameState:
        return self._run_turn(lambda state: buy_commodity(state, self.bundle, commodity_id, quantity))

    def sell(self, commodity_id: str, quantity: int) -> GameState:
        return self._run_turn(lambda state: sell_commodity(state, self.bundle, commodity_id, quantity))

    def work_gig(self, gig_id: str) -> GameState:
        return self._run_turn(lambda state: perform_gig(state, self.bundle, gig_id))

    def rest(self) -> GameState:
        return self._run_turn(lambda state: rest_for_day(state, self.bundle))

    def study(self) -> GameState:
        return self._run_turn(lambda state: study_for_day(state, self.bundle))

    def bank_deposit(self, amount: int) -> GameState:
        return self._run_turn(lambda state: deposit_cash(state, self.bundle, amount))

    def bank_withdraw(self, amount: int) -> GameState:
        return self._run_turn(lambda state: withdraw_cash(state, self.bundle, amount))

    def bank_borrow(self, amount: int) -> GameState:
        return self._run_turn(lambda state: borrow_cash(state, self.bundle, amount))

    def bank_repay(self, amount: int) -> GameState:
        return self._run_turn(lambda state: repay_debt(state, self.bundle, amount))

    def buy_support_item(self, item_id: str, quantity: int = 1) -> GameState:
        return self._run_turn(lambda state: buy_item(state, self.bundle, item_id, quantity))

    def use_support_item(self, item_id: str) -> GameState:
        return self._run_turn(lambda state: use_item(state, self.bundle, item_id))

    def drop_commodity(self, commodity_id: str, quantity: int) -> GameState:
        self.state = drop_commodity(self.state, self.bundle, commodity_id, quantity)
        return self.state

    def drop_item(self, item_id: str, quantity: int = 1) -> GameState:
        self.state = drop_item(self.state, self.bundle, item_id, quantity)
        return self.state

    def local_supply_items(self):
        item_ids: set[str] = set()
        for service in self.bundle.services:
            if service.kind == "supply_shop" and self.state.player.current_district_id in service.district_ids:
                item_ids.update(service.item_ids)
        return [get_item(self.bundle, item_id) for item_id in sorted(item_ids)]

    def save_path(self, save_path: Path) -> Path:
        from budgetwars.saves import save_game

        return save_game(self.state, save_path)
