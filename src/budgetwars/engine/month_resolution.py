from __future__ import annotations

from dataclasses import dataclass
from random import Random

from budgetwars.models import ActiveMonthlyModifier, ContentBundle, GameState

from .budgeting import (
    apply_budget_stance,
    apply_interest_and_growth,
    debt_payment_due,
    discretionary_spending,
    living_cost,
    make_debt_payment,
    pay_named_cost,
)
from .careers import add_promotion_progress, apply_career_effects, current_income, maybe_promote
from .education import apply_education_effects, education_monthly_cost, update_education_progress
from .effects import append_log, apply_stat_effects, clamp_player_state, net_worth, trim_logs
from .events import roll_month_events
from .housing import apply_housing_effects, monthly_housing_cost
from .lookups import get_city, get_focus_action, get_housing_option
from .transport import apply_transport_access_penalty, apply_transport_effects, monthly_transport_cost


@dataclass(slots=True)
class ModifierSnapshot:
    income_multiplier: float = 1.0
    housing_cost_delta: int = 0
    living_cost_delta: int = 0
    transport_cost_delta: int = 0
    education_cost_delta: int = 0
    promotion_progress_delta: int = 0
    education_progress_delta: int = 0
    transport_switch_discount: int = 0


def _capture_resource_delta(
    state: GameState,
    *,
    label: str,
    previous_stress: int,
    previous_energy: int,
    stress_parts: list[str],
    energy_parts: list[str],
) -> None:
    stress_delta = state.player.stress - previous_stress
    energy_delta = state.player.energy - previous_energy
    if stress_delta:
        stress_parts.append(f"{label} {stress_delta:+d}")
    if energy_delta:
        energy_parts.append(f"{label} {energy_delta:+d}")


def _apply_start_of_month_modifiers(state: GameState, modifiers: list[ActiveMonthlyModifier]) -> ModifierSnapshot:
    snapshot = ModifierSnapshot()
    for modifier in modifiers:
        apply_stat_effects(state, modifier.stat_effects)
        snapshot.income_multiplier *= modifier.income_multiplier
        snapshot.housing_cost_delta += modifier.housing_cost_delta
        snapshot.living_cost_delta += modifier.living_cost_delta
        snapshot.transport_cost_delta += modifier.transport_cost_delta
        snapshot.education_cost_delta += modifier.education_cost_delta
        snapshot.promotion_progress_delta += modifier.promotion_progress_delta
        snapshot.education_progress_delta += modifier.education_progress_delta
        snapshot.transport_switch_discount += modifier.transport_switch_discount
        append_log(state, f"Active carryover: {modifier.label}")
    return snapshot


def _tick_existing_modifiers(state: GameState, existing_modifier_tokens: set[int]) -> None:
    remaining: list[ActiveMonthlyModifier] = []
    for modifier in state.active_modifiers:
        if id(modifier) in existing_modifier_tokens:
            modifier.remaining_months -= 1
        if modifier.remaining_months > 0:
            remaining.append(modifier)
        else:
            append_log(state, f"{modifier.label} wore off.")
    state.active_modifiers = remaining


def _update_housing_stability(bundle: ContentBundle, state: GameState, housing_shortfall: int) -> None:
    if housing_shortfall > 0:
        state.missed_housing_payments += 1
    else:
        state.missed_housing_payments = max(0, state.missed_housing_payments - 1)

    if state.missed_housing_payments <= state.housing_miss_limit:
        return

    player = state.player
    if (
        player.current_city_id == "hometown"
        and player.family_support >= state.minimum_parent_fallback_support
        and player.housing_id != "parents"
    ):
        player.housing_id = "parents"
        state.missed_housing_payments = 0
        append_log(state, "Housing slipped badly enough that you moved back in with your parents to stabilize.")
        return
    state.game_over_reason = "housing_loss"


def _update_burnout(state: GameState) -> None:
    if state.player.stress >= state.burnout_stress_threshold or state.player.energy <= state.burnout_energy_threshold:
        state.burnout_streak += 1
    else:
        state.burnout_streak = 0
    if state.burnout_streak > state.burnout_streak_limit:
        state.game_over_reason = "burnout_collapse"


def _check_collections(state: GameState) -> None:
    if state.player.debt >= state.debt_game_over_threshold:
        state.game_over_reason = "collections"


def _annual_summary(state: GameState) -> None:
    append_log(
        state,
        (
            f"Year {state.current_year} closed: cash ${state.player.cash}, savings ${state.player.savings}, "
            f"debt ${state.player.debt}, stress {state.player.stress}, energy {state.player.energy}."
        ),
    )


