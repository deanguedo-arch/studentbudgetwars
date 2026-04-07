from __future__ import annotations

from random import Random

from budgetwars.engine.careers import promotion_blockers
from budgetwars.engine.events import eligible_events
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.wealth import apply_wealth_allocations, apply_wealth_returns
from budgetwars.models import ActiveMonthlyModifier


def test_career_switch_applies_friction(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    state = controller.state
    state.player.career.promotion_progress = 12
    start_stress = state.player.stress
    start_cash = state.player.cash
    controller.change_career("sales")
    assert state.player.career.track_id == "sales"
    assert state.player.career.transition_penalty_months > 0
    assert state.player.career.promotion_progress < 12
    assert state.player.stress > start_stress
    assert state.player.cash < start_cash


def test_promotion_blockers_surface_track_gates(controller_factory):
    controller = controller_factory(opening_path_id="trades_apprenticeship")
    state = controller.state
    state.player.career.promotion_progress = 20
    state.player.transport.reliability_score = 40
    blockers = promotion_blockers(controller.bundle, state)
    assert any("transport" in blocker.lower() for blocker in blockers)


def test_housing_switch_creates_instability_penalty(controller_factory):
    controller = controller_factory(city_id="mid_size_city", opening_path_id="move_out_immediately")
    state = controller.state
    state.player.credit_score = 700  # clear the solo_rental gate (needs 680)
    start_stability = state.player.housing.housing_stability
    controller.change_housing("solo_rental")
    assert state.player.housing.recent_move_penalty_months > 0
    assert state.player.housing.housing_stability <= start_stability


def test_transport_reliability_impacts_access(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    state = controller.state
    state.player.transport.option_id = "beater_car"
    state.player.transport.reliability_score = 35
    state.player.career.track_id = "warehouse_logistics"
    before_energy = state.player.energy
    resolve_month(bundle, state, controller.rng)
    assert state.player.energy < before_energy


def test_education_reentry_has_friction(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    state = controller.state
    state.current_month = 36
    start_cash = state.player.cash
    start_stress = state.player.stress
    controller.change_education("part_time_college")
    assert state.player.education.reentry_drag_months > 0
    assert state.player.cash <= start_cash
    assert state.player.stress >= start_stress


def test_wealth_strategy_is_player_controlled(controller_factory):
    controller = controller_factory()
    controller.change_wealth_strategy("market_chaser")
    assert controller.state.player.wealth_strategy_id == "market_chaser"


def test_wealth_allocation_and_returns_apply(bundle, controller_factory):
    controller = controller_factory()
    state = controller.state
    state.player.cash = 3000
    state.player.wealth_strategy_id = "market_chaser"
    allocation = apply_wealth_allocations(bundle, state)
    assert allocation["index"] > 0 or allocation["growth"] > 0
    before_total = state.player.high_interest_savings + state.player.index_fund + state.player.aggressive_growth_fund
    apply_wealth_returns(bundle, state, Random(99))
    after_total = state.player.high_interest_savings + state.player.index_fund + state.player.aggressive_growth_fund
    assert after_total != before_total or state.current_market_regime_id


def test_market_regime_event_targeting(bundle, controller_factory):
    controller = controller_factory()
    state = controller.state
    state.current_month = 15
    state.current_market_regime_id = "correction"
    events = eligible_events(bundle, state)
    ids = {event.id for event in events}
    assert "market_correction_shock" in ids


def test_modifier_gated_event_chain_targets_follow_up(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.current_month = 8
    state.player.housing.option_id = "roommates"
    state.player.housing.housing_stability = 50
    state.active_modifiers.append(
        ActiveMonthlyModifier(id="roommate_bill_chaos", label="Roommate Bill Chaos", remaining_months=2)
    )
    ids = {event.id for event in eligible_events(bundle, state)}
    assert "roommate_moves_out" in ids


def test_month_driver_notes_surface_real_causes(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.player.transport.option_id = "financed_car"
    state.player.transport.reliability_score = 40
    state.player.housing.housing_stability = 38
    state.player.wealth_strategy_id = "market_chaser"
    resolve_month(bundle, state, controller.rng)
    assert state.month_driver_notes
    combined = " ".join(state.month_driver_notes).lower()
    assert "transport" in combined or "housing" in combined or "market" in combined


def test_stacked_drag_preserves_game_over_logic(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.player.cash = 0
    state.player.savings = 0
    state.player.debt = state.debt_game_over_threshold - 20
    state.active_modifiers.extend(
        [
            ActiveMonthlyModifier(id="income_cut", label="Income Cut", remaining_months=2, income_multiplier=0.3),
            ActiveMonthlyModifier(id="rent_spike", label="Rent Spike", remaining_months=2, housing_cost_delta=1400),
        ]
    )
    resolve_month(bundle, state, controller.rng)
    assert state.game_over_reason in {"collections", "housing_loss", "burnout_collapse"}
