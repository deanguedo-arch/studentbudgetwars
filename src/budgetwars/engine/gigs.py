from __future__ import annotations

from budgetwars.models import ContentBundle, GameState, GigDefinition

from .effects import append_log, apply_state_effects
from .inventory import item_quantity
from .lookups import get_district, get_gig


def available_gigs(state: GameState, bundle: ContentBundle) -> list[GigDefinition]:
    district_id = state.player.current_district_id
    gigs: list[GigDefinition] = []
    for gig in bundle.gigs:
        if district_id not in gig.district_ids:
            continue
        if state.player.gpa < gig.min_gpa:
            continue
        if any(item_quantity(state, item_id) <= 0 for item_id in gig.required_item_ids):
            continue
        gigs.append(gig)
    return gigs


def perform_gig(state: GameState, bundle: ContentBundle, gig_id: str) -> GameState:
    gig = get_gig(bundle, gig_id)
    if gig not in available_gigs(state, bundle):
        raise ValueError("That gig is not available right now")
    district = get_district(bundle, state.player.current_district_id)
    strain_bonus = 2 if district.local_risk + state.player.heat >= bundle.config.gig_heat_threshold else 0
    state = apply_state_effects(
        state,
        bundle,
        {
            "cash": gig.pay,
            "energy": -gig.energy_cost,
            "stress": gig.stress_delta + strain_bonus,
            "heat": gig.heat_delta + (1 if district.local_risk >= 25 else 0),
        },
        gig.name,
    )
    return append_log(state, f"Worked {gig.name} in {district.name}.")
