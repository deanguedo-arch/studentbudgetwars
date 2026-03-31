from __future__ import annotations

import pytest


def test_buy_and_sell_commodity_updates_inventory_and_cash(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="dorm_flipper", seed=82)
    commodity_id = "meal_swipes"
    buy_price = controller.current_market().listings[commodity_id]
    controller.buy(commodity_id, 2)
    entry = next(entry for entry in controller.state.player.commodity_inventory if entry.commodity_id == commodity_id)
    assert entry.quantity == 2
    assert controller.state.player.cash <= 120 - (buy_price * 2)

    controller.sell(commodity_id, 1)
    entry = next(entry for entry in controller.state.player.commodity_inventory if entry.commodity_id == commodity_id)
    assert entry.quantity == 1


def test_backpack_capacity_blocks_oversized_buy(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="dorm_flipper", seed=82)
    with pytest.raises(ValueError):
        controller.buy("mini_fridges", 20)
