from __future__ import annotations

from budgetwars.engine.events import activate_event
from budgetwars.engine.lookups import get_event
from budgetwars.engine.market import generate_daily_markets


def test_market_generation_is_seeded_and_within_ranges(bundle, controller_factory):
    first = controller_factory(bundle, seed=77)
    second = controller_factory(bundle, seed=77)
    assert first.state.current_markets == second.state.current_markets
    for commodity in bundle.commodities:
        for market in first.state.current_markets.values():
            assert commodity.min_price <= market.listings[commodity.id] <= commodity.max_price


def test_active_event_changes_market_prices(bundle, controller_factory):
    controller = controller_factory(bundle, seed=91)
    baseline = generate_daily_markets(controller.state.model_copy(update={"active_events": []}), bundle)
    event = get_event(bundle, "sold_out_show")
    boosted_state = activate_event(controller.state.model_copy(update={"active_events": []}), bundle, event, controller.state.current_day)
    boosted_markets = generate_daily_markets(boosted_state, bundle)
    assert boosted_markets["stadium_district"].listings["concert_tickets"] > baseline["stadium_district"].listings["concert_tickets"]
