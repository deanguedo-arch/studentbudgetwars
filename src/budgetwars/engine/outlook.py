from __future__ import annotations

from budgetwars.models import ContentBundle, GameState

from .lookups import get_commodity, get_district
from .market import current_market


def build_outlook_lines(state: GameState, bundle: ContentBundle) -> list[str]:
    lines: list[str] = []
    district = get_district(bundle, state.player.current_district_id)
    lines.append(f"{district.name}: {district.description}")

    if state.player.energy <= 25:
        lines.append("Energy is low. Rest, use supplies, or avoid hard gigs.")
    elif state.player.stress >= 70:
        lines.append("Stress is running hot. Quiet districts and study-safe days matter.")

    if state.player.debt >= int(state.debt_game_over_threshold * 0.6):
        lines.append("Debt pressure is real. Cashing out profitable flips matters this week.")

    market = current_market(state)
    cheap_candidates: list[tuple[float, str, int]] = []
    hot_sale_candidates: list[tuple[float, str, int]] = []
    for commodity in bundle.commodities:
        local_price = market.listings[commodity.id]
        midpoint = (commodity.typical_low + commodity.typical_high) / 2
        cheap_candidates.append((local_price / midpoint, commodity.name, local_price))
    for entry in state.player.commodity_inventory:
        local_price = market.listings[entry.commodity_id]
        if local_price > entry.average_price:
            hot_sale_candidates.append((local_price / max(1, entry.average_price), get_commodity(bundle, entry.commodity_id).name, local_price))

    if cheap_candidates:
        best_buy = min(cheap_candidates, key=lambda item: item[0])
        if best_buy[0] <= 0.8:
            lines.append(f"Buy signal: {best_buy[1]} looks unusually cheap here at ${best_buy[2]}.")
    if hot_sale_candidates:
        best_sale = max(hot_sale_candidates, key=lambda item: item[0])
        if best_sale[0] >= 1.18:
            lines.append(f"Sell signal: {best_sale[1]} is paying well here at ${best_sale[2]}.")

    if state.active_events:
        names = ", ".join(event.name for event in state.active_events[:2])
        lines.append(f"Board pressure: {names}.")

    if not state.active_events and len(lines) < 3:
        lines.append("No big board shock today. Clean execution matters.")

    return lines[:4]
