from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, InventoryEntry, SupportItemEntry

from .effects import append_log, apply_state_effects
from .lookups import get_commodity, get_item
from .market import current_market


def commodity_quantity(state: GameState, commodity_id: str) -> int:
    for entry in state.player.commodity_inventory:
        if entry.commodity_id == commodity_id:
            return entry.quantity
    return 0


def item_quantity(state: GameState, item_id: str) -> int:
    for entry in state.player.item_inventory:
        if entry.item_id == item_id:
            return entry.quantity
    return 0


def inventory_slots_used(state: GameState, bundle: ContentBundle) -> int:
    total = 0
    for entry in state.player.commodity_inventory:
        total += entry.quantity * get_commodity(bundle, entry.commodity_id).size
    for entry in state.player.item_inventory:
        total += entry.quantity * get_item(bundle, entry.item_id).size
    return total


def remaining_capacity(state: GameState, bundle: ContentBundle) -> int:
    return state.player.backpack_capacity - inventory_slots_used(state, bundle)


def _upsert_commodity_entries(state: GameState, commodity_id: str, quantity_delta: int, unit_price: int) -> list[InventoryEntry]:
    entries: list[InventoryEntry] = []
    found = False
    for entry in state.player.commodity_inventory:
        if entry.commodity_id != commodity_id:
            entries.append(entry)
            continue
        found = True
        new_quantity = entry.quantity + quantity_delta
        if new_quantity <= 0:
            continue
        if quantity_delta > 0:
            total_cost = (entry.average_price * entry.quantity) + (unit_price * quantity_delta)
            average_price = int(round(total_cost / new_quantity))
        else:
            average_price = entry.average_price
        entries.append(entry.model_copy(update={"quantity": new_quantity, "average_price": average_price}))
    if not found and quantity_delta > 0:
        entries.append(InventoryEntry(commodity_id=commodity_id, quantity=quantity_delta, average_price=unit_price))
    return entries


def _upsert_item_entries(state: GameState, item_id: str, quantity_delta: int) -> list[SupportItemEntry]:
    entries: list[SupportItemEntry] = []
    found = False
    for entry in state.player.item_inventory:
        if entry.item_id != item_id:
            entries.append(entry)
            continue
        found = True
        new_quantity = entry.quantity + quantity_delta
        if new_quantity <= 0:
            continue
        entries.append(entry.model_copy(update={"quantity": new_quantity}))
    if not found and quantity_delta > 0:
        entries.append(SupportItemEntry(item_id=item_id, quantity=quantity_delta))
    return entries


def buy_commodity(state: GameState, bundle: ContentBundle, commodity_id: str, quantity: int) -> GameState:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    commodity = get_commodity(bundle, commodity_id)
    market = current_market(state)
    if commodity.id not in market.listings:
        raise ValueError(f"{commodity.name} is not available here")
    total_cost = market.listings[commodity_id] * quantity
    required_slots = commodity.size * quantity
    if state.player.cash < total_cost:
        raise ValueError("Not enough cash")
    if remaining_capacity(state, bundle) < required_slots:
        raise ValueError("Not enough backpack space")
    updated_player = state.player.model_copy(
        update={
            "cash": state.player.cash - total_cost,
            "commodity_inventory": _upsert_commodity_entries(state, commodity_id, quantity, market.listings[commodity_id]),
        }
    )
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Bought {quantity} {commodity.name} for ${total_cost}.")


def sell_commodity(state: GameState, bundle: ContentBundle, commodity_id: str, quantity: int) -> GameState:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    commodity = get_commodity(bundle, commodity_id)
    if commodity_quantity(state, commodity_id) < quantity:
        raise ValueError("You are not carrying that many units")
    market = current_market(state)
    total_sale = market.listings[commodity_id] * quantity
    updated_player = state.player.model_copy(
        update={
            "cash": state.player.cash + total_sale,
            "commodity_inventory": _upsert_commodity_entries(state, commodity_id, -quantity, market.listings[commodity_id]),
        }
    )
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Sold {quantity} {commodity.name} for ${total_sale}.")


def buy_item(state: GameState, bundle: ContentBundle, item_id: str, quantity: int = 1) -> GameState:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    item = get_item(bundle, item_id)
    local_shop_items = set()
    for service in bundle.services:
        if service.kind == "supply_shop" and state.player.current_district_id in service.district_ids:
            local_shop_items.update(service.item_ids)
    if item_id not in local_shop_items:
        raise ValueError(f"{item.name} is not sold in this district")
    total_cost = item.price * quantity
    required_slots = item.size * quantity
    if state.player.cash < total_cost:
        raise ValueError("Not enough cash")
    if remaining_capacity(state, bundle) < required_slots:
        raise ValueError("Not enough backpack space")
    updated_player = state.player.model_copy(
        update={
            "cash": state.player.cash - total_cost,
            "item_inventory": _upsert_item_entries(state, item_id, quantity),
        }
    )
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"Bought {quantity} {item.name} for ${total_cost}.")


def use_item(state: GameState, bundle: ContentBundle, item_id: str) -> GameState:
    if item_quantity(state, item_id) <= 0:
        raise ValueError("That item is not in your bag")
    item = get_item(bundle, item_id)
    updated_player = state.player.model_copy(update={"item_inventory": _upsert_item_entries(state, item_id, -1)})
    state = state.model_copy(update={"player": updated_player})
    state = append_log(state, f"Used {item.name}.")
    return apply_state_effects(state, bundle, item.use_effects, item.name)


def drop_commodity(state: GameState, bundle: ContentBundle, commodity_id: str, quantity: int) -> GameState:
    if commodity_quantity(state, commodity_id) < quantity or quantity <= 0:
        raise ValueError("Invalid drop quantity")
    updated_player = state.player.model_copy(
        update={"commodity_inventory": _upsert_commodity_entries(state, commodity_id, -quantity, 0)}
    )
    state = state.model_copy(update={"player": updated_player})
    commodity = get_commodity(bundle, commodity_id)
    return append_log(state, f"Dropped {quantity} {commodity.name}.")


def drop_item(state: GameState, bundle: ContentBundle, item_id: str, quantity: int = 1) -> GameState:
    if item_quantity(state, item_id) < quantity or quantity <= 0:
        raise ValueError("Invalid drop quantity")
    updated_player = state.player.model_copy(update={"item_inventory": _upsert_item_entries(state, item_id, -quantity)})
    state = state.model_copy(update={"player": updated_player})
    item = get_item(bundle, item_id)
    return append_log(state, f"Dropped {quantity} {item.name}.")


def estimated_inventory_value(state: GameState, bundle: ContentBundle) -> int:
    total = 0
    local_prices = state.current_markets.get(state.player.current_district_id)
    for entry in state.player.commodity_inventory:
        commodity = get_commodity(bundle, entry.commodity_id)
        price = local_prices.listings.get(entry.commodity_id) if local_prices else None
        if price is None:
            price = int(round((commodity.typical_low + commodity.typical_high) / 2))
        total += price * entry.quantity
    for entry in state.player.item_inventory:
        total += get_item(bundle, entry.item_id).price * entry.quantity
    return total