def resolve_month(bundle: ContentBundle, state: GameState, rng: Random) -> None:
    if state.game_over_reason or state.current_month > state.total_months:
        return
    _check_collections(state)
    if state.game_over_reason:
        return

    start_net = net_worth(state)
    stress_start = state.player.stress
    energy_start = state.player.energy
    stress_parts: list[str] = []
    energy_parts: list[str] = []
    existing_modifier_tokens = {id(modifier) for modifier in state.active_modifiers}
    state.recent_summary = []
    append_log(state, f"--- Month {state.current_month} / Year {state.current_year} (Age {state.current_age}) ---")

    state.player.energy += bundle.config.baseline_monthly_energy_recovery
    state.player.stress -= bundle.config.baseline_monthly_stress_relief
    stress_parts.append(f"baseline {-bundle.config.baseline_monthly_stress_relief:+d}")
    energy_parts.append(f"baseline {bundle.config.baseline_monthly_energy_recovery:+d}")

    before_stress = state.player.stress
    before_energy = state.player.energy
    snapshot = _apply_start_of_month_modifiers(state, list(state.active_modifiers))
    _capture_resource_delta(
        state,
        label="carryover",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    focus = get_focus_action(bundle, state.player.selected_focus_action_id)

    before_stress = state.player.stress
    before_energy = state.player.energy
    access_multiplier = apply_transport_access_penalty(bundle, state)
    _capture_resource_delta(
        state,
        label="access",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    income = current_income(bundle, state, snapshot.income_multiplier * focus.income_multiplier * access_multiplier)
    state.player.cash += income
    append_log(state, f"Income from {state.player.career.track_id.replace('_', ' ')}: ${income}")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_career_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="work",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    before_stress = state.player.stress
    before_energy = state.player.energy
    education_program = apply_education_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="school",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    education_cost = education_monthly_cost(bundle, state, modifier_delta=snapshot.education_cost_delta)
    if education_cost:
        pay_named_cost(state, education_cost, "Education")

    housing_cost = monthly_housing_cost(bundle, state, modifier_delta=snapshot.housing_cost_delta)
    housing_payment = pay_named_cost(state, housing_cost, "Housing")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_housing_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="housing",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    transport_cost = monthly_transport_cost(bundle, state, modifier_delta=snapshot.transport_cost_delta)
    if transport_cost:
        pay_named_cost(state, transport_cost, "Transport")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_transport_effects(bundle, state)
    _capture_resource_delta(
        state,
        label="transport",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    living = living_cost(bundle, state, modifier_delta=snapshot.living_cost_delta)
    pay_named_cost(state, living, "Living costs")

    debt_due = debt_payment_due(bundle, state)
    if debt_due:
        make_debt_payment(state, debt_due)

    discretionary = discretionary_spending(bundle, state)
    if discretionary:
        pay_named_cost(state, discretionary, "Discretionary spending")

    before_stress = state.player.stress
    before_energy = state.player.energy
    apply_budget_stance(bundle, state, state.player.cash)
    _capture_resource_delta(
        state,
        label="budget",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    before_stress = state.player.stress
    before_energy = state.player.energy
    state.player.stress += focus.stress_delta
    state.player.energy += focus.energy_delta
    state.player.life_satisfaction += focus.life_satisfaction_delta
    _capture_resource_delta(
        state,
        label=focus.name.lower(),
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )
    append_log(state, f"Focus for the month: {focus.name}")

    before_stress = state.player.stress
    before_energy = state.player.energy
    roll_month_events(bundle, state, rng)
    _capture_resource_delta(
        state,
        label="events",
        previous_stress=before_stress,
        previous_energy=before_energy,
        stress_parts=stress_parts,
        energy_parts=energy_parts,
    )

    add_promotion_progress(bundle, state, focus.promotion_progress_bonus + snapshot.promotion_progress_delta)
    update_education_progress(bundle, state, focus.education_progress_bonus + snapshot.education_progress_delta)
    maybe_promote(bundle, state)

    interest, savings_growth = apply_interest_and_growth(bundle, state)
    clamp_player_state(state)
    _tick_existing_modifiers(state, existing_modifier_tokens)
    _update_housing_stability(bundle, state, housing_payment.added_to_debt)
    _update_burnout(state)
    _check_collections(state)

    end_net = net_worth(state)
    state.player.monthly_surplus = end_net - start_net
    state.recent_summary = [
        f"Income ${income}",
        f"Housing ${housing_cost}",
        f"Transport ${transport_cost}",
        f"Living ${living}",
        f"Debt {'payment $' + str(debt_due) if debt_due else 'steady'}",
        f"Month swing {state.player.monthly_surplus:+d}",
        f"Stress {stress_start}->{state.player.stress} ({state.player.stress - stress_start:+d})",
        "Stress drivers: " + (", ".join(stress_parts) if stress_parts else "steady"),
        f"Energy {energy_start}->{state.player.energy} ({state.player.energy - energy_start:+d})",
        "Energy drivers: " + (", ".join(energy_parts) if energy_parts else "steady"),
    ]
    if state.game_over_reason:
        append_log(state, f"Run ended: {state.game_over_reason.replace('_', ' ')}.")
    elif state.current_month % 12 == 0:
        _annual_summary(state)

    trim_logs(bundle, state)
    if not state.game_over_reason:
        state.current_month += 1
