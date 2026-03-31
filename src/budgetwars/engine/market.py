from __future__ import annotations

import random

from budgetwars.models import CommodityDefinition, ContentBundle, GameState, MarketSnapshot
from budgetwars.utils import clamp, derive_seed

from .lookups import get_difficulty, get_district


def _event_multiplier(state: GameState, district_id: str, commodity_id: str) -> float:
    multiplier = 1.0
    for event in state.active_events:
        if event.expires_on_day < state.current_day:
            continue
        multiplier *= event.commodity_multipliers.get(commodity_id, 1.0)
        multiplier *= event.district_commodity_multipliers.get(district_id, {}).get(commodity_id, 1.0)
    return multiplier


def _scarcity_roll(bundle: ContentBundle, rng: random.Random) -> float:
    roll = rng.random()
    if roll > 0.95:
        return rng.uniform(
            bundle.price_curves.scarcity_multiplier_floor,
            bundle.price_curves.scarcity_multiplier_ceiling,
        )
    if roll < 0.05:
        return rng.uniform(
            bundle.price_curves.flood_multiplier_floor,
            bundle.price_curves.flood_multiplier_ceiling,
        )
    return 1.0


def _build_price(
    state: GameState,
    bundle: ContentBundle,
    commodity: CommodityDefinition,
    district_id: str,
) -> int:
    difficulty = get_difficulty(bundle, state.difficulty_id)
    rng = random.Random(derive_seed(state.seed, state.current_day, district_id, commodity.id))

    base_price = rng.uniform(commodity.typical_low, commodity.typical_high)
    variance = rng.uniform(-commodity.volatility, commodity.volatility) * difficulty.price_spread_multiplier
    price = base_price * (1.0 + variance)

    district_multiplier = commodity.district_biases.get(district_id, 1.0)
    district_multiplier *= get_district(bundle, district_id).commodity_biases.get(commodity.id, 1.0)
    price *= district_multiplier
    price *= _event_multiplier(state, district_id, commodity.id)
    price *= _scarcity_roll(bundle, rng)

    return int(round(clamp(price, commodity.min_price, commodity.max_price)))


def generate_daily_markets(state: GameState, bundle: ContentBundle) -> dict[str, MarketSnapshot]:
    markets: dict[str, MarketSnapshot] = {}
    notes = [event.name for event in state.active_events if event.expires_on_day >= state.current_day][:4]
    for district in bundle.districts:
        listings = {commodity.id: _build_price(state, bundle, commodity, district.id) for commodity in bundle.commodities}
        markets[district.id] = MarketSnapshot(
            district_id=district.id,
            day_index=state.current_day,
            listings=listings,
            notes=notes,
        )
    return markets


def current_market(state: GameState) -> MarketSnapshot:
    market = state.current_markets.get(state.player.current_district_id)
    if market is None:
        raise ValueError("Current district market is unavailable")
    return market
