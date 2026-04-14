from __future__ import annotations

from random import Random

import pytest

from budgetwars.engine.careers import current_income, promotion_blockers
from budgetwars.engine.events import eligible_events, event_severity_multiplier, event_weight, resolve_event, resolve_event_choice
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import calculate_final_score
from budgetwars.engine.status_arcs import start_status_arc
from budgetwars.engine.housing import can_switch_housing
from budgetwars.engine.transport import can_switch_transport
from budgetwars.engine.wealth import apply_wealth_allocations, apply_wealth_returns, emergency_liquidation
from budgetwars.models import ActiveMonthlyModifier


def _top_weighted_event_ids(bundle, state, *, limit: int = 6) -> list[str]:
    scored = sorted(
        ((event_weight(bundle, state, event), event.id) for event in eligible_events(bundle, state)),
        reverse=True,
    )
    return [event_id for _weight, event_id in scored[:limit]]


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


def test_phase_status_arc_transport_changes_followup_event_pressure(bundle, controller_factory):
    clean = controller_factory(opening_path_id="full_time_work")
    unstable = controller_factory(opening_path_id="full_time_work")
    for controller in (clean, unstable):
        controller.state.player.transport.option_id = "beater_car"
        controller.state.player.transport.reliability_score = 42

    missed_shift = next(event for event in bundle.events if event.id == "missed_shift_after_breakdown")
    start_status_arc(
        bundle,
        unstable.state,
        "transport_unstable",
        source_event_id="car_repair",
        duration_months=3,
        severity=2,
    )

    assert event_weight(bundle, unstable.state, missed_shift) > event_weight(bundle, clean.state, missed_shift)


def test_phase_status_arc_severe_transport_arc_sharply_raises_failure_weight(bundle, controller_factory):
    clean = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    unstable = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    for controller in (clean, unstable):
        controller.state.current_month = 10
        controller.state.player.transport.option_id = "beater_car"
        controller.state.player.transport.reliability_score = 34
        controller.state.player.monthly_surplus = -120

    beater_total_failure = next(event for event in bundle.events if event.id == "beater_total_failure")
    start_status_arc(
        bundle,
        unstable.state,
        "transport_unstable",
        source_event_id="beater_breakdown",
        duration_months=3,
        severity=3,
    )

    assert event_weight(bundle, unstable.state, beater_total_failure) >= event_weight(bundle, clean.state, beater_total_failure) * 2


def test_phase_status_arc_severe_transport_surfaces_rescue_window_alongside_failure(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.current_month = 18
    state.player.transport.option_id = "beater_car"
    state.player.transport.reliability_score = 28
    state.player.monthly_surplus = -140

    start_status_arc(
        bundle,
        state,
        "transport_unstable",
        source_event_id="beater_total_failure",
        duration_months=4,
        severity=3,
    )

    top_ids = _top_weighted_event_ids(bundle, state)

    assert "beater_total_failure" in top_ids
    assert "used_car_window" in top_ids


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


def test_market_chaser_captures_more_upside_than_cushion_first_in_strong_month(bundle, controller_factory):
    strong_bundle = bundle.model_copy(deep=True)
    strong_bundle.config = strong_bundle.config.model_copy(
        update={
            "default_market_regime_id": "strong",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "strong"],
        }
    )
    cushion = controller_factory()
    chaser = controller_factory()
    for controller in (cushion, chaser):
        controller.state.player.high_interest_savings = 1000
        controller.state.player.index_fund = 5000
        controller.state.player.aggressive_growth_fund = 3000
    cushion.state.player.wealth_strategy_id = "cushion_first"
    chaser.state.player.wealth_strategy_id = "market_chaser"

    apply_wealth_returns(strong_bundle, cushion.state, Random(7))
    apply_wealth_returns(strong_bundle, chaser.state, Random(7))

    cushion_total = cushion.state.player.high_interest_savings + cushion.state.player.index_fund + cushion.state.player.aggressive_growth_fund
    chaser_total = chaser.state.player.high_interest_savings + chaser.state.player.index_fund + chaser.state.player.aggressive_growth_fund

    assert chaser_total > cushion_total


def test_cushion_first_softens_correction_losses_vs_market_chaser(bundle, controller_factory):
    correction_bundle = bundle.model_copy(deep=True)
    correction_bundle.config = correction_bundle.config.model_copy(
        update={
            "default_market_regime_id": "correction",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "correction"],
        }
    )
    cushion = controller_factory()
    chaser = controller_factory()
    for controller in (cushion, chaser):
        controller.state.player.high_interest_savings = 1000
        controller.state.player.index_fund = 5000
        controller.state.player.aggressive_growth_fund = 3000
    cushion.state.player.wealth_strategy_id = "cushion_first"
    chaser.state.player.wealth_strategy_id = "market_chaser"

    apply_wealth_returns(correction_bundle, cushion.state, Random(7))
    apply_wealth_returns(correction_bundle, chaser.state, Random(7))

    cushion_total = cushion.state.player.high_interest_savings + cushion.state.player.index_fund + cushion.state.player.aggressive_growth_fund
    chaser_total = chaser.state.player.high_interest_savings + chaser.state.player.index_fund + chaser.state.player.aggressive_growth_fund

    assert cushion_total > chaser_total


def test_debt_crusher_uses_positive_months_to_reduce_debt(bundle, controller_factory):
    strong_bundle = bundle.model_copy(deep=True)
    strong_bundle.config = strong_bundle.config.model_copy(
        update={
            "default_market_regime_id": "strong",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "strong"],
        }
    )
    controller = controller_factory()
    controller.state.player.wealth_strategy_id = "debt_crusher"
    controller.state.player.debt = 9000
    controller.state.player.high_interest_savings = 800
    controller.state.player.index_fund = 3500
    controller.state.player.aggressive_growth_fund = 0
    starting_debt = controller.state.player.debt

    apply_wealth_returns(strong_bundle, controller.state, Random(7))

    assert controller.state.player.debt < starting_debt


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


def test_credit_driven_events_change_with_credit_state(bundle, controller_factory):
    low_credit = controller_factory()
    low_credit.state.current_month = 6
    low_credit.state.player.credit_score = 540
    low_credit.state.player.debt = 2400

    high_credit = controller_factory()
    high_credit.state.current_month = 6
    high_credit.state.player.credit_score = 760
    high_credit.state.player.debt = 2400

    low_ids = {event.id for event in eligible_events(bundle, low_credit.state)}
    high_ids = {event.id for event in eligible_events(bundle, high_credit.state)}

    assert "credit_limit_review" in low_ids
    assert "refinance_window" in high_ids


def test_branch_specific_events_change_with_selected_branch(bundle, controller_factory):
    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    management.state.current_month = 10
    management.state.player.career.tier_index = 1
    management.state.player.career.branch_id = "retail_management_track"

    sales = controller_factory(opening_path_id="full_time_work")
    sales.change_career("retail_service")
    sales.state.current_month = 10
    sales.state.player.career.tier_index = 1
    sales.state.player.career.branch_id = "retail_sales_track"
    sales.state.player.social_stability = 68

    management_ids = {event.id for event in eligible_events(bundle, management.state)}
    sales_ids = {event.id for event in eligible_events(bundle, sales.state)}

    assert "retail_inventory_crunch" in management_ids
    assert "sales_whale_month" not in management_ids
    assert "sales_whale_month" in sales_ids
    assert "retail_inventory_crunch" not in sales_ids


def test_late_run_branch_promotion_offers_diverge_by_retail_branch(bundle, controller_factory):
    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    management.state.current_month = 22
    management.state.player.career.tier_index = 2
    management.state.player.career.branch_id = "retail_management_track"
    management.state.player.social_stability = 58

    sales = controller_factory(opening_path_id="full_time_work")
    sales.change_career("retail_service")
    sales.state.current_month = 22
    sales.state.player.career.tier_index = 2
    sales.state.player.career.branch_id = "retail_sales_track"
    sales.state.player.social_stability = 68

    management_ids = {event.id for event in eligible_events(bundle, management.state)}
    sales_ids = {event.id for event in eligible_events(bundle, sales.state)}

    assert "retail_leadership_offer" in management_ids
    assert "sales_territory_offer" not in management_ids
    assert "sales_territory_offer" in sales_ids
    assert "retail_leadership_offer" not in sales_ids


def test_late_run_branch_promotion_offers_diverge_by_warehouse_branch(bundle, controller_factory):
    dispatch = controller_factory(opening_path_id="full_time_work")
    dispatch.state.current_month = 22
    dispatch.state.player.career.tier_index = 2
    dispatch.state.player.career.branch_id = "warehouse_dispatch_track"
    dispatch.state.player.social_stability = 52
    dispatch.state.player.transport.reliability_score = 76

    equipment = controller_factory(opening_path_id="full_time_work")
    equipment.state.current_month = 22
    equipment.state.player.career.tier_index = 2
    equipment.state.player.career.branch_id = "warehouse_equipment_track"
    equipment.state.player.transport.reliability_score = 78
    equipment.state.player.energy = 56

    dispatch_ids = {event.id for event in eligible_events(bundle, dispatch.state)}
    equipment_ids = {event.id for event in eligible_events(bundle, equipment.state)}

    assert "dispatch_lead_offer" in dispatch_ids
    assert "equipment_shift_contract" not in dispatch_ids
    assert "equipment_shift_contract" in equipment_ids
    assert "dispatch_lead_offer" not in equipment_ids


def test_clienteling_branch_has_unique_opportunity_and_failure_hooks(bundle, controller_factory):
    stable = controller_factory(opening_path_id="full_time_work")
    stable.change_career("retail_service")
    stable.state.current_month = 20
    stable.state.player.career.tier_index = 2
    stable.state.player.career.branch_id = "retail_clienteling_track"
    stable.state.player.social_stability = 72
    stable.state.player.stress = 42

    strained = controller_factory(opening_path_id="full_time_work")
    strained.change_career("retail_service")
    strained.state.current_month = 20
    strained.state.player.career.tier_index = 2
    strained.state.player.career.branch_id = "retail_clienteling_track"
    strained.state.player.social_stability = 44
    strained.state.player.stress = 74

    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    management.state.current_month = 20
    management.state.player.career.tier_index = 2
    management.state.player.career.branch_id = "retail_management_track"
    management.state.player.social_stability = 72

    stable_ids = {event.id for event in eligible_events(bundle, stable.state)}
    strained_ids = {event.id for event in eligible_events(bundle, strained.state)}
    management_ids = {event.id for event in eligible_events(bundle, management.state)}

    assert "clienteling_key_account_offer" in stable_ids
    assert "client_book_attrition_risk" not in stable_ids
    assert "client_book_attrition_risk" in strained_ids
    assert "clienteling_key_account_offer" not in management_ids


def test_warehouse_ops_branch_has_unique_failure_and_offer_hooks(bundle, controller_factory):
    stable_ops = controller_factory(opening_path_id="full_time_work")
    stable_ops.state.current_month = 22
    stable_ops.state.player.career.tier_index = 2
    stable_ops.state.player.career.branch_id = "warehouse_ops_track"
    stable_ops.state.player.transport.reliability_score = 78
    stable_ops.state.player.energy = 58
    stable_ops.state.player.stress = 48

    strained_ops = controller_factory(opening_path_id="full_time_work")
    strained_ops.state.current_month = 22
    strained_ops.state.player.career.tier_index = 2
    strained_ops.state.player.career.branch_id = "warehouse_ops_track"
    strained_ops.state.player.transport.reliability_score = 58
    strained_ops.state.player.energy = 33
    strained_ops.state.player.stress = 76

    dispatch = controller_factory(opening_path_id="full_time_work")
    dispatch.state.current_month = 22
    dispatch.state.player.career.tier_index = 2
    dispatch.state.player.career.branch_id = "warehouse_dispatch_track"
    dispatch.state.player.transport.reliability_score = 78
    dispatch.state.player.energy = 58
    dispatch.state.player.stress = 48

    stable_ids = {event.id for event in eligible_events(bundle, stable_ops.state)}
    strained_ids = {event.id for event in eligible_events(bundle, strained_ops.state)}
    dispatch_ids = {event.id for event in eligible_events(bundle, dispatch.state)}

    assert "warehouse_foreman_offer" in stable_ids
    assert "warehouse_safety_crunch" not in stable_ids
    assert "warehouse_safety_crunch" in strained_ids
    assert "warehouse_foreman_offer" not in dispatch_ids


def test_warehouse_equipment_branch_has_unique_failure_and_offer_hooks(bundle, controller_factory):
    stable_equipment = controller_factory(opening_path_id="full_time_work")
    stable_equipment.state.current_month = 24
    stable_equipment.state.player.career.tier_index = 2
    stable_equipment.state.player.career.branch_id = "warehouse_equipment_track"
    stable_equipment.state.player.transport.reliability_score = 82
    stable_equipment.state.player.energy = 60
    stable_equipment.state.player.stress = 44
    stable_equipment.state.player.social_stability = 56

    strained_equipment = controller_factory(opening_path_id="full_time_work")
    strained_equipment.state.current_month = 24
    strained_equipment.state.player.career.tier_index = 2
    strained_equipment.state.player.career.branch_id = "warehouse_equipment_track"
    strained_equipment.state.player.transport.reliability_score = 56
    strained_equipment.state.player.energy = 34
    strained_equipment.state.player.stress = 74
    strained_equipment.state.player.social_stability = 42

    dispatch = controller_factory(opening_path_id="full_time_work")
    dispatch.state.current_month = 24
    dispatch.state.player.career.tier_index = 2
    dispatch.state.player.career.branch_id = "warehouse_dispatch_track"
    dispatch.state.player.transport.reliability_score = 82
    dispatch.state.player.energy = 60
    dispatch.state.player.stress = 44
    dispatch.state.player.social_stability = 56

    stable_ids = {event.id for event in eligible_events(bundle, stable_equipment.state)}
    strained_ids = {event.id for event in eligible_events(bundle, strained_equipment.state)}
    dispatch_ids = {event.id for event in eligible_events(bundle, dispatch.state)}

    assert "equipment_specialist_offer" in stable_ids
    assert "equipment_safety_recall" not in stable_ids
    assert "equipment_safety_recall" in strained_ids
    assert "equipment_specialist_offer" not in dispatch_ids


def test_wealth_strategy_events_change_with_strategy(bundle, controller_factory):
    cushion = controller_factory(opening_path_id="stay_home_stack_cash")
    cushion.state.current_month = 14
    cushion.state.current_market_regime_id = "correction"
    cushion.change_wealth_strategy("cushion_first")

    chaser = controller_factory(opening_path_id="stay_home_stack_cash")
    chaser.state.current_month = 14
    chaser.state.current_market_regime_id = "correction"
    chaser.change_wealth_strategy("market_chaser")

    cushion_ids = {event.id for event in eligible_events(bundle, cushion.state)}
    chaser_ids = {event.id for event in eligible_events(bundle, chaser.state)}

    assert "dry_powder_window" in cushion_ids
    assert "market_panic_window" not in cushion_ids
    assert "market_panic_window" in chaser_ids
    assert "dry_powder_window" not in chaser_ids


def test_market_chaser_has_unique_liquidity_trap_event(bundle, controller_factory):
    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser.state.current_month = 16
    chaser.state.player.wealth_strategy_id = "market_chaser"
    chaser.state.current_market_regime_id = "correction"
    chaser.state.player.debt = 11200
    chaser.state.player.cash = 120
    chaser.state.player.savings = 80
    chaser.state.player.monthly_surplus = -140
    chaser.state.player.credit_score = 612

    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    cushion.state.current_month = 16
    cushion.state.player.wealth_strategy_id = "cushion_first"
    cushion.state.current_market_regime_id = "correction"
    cushion.state.player.debt = 11200
    cushion.state.player.cash = 120
    cushion.state.player.savings = 80
    cushion.state.player.monthly_surplus = -140
    cushion.state.player.credit_score = 612

    chaser_ids = {event.id for event in eligible_events(bundle, chaser.state)}
    cushion_ids = {event.id for event in eligible_events(bundle, cushion.state)}

    assert "market_margin_call" in chaser_ids
    assert "market_margin_call" not in cushion_ids


def test_debt_crusher_has_unique_cash_tightrope_event(bundle, controller_factory):
    crusher = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    crusher.state.current_month = 14
    crusher.state.player.wealth_strategy_id = "debt_crusher"
    crusher.state.player.debt = 9600
    crusher.state.player.cash = 180
    crusher.state.player.savings = 60
    crusher.state.player.monthly_surplus = 90
    crusher.state.player.stress = 62

    steady = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    steady.state.current_month = 14
    steady.state.player.wealth_strategy_id = "steady_builder"
    steady.state.player.debt = 9600
    steady.state.player.cash = 180
    steady.state.player.savings = 60
    steady.state.player.monthly_surplus = 90
    steady.state.player.stress = 62

    crusher_ids = {event.id for event in eligible_events(bundle, crusher.state)}
    steady_ids = {event.id for event in eligible_events(bundle, steady.state)}

    assert "debt_paydown_tightrope" in crusher_ids
    assert "debt_paydown_tightrope" not in steady_ids


def test_cushion_first_has_unique_strong_market_regret_event(bundle, controller_factory):
    cushion = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    cushion.state.current_month = 16
    cushion.state.player.wealth_strategy_id = "cushion_first"
    cushion.state.current_market_regime_id = "strong"
    cushion.state.player.cash = 3200
    cushion.state.player.savings = 2400
    cushion.state.player.debt = 1800
    cushion.state.player.monthly_surplus = 380

    steady = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    steady.state.current_month = 16
    steady.state.player.wealth_strategy_id = "steady_builder"
    steady.state.current_market_regime_id = "strong"
    steady.state.player.cash = 3200
    steady.state.player.savings = 2400
    steady.state.player.debt = 1800
    steady.state.player.monthly_surplus = 380

    cushion_ids = {event.id for event in eligible_events(bundle, cushion.state)}
    steady_ids = {event.id for event in eligible_events(bundle, steady.state)}

    assert "cash_drag_regret" in cushion_ids
    assert "cash_drag_regret" not in steady_ids


def test_credit_specific_event_pools_change_with_housing_and_transport_doors(bundle, controller_factory):
    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    fragile.state.current_month = 14
    fragile.state.player.housing.option_id = "roommates"
    fragile.state.player.credit_score = 560
    fragile.state.player.debt = 5200

    prime = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    prime.state.current_month = 14
    prime.state.player.transport.option_id = "reliable_used_car"
    prime.state.player.credit_score = 760
    prime.state.player.debt = 1800

    fragile_ids = {event.id for event in eligible_events(bundle, fragile.state)}
    prime_ids = {event.id for event in eligible_events(bundle, prime.state)}

    assert "security_deposit_shock" in fragile_ids
    assert "prime_vehicle_offer" not in fragile_ids
    assert "prime_vehicle_offer" in prime_ids
    assert "security_deposit_shock" not in prime_ids


def test_credit_rebuild_event_requires_clean_stable_repair_context(bundle, controller_factory):
    repair = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    repair.state.current_month = 14
    repair.state.player.credit_score = 565
    repair.state.player.debt = 3200
    repair.state.player.cash = 2400
    repair.state.player.savings = 1600
    repair.state.player.monthly_surplus = 260
    repair.state.player.housing.missed_payment_streak = 0

    strained = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    strained.state.current_month = 14
    strained.state.player.credit_score = 565
    strained.state.player.debt = 9200
    strained.state.player.cash = 100
    strained.state.player.savings = 0
    strained.state.player.monthly_surplus = -140
    strained.state.player.housing.missed_payment_streak = 1

    repair_ids = {event.id for event in eligible_events(bundle, repair.state)}
    strained_ids = {event.id for event in eligible_events(bundle, strained.state)}

    assert "credit_rebuild_window" in repair_ids
    assert "credit_rebuild_window" not in strained_ids


def test_credit_access_events_distinguish_fragile_transport_from_strong_housing(bundle, controller_factory):
    fragile_driver = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    fragile_driver.state.current_month = 18
    fragile_driver.state.player.transport.option_id = "financed_car"
    fragile_driver.state.player.credit_score = 575
    fragile_driver.state.player.debt = 8200

    stable_renter = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    stable_renter.state.current_month = 18
    stable_renter.state.player.housing.option_id = "solo_rental"
    stable_renter.state.player.housing.housing_stability = 78
    stable_renter.state.player.credit_score = 748
    stable_renter.state.player.debt = 2400

    fragile_ids = {event.id for event in eligible_events(bundle, fragile_driver.state)}
    stable_ids = {event.id for event in eligible_events(bundle, stable_renter.state)}

    assert "financed_car_insurance_spike" in fragile_ids
    assert "good_tenant_renewal" not in fragile_ids
    assert "good_tenant_renewal" in stable_ids
    assert "financed_car_insurance_spike" not in stable_ids


def test_credit_pressure_blocks_solo_rental_without_strong_credit(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 690
    controller.state.player.debt = 16500
    controller.state.player.monthly_surplus = 180

    allowed, reason = can_switch_housing(bundle, controller.state, "solo_rental")

    assert not allowed
    assert "stronger credit" in reason.lower() or "debt" in reason.lower()


def test_negative_month_blocks_financed_car_even_with_score(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 680
    controller.state.player.debt = 9000
    controller.state.player.monthly_surplus = -160

    allowed, reason = can_switch_transport(bundle, controller.state, "financed_car")

    assert not allowed
    assert "monthly" in reason.lower() or "payment" in reason.lower()


def test_fragile_credit_and_debt_can_block_roommates_access(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.housing.option_id = "student_residence"
    controller.state.player.credit_score = 558
    controller.state.player.debt = 10800
    controller.state.player.monthly_surplus = -180

    allowed, reason = can_switch_housing(bundle, controller.state, "roommates")

    assert not allowed
    assert "credit" in reason.lower() or "debt" in reason.lower()


def test_fair_credit_with_thin_surplus_blocks_financed_car(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 645
    controller.state.player.debt = 9800
    controller.state.player.monthly_surplus = 40

    allowed, reason = can_switch_transport(bundle, controller.state, "financed_car")

    assert not allowed
    assert "credit" in reason.lower() or "monthly" in reason.lower() or "debt" in reason.lower()


def test_strong_credit_and_stable_finances_unlock_financed_doors(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 748
    controller.state.player.debt = 4200
    controller.state.player.monthly_surplus = 320
    controller.state.player.cash = 2500

    housing_allowed, _ = can_switch_housing(bundle, controller.state, "solo_rental")
    transport_allowed, _ = can_switch_transport(bundle, controller.state, "financed_car")

    assert housing_allowed
    assert transport_allowed


def test_phase4_credit_missed_obligation_streak_blocks_core_credit_doors(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 738
    controller.state.player.debt = 7800
    controller.state.player.monthly_surplus = 240
    controller.state.player.cash = 2400
    controller.state.player.savings = 1400
    controller.state.player.credit_missed_obligation_streak = 2

    housing_allowed, housing_reason = can_switch_housing(bundle, controller.state, "solo_rental")
    transport_allowed, transport_reason = can_switch_transport(bundle, controller.state, "financed_car")

    assert not housing_allowed
    assert not transport_allowed
    assert "payment" in housing_reason.lower() or "obligation" in housing_reason.lower() or "history" in housing_reason.lower()
    assert "payment" in transport_reason.lower() or "obligation" in transport_reason.lower() or "history" in transport_reason.lower()


def test_phase4_refinance_window_requires_recent_credit_stability(bundle, controller_factory):
    stable = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    stable.state.current_month = 14
    stable.state.player.credit_score = 748
    stable.state.player.debt = 8600
    stable.state.player.monthly_surplus = -60
    stable.state.player.cash = 240
    stable.state.player.savings = 180
    stable.state.player.credit_missed_obligation_streak = 0

    unstable = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    unstable.state.current_month = 14
    unstable.state.player.credit_score = 748
    unstable.state.player.debt = 8600
    unstable.state.player.monthly_surplus = -60
    unstable.state.player.cash = 240
    unstable.state.player.savings = 180
    unstable.state.player.credit_missed_obligation_streak = 2

    stable_ids = {event.id for event in eligible_events(bundle, stable.state)}
    unstable_ids = {event.id for event in eligible_events(bundle, unstable.state)}

    assert "refinance_window" in stable_ids
    assert "refinance_window" not in unstable_ids


def test_phase4_credit_penalty_severity_scales_with_missed_obligation_streak(bundle, controller_factory):
    event = next(item for item in bundle.events if item.id == "security_deposit_shock")

    stable_file = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    stable_file.state.player.credit_score = 568
    stable_file.state.player.debt = 5600
    stable_file.state.player.monthly_surplus = -90
    stable_file.state.player.credit_missed_obligation_streak = 0

    stressed_file = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    stressed_file.state.player.credit_score = 568
    stressed_file.state.player.debt = 5600
    stressed_file.state.player.monthly_surplus = -90
    stressed_file.state.player.credit_missed_obligation_streak = 3

    assert event_severity_multiplier(bundle, stressed_file.state, event) > event_severity_multiplier(bundle, stable_file.state, event)


def test_phase4_credit_rebuild_window_prefers_rebuild_streak(bundle, controller_factory):
    rebuilding = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    rebuilding.state.current_month = 14
    rebuilding.state.player.credit_score = 565
    rebuilding.state.player.debt = 3200
    rebuilding.state.player.cash = 2000
    rebuilding.state.player.savings = 1400
    rebuilding.state.player.monthly_surplus = 260
    rebuilding.state.player.housing.missed_payment_streak = 0
    rebuilding.state.player.credit_rebuild_streak = 3

    flat = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    flat.state.current_month = 14
    flat.state.player.credit_score = 565
    flat.state.player.debt = 3200
    flat.state.player.cash = 2000
    flat.state.player.savings = 1400
    flat.state.player.monthly_surplus = 260
    flat.state.player.housing.missed_payment_streak = 0
    flat.state.player.credit_rebuild_streak = 0

    rebuild_event = next(event for event in bundle.events if event.id == "credit_rebuild_window")
    assert event_weight(bundle, rebuilding.state, rebuild_event) > event_weight(bundle, flat.state, rebuild_event)


def test_phase4_weak_vs_strong_credit_contrast_scenario(bundle, controller_factory):
    weak = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    weak.state.current_month = 14
    weak.state.player.credit_score = 556
    weak.state.player.debt = 12800
    weak.state.player.cash = 120
    weak.state.player.savings = 0
    weak.state.player.monthly_surplus = -150
    weak.state.player.credit_missed_obligation_streak = 3
    weak.state.player.credit_utilization_pressure = 84
    weak.state.player.transport.option_id = "beater_car"

    strong = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    strong.state.current_month = 14
    strong.state.player.credit_score = 754
    strong.state.player.debt = 2600
    strong.state.player.cash = 2400
    strong.state.player.savings = 1600
    strong.state.player.monthly_surplus = 320
    strong.state.player.credit_missed_obligation_streak = 0
    strong.state.player.credit_rebuild_streak = 2
    strong.state.player.credit_utilization_pressure = 34
    strong.state.player.transport.option_id = "transit"

    weak_housing_allowed, _ = can_switch_housing(bundle, weak.state, "solo_rental")
    weak_transport_allowed, _ = can_switch_transport(bundle, weak.state, "financed_car")
    strong_housing_allowed, _ = can_switch_housing(bundle, strong.state, "solo_rental")
    strong_transport_allowed, _ = can_switch_transport(bundle, strong.state, "financed_car")

    weak_ids = {event.id for event in eligible_events(bundle, weak.state)}
    strong_ids = {event.id for event in eligible_events(bundle, strong.state)}

    security_deposit_shock = next(event for event in bundle.events if event.id == "security_deposit_shock")
    weak_severity = event_severity_multiplier(bundle, weak.state, security_deposit_shock)
    strong_severity = event_severity_multiplier(bundle, strong.state, security_deposit_shock)

    assert not weak_housing_allowed
    assert not weak_transport_allowed
    assert strong_housing_allowed
    assert strong_transport_allowed
    assert "collections_warning" in weak_ids
    assert "refinance_window" not in weak_ids
    assert "refinance_window" in strong_ids
    assert weak_severity > strong_severity


def test_phase_status_arc_credit_tightens_financing_door_and_score(bundle, controller_factory):
    clean = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    squeezed = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    for controller in (clean, squeezed):
        controller.state.player.credit_score = 690
        controller.state.player.debt = 7000
        controller.state.player.monthly_surplus = 220
        controller.state.player.cash = 1800
        controller.state.player.savings = 1200
        controller.state.player.transport.option_id = "transit"

    clean_allowed, _ = can_switch_transport(bundle, clean.state, "financed_car")
    start_status_arc(
        bundle,
        squeezed.state,
        "credit_squeeze",
        source_event_id="collections_warning",
        duration_months=4,
        severity=2,
    )
    squeezed_allowed, squeeze_reason = can_switch_transport(bundle, squeezed.state, "financed_car")

    clean_score = calculate_final_score(bundle, clean.state).final_score
    squeezed_score = calculate_final_score(bundle, squeezed.state).final_score

    assert clean_allowed
    assert not squeezed_allowed
    assert "credit" in squeeze_reason.lower() or "financing" in squeeze_reason.lower()
    assert squeezed_score < clean_score


def test_phase_status_arc_education_raises_probation_followup_pressure(bundle, controller_factory):
    clean = controller_factory(opening_path_id="college_university")
    slipping = controller_factory(opening_path_id="college_university")
    for controller in (clean, slipping):
        controller.state.player.education.program_id = "full_time_university"
        controller.state.player.education.is_active = True
        controller.state.player.education.intensity_level = "intensive"
        controller.state.player.stress = 68
        controller.state.player.energy = 38

    probation = next(event for event in bundle.events if event.id == "exam_probation_hearing")
    start_status_arc(
        bundle,
        slipping.state,
        "education_slipping",
        source_event_id="overtime_exam_collision",
        duration_months=3,
        severity=2,
    )

    assert event_weight(bundle, slipping.state, probation) > event_weight(bundle, clean.state, probation)


def test_phase_status_arc_severe_education_surfaces_funding_review_pressure(bundle, controller_factory):
    controller = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    state = controller.state
    state.current_month = 16
    state.player.education.program_id = "full_time_university"
    state.player.education.is_active = True
    state.player.education.intensity_level = "intensive"
    state.player.stress = 74
    state.player.energy = 36

    start_status_arc(
        bundle,
        state,
        "education_slipping",
        source_event_id="exam_probation_hearing",
        duration_months=3,
        severity=3,
    )

    top_ids = _top_weighted_event_ids(bundle, state)

    assert "exam_probation_hearing" in top_ids
    assert "academic_funding_review" in top_ids


def test_phase_status_arc_lease_raises_followup_pressure_and_score_penalty(bundle, controller_factory):
    stable = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    pressured = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    stable.state.current_month = 14
    stable.state.player.housing.option_id = "parents"
    stable.state.player.housing.housing_stability = 82
    stable.state.player.credit_score = 742
    stable.state.player.debt = 1800
    stable.state.player.monthly_surplus = 320

    pressured.state.current_month = 14
    pressured.state.player.housing.option_id = "solo_rental"
    pressured.state.player.housing.housing_stability = 34
    pressured.state.player.credit_score = 556
    pressured.state.player.debt = 12200
    pressured.state.player.cash = 120
    pressured.state.player.savings = 0
    pressured.state.player.monthly_surplus = -220
    start_status_arc(
        bundle,
        pressured.state,
        "lease_pressure",
        source_event_id="lease_default_warning",
        duration_months=4,
        severity=2,
    )

    enforcement = next(event for event in bundle.events if event.id == "lease_enforcement_notice")

    stable_score = calculate_final_score(bundle, stable.state).final_score
    pressured_score = calculate_final_score(bundle, pressured.state).final_score

    assert event_weight(bundle, pressured.state, enforcement) > event_weight(bundle, stable.state, enforcement)
    assert pressured_score < stable_score


def test_phase_status_arc_severe_lease_pushes_cushion_first_reserve_window_near_top(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.current_month = 18
    state.player.housing.option_id = "solo_rental"
    state.player.housing.housing_stability = 34
    state.player.monthly_surplus = -180
    state.player.wealth_strategy_id = "cushion_first"

    start_status_arc(
        bundle,
        state,
        "lease_pressure",
        source_event_id="lease_enforcement_notice",
        duration_months=4,
        severity=3,
    )

    top_ids = _top_weighted_event_ids(bundle, state, limit=4)

    assert "lease_enforcement_notice" in top_ids
    assert "reserve_deployment_window" in top_ids


def test_phase_status_arc_burnout_raises_followup_pressure_and_score_penalty(bundle, controller_factory):
    stable = controller_factory(opening_path_id="full_time_work")
    strained = controller_factory(opening_path_id="full_time_work")

    stable.state.current_month = 10
    stable.state.player.selected_focus_action_id = "social_maintenance"
    stable.state.player.stress = 48
    stable.state.player.energy = 60

    strained.state.current_month = 10
    strained.state.player.selected_focus_action_id = "overtime"
    strained.state.player.stress = 76
    strained.state.player.energy = 30
    start_status_arc(
        bundle,
        strained.state,
        "burnout_risk",
        source_event_id="overtime_attrition_warning",
        duration_months=3,
        severity=2,
    )

    burnout = next(event for event in bundle.events if event.id == "burnout_month")

    stable_score = calculate_final_score(bundle, stable.state).final_score
    strained_score = calculate_final_score(bundle, strained.state).final_score

    assert event_weight(bundle, strained.state, burnout) > event_weight(bundle, stable.state, burnout)
    assert strained_score < stable_score


def test_phase_status_arc_promotion_raises_future_opportunity_weight_and_score(bundle, controller_factory):
    flat = controller_factory(opening_path_id="full_time_work")
    open_window = controller_factory(opening_path_id="full_time_work")

    for controller in (flat, open_window):
        controller.change_career("retail_service")
        controller.state.current_month = 18
        controller.state.player.career.tier_index = 1
        controller.state.player.career.promotion_progress = 8
        controller.state.player.career.promotion_momentum = 64
        controller.state.player.credit_score = 708
        controller.state.player.housing.housing_stability = 68
        controller.state.player.transport.reliability_score = 72
        controller.state.player.social_stability = 60
        controller.state.player.stress = 44
        controller.state.player.energy = 62

    start_status_arc(
        bundle,
        open_window.state,
        "promotion_window_open",
        source_event_id="promotion_window",
        duration_months=3,
        severity=2,
    )
    open_window.state.pending_promotion_branch_track_id = open_window.state.player.career.track_id

    promotion = next(event for event in bundle.events if event.id == "promotion_window")

    flat_score = calculate_final_score(bundle, flat.state).final_score
    open_score = calculate_final_score(bundle, open_window.state).final_score

    assert event_weight(bundle, open_window.state, promotion) > event_weight(bundle, flat.state, promotion)
    assert open_score > flat_score


def test_phase_status_arc_promotion_boosts_office_advancement_charter(bundle, controller_factory):
    closed = controller_factory(opening_path_id="full_time_work")
    opened = controller_factory(opening_path_id="full_time_work")

    for controller in (closed, opened):
        controller.state.current_month = 24
        controller.state.player.career.track_id = "office_admin"
        controller.state.player.career.branch_id = "office_operations_track"
        controller.state.player.career.tier_index = 3
        controller.state.player.social_stability = 66
        controller.state.player.energy = 68
        controller.state.player.stress = 42

    office_charter = next(event for event in bundle.events if event.id == "office_advancement_charter")

    start_status_arc(
        bundle,
        opened.state,
        "promotion_window_open",
        source_event_id="promotion_window",
        duration_months=2,
        severity=2,
    )

    closed_weight = event_weight(bundle, closed.state, office_charter)
    opened_weight = event_weight(bundle, opened.state, office_charter)
    open_top = _top_weighted_event_ids(bundle, opened.state, limit=6)

    assert opened_weight > closed_weight
    assert "office_advancement_charter" in open_top


@pytest.mark.parametrize(
    ("track_id", "branch_id", "tag", "expected_event_id"),
    [
        ("sales", "sales_volume_closer_track", "sales_hunter_lane", "sales_hunter_pressure_cycle"),
        ("sales", "sales_account_manager_track", "sales_book_builder_lane", "sales_book_compound_window"),
        ("sales", "sales_enterprise_strategy_track", "sales_strategic_scope_lane", "sales_strategic_scope_dividend"),
        (
            "degree_gated_professional",
            "professional_technical_specialist_track",
            "professional_specialist_lane",
            "professional_specialist_reputation_dividend",
        ),
        (
            "degree_gated_professional",
            "professional_client_lead_track",
            "professional_scope_lane",
            "professional_scope_politics_wave",
        ),
        (
            "degree_gated_professional",
            "professional_people_ops_track",
            "professional_ops_anchor_lane",
            "professional_ops_stability_dividend",
        ),
    ],
)
def test_sales_and_professional_tagged_lanes_surface_late_followups_in_top_band(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    tag,
    expected_event_id,
):
    controller = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    state = controller.state
    state.current_month = 28
    state.player.career.track_id = track_id
    state.player.career.branch_id = branch_id
    state.player.career.tier_index = 3
    state.player.stress = 58
    state.player.energy = 58
    state.player.social_stability = 64
    state.player.credit_score = 660
    state.player.monthly_surplus = 90
    state.player.transport.reliability_score = 72
    state.player.persistent_tags = [tag]

    top_ids = _top_weighted_event_ids(bundle, state, limit=7)

    assert expected_event_id in top_ids


def test_phase5_market_chaser_has_amplified_upside_and_downside_vs_steady_builder(bundle, controller_factory):
    strong_bundle = bundle.model_copy(deep=True)
    strong_bundle.config = strong_bundle.config.model_copy(
        update={
            "default_market_regime_id": "strong",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "strong"],
        }
    )
    correction_bundle = bundle.model_copy(deep=True)
    correction_bundle.config = correction_bundle.config.model_copy(
        update={
            "default_market_regime_id": "correction",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "correction"],
        }
    )

    def _build(strategy_id: str):
        controller = controller_factory(opening_path_id="stay_home_stack_cash")
        controller.state.player.wealth_strategy_id = strategy_id
        controller.state.player.high_interest_savings = 1500
        controller.state.player.index_fund = 6000
        controller.state.player.aggressive_growth_fund = 3000
        controller.state.player.debt = 7000
        return controller

    strong_chaser = _build("market_chaser")
    strong_steady = _build("steady_builder")
    strong_chaser_before = (
        strong_chaser.state.player.high_interest_savings
        + strong_chaser.state.player.index_fund
        + strong_chaser.state.player.aggressive_growth_fund
    )
    strong_steady_before = (
        strong_steady.state.player.high_interest_savings
        + strong_steady.state.player.index_fund
        + strong_steady.state.player.aggressive_growth_fund
    )

    apply_wealth_returns(strong_bundle, strong_chaser.state, Random(7))
    apply_wealth_returns(strong_bundle, strong_steady.state, Random(7))

    strong_chaser_gain = (
        strong_chaser.state.player.high_interest_savings
        + strong_chaser.state.player.index_fund
        + strong_chaser.state.player.aggressive_growth_fund
        - strong_chaser_before
    )
    strong_steady_gain = (
        strong_steady.state.player.high_interest_savings
        + strong_steady.state.player.index_fund
        + strong_steady.state.player.aggressive_growth_fund
        - strong_steady_before
    )

    correction_chaser = _build("market_chaser")
    correction_steady = _build("steady_builder")
    correction_chaser_before = (
        correction_chaser.state.player.high_interest_savings
        + correction_chaser.state.player.index_fund
        + correction_chaser.state.player.aggressive_growth_fund
    )
    correction_steady_before = (
        correction_steady.state.player.high_interest_savings
        + correction_steady.state.player.index_fund
        + correction_steady.state.player.aggressive_growth_fund
    )

    apply_wealth_returns(correction_bundle, correction_chaser.state, Random(7))
    apply_wealth_returns(correction_bundle, correction_steady.state, Random(7))

    correction_chaser_swing = (
        correction_chaser.state.player.high_interest_savings
        + correction_chaser.state.player.index_fund
        + correction_chaser.state.player.aggressive_growth_fund
        - correction_chaser_before
    )
    correction_steady_swing = (
        correction_steady.state.player.high_interest_savings
        + correction_steady.state.player.index_fund
        + correction_steady.state.player.aggressive_growth_fund
        - correction_steady_before
    )

    assert strong_chaser_gain - strong_steady_gain >= 60
    assert correction_chaser_swing <= (correction_steady_swing - 110)


def test_phase5_market_chaser_forced_liquidation_has_extra_asset_loss(bundle, controller_factory):
    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    cushion.state.player.wealth_strategy_id = "cushion_first"
    cushion.state.player.cash = 0
    cushion.state.player.savings = 0
    cushion.state.player.high_interest_savings = 300
    cushion.state.player.index_fund = 1500
    cushion.state.player.aggressive_growth_fund = 900

    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser.state.player.wealth_strategy_id = "market_chaser"
    chaser.state.player.cash = 0
    chaser.state.player.savings = 0
    chaser.state.player.high_interest_savings = 300
    chaser.state.player.index_fund = 1500
    chaser.state.player.aggressive_growth_fund = 900

    cushion_raised = emergency_liquidation(cushion.state, 1000)
    chaser_raised = emergency_liquidation(chaser.state, 1000)

    cushion_remaining = (
        cushion.state.player.high_interest_savings
        + cushion.state.player.index_fund
        + cushion.state.player.aggressive_growth_fund
    )
    chaser_remaining = (
        chaser.state.player.high_interest_savings
        + chaser.state.player.index_fund
        + chaser.state.player.aggressive_growth_fund
    )

    assert cushion_raised == 1000
    assert chaser_raised == 1000
    assert chaser_remaining < cushion_remaining


def test_phase5_cushion_first_strong_market_surfaces_cash_drag_regret_in_top_five(bundle, controller_factory):
    controller = controller_factory(
        opening_path_id="stay_home_stack_cash",
        city_id="hometown_low_cost",
        family_support_level_id="high",
        savings_band_id="solid",
    )
    state = controller.state
    state.current_month = 16
    state.current_market_regime_id = "strong"
    state.player.wealth_strategy_id = "cushion_first"
    state.player.cash = 2200
    state.player.savings = 1800
    state.player.high_interest_savings = 1200
    state.player.credit_score = 710
    state.player.monthly_surplus = 260
    state.player.debt = 3200
    state.player.transport.reliability_score = 82

    top_ids = _top_weighted_event_ids(bundle, state, limit=5)

    assert "cash_drag_regret" in top_ids


def test_phase4_cushion_first_has_reserve_deployment_window_under_lease_pressure(bundle, controller_factory):
    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller, strategy_id in ((cushion, "cushion_first"), (chaser, "market_chaser")):
        state = controller.state
        state.current_month = 14
        state.player.wealth_strategy_id = strategy_id
        state.player.credit_score = 642
        state.player.cash = 180
        state.player.savings = 520
        state.player.high_interest_savings = 1250
        state.player.housing.option_id = "roommates"
        state.player.housing.housing_stability = 34
        state.player.housing.missed_payment_streak = 1
        start_status_arc(
            bundle,
            state,
            "lease_pressure",
            source_event_id="lease_default_warning",
            duration_months=3,
            severity=2,
        )

    cushion_ids = {event.id for event in eligible_events(bundle, cushion.state)}
    chaser_ids = {event.id for event in eligible_events(bundle, chaser.state)}

    assert "reserve_deployment_window" in cushion_ids
    assert "reserve_deployment_window" not in chaser_ids


def test_phase4_market_margin_call_weight_spikes_under_credit_squeeze(bundle, controller_factory):
    flat = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    squeezed = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (flat, squeezed):
        state = controller.state
        state.current_month = 14
        state.current_market_regime_id = "correction"
        state.player.wealth_strategy_id = "market_chaser"
        state.player.cash = 120
        state.player.savings = 160
        state.player.high_interest_savings = 80
        state.player.index_fund = 3200
        state.player.aggressive_growth_fund = 1800
        state.player.debt = 9800
        state.player.credit_score = 646

    start_status_arc(
        bundle,
        squeezed.state,
        "credit_squeeze",
        source_event_id="credit_limit_review",
        duration_months=3,
        severity=2,
    )

    margin_call = next(event for event in bundle.events if event.id == "market_margin_call")

    assert event_weight(bundle, squeezed.state, margin_call) > event_weight(bundle, flat.state, margin_call)


def test_phase5_steady_builder_has_unique_compound_window(bundle, controller_factory):
    steady = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    steady.state.current_month = 16
    steady.state.player.wealth_strategy_id = "steady_builder"
    steady.state.current_market_regime_id = "strong"
    steady.state.player.cash = 2200
    steady.state.player.savings = 1600
    steady.state.player.debt = 3200
    steady.state.player.monthly_surplus = 260
    steady.state.player.credit_score = 700

    cushion = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    cushion.state.current_month = 16
    cushion.state.player.wealth_strategy_id = "cushion_first"
    cushion.state.current_market_regime_id = "strong"
    cushion.state.player.cash = 2200
    cushion.state.player.savings = 1600
    cushion.state.player.debt = 3200
    cushion.state.player.monthly_surplus = 260
    cushion.state.player.credit_score = 700

    steady_ids = {event.id for event in eligible_events(bundle, steady.state)}
    cushion_ids = {event.id for event in eligible_events(bundle, cushion.state)}

    assert "steady_compound_window" in steady_ids
    assert "steady_compound_window" not in cushion_ids


def test_used_car_window_requires_actual_vehicle(bundle, controller_factory):
    controller = controller_factory(opening_path_id="stay_home_stack_cash")
    controller.state.current_month = 6

    controller.state.player.transport.option_id = "transit"
    transit_events = {event.id for event in eligible_events(bundle, controller.state)}
    assert "used_car_window" not in transit_events

    controller.state.player.transport.option_id = "beater_car"
    car_events = {event.id for event in eligible_events(bundle, controller.state)}
    assert "used_car_window" in car_events


def test_transport_fragility_build_surfaces_breakdown_cascade_events(bundle, controller_factory):
    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    fragile.state.current_month = 10
    fragile.state.player.transport.option_id = "beater_car"
    fragile.state.player.transport.reliability_score = 36
    fragile.state.player.debt = 8800
    fragile.state.player.cash = 180
    fragile.state.player.savings = 0

    stable = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    stable.state.current_month = 10
    stable.state.player.transport.option_id = "transit"
    stable.state.player.transport.reliability_score = 88
    stable.state.player.debt = 1400
    stable.state.player.cash = 1800
    stable.state.player.savings = 1200

    fragile_ids = {event.id for event in eligible_events(bundle, fragile.state)}
    stable_ids = {event.id for event in eligible_events(bundle, stable.state)}

    assert "beater_cascade_choice" in fragile_ids
    assert "beater_cascade_choice" not in stable_ids

    cascade = next(event for event in bundle.events if event.id == "beater_cascade_choice")
    assert event_weight(bundle, fragile.state, cascade) >= event_weight(bundle, stable.state, cascade) * 4


def test_school_pressure_build_surfaces_exam_collision_choice(bundle, controller_factory):
    school_heavy = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    school_heavy.state.current_month = 9
    school_heavy.state.player.education.program_id = "full_time_university"
    school_heavy.state.player.education.is_active = True
    school_heavy.state.player.selected_focus_action_id = "overtime"
    school_heavy.state.player.stress = 69
    school_heavy.state.player.energy = 42

    worker_first = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    worker_first.state.current_month = 9
    worker_first.state.player.education.program_id = "none"
    worker_first.state.player.education.is_active = False
    worker_first.state.player.selected_focus_action_id = "recovery_month"

    school_ids = {event.id for event in eligible_events(bundle, school_heavy.state)}
    worker_ids = {event.id for event in eligible_events(bundle, worker_first.state)}

    assert "overtime_exam_collision" in school_ids
    assert "overtime_exam_collision" not in worker_ids

    collision = next(event for event in bundle.events if event.id == "overtime_exam_collision")
    assert event_weight(bundle, school_heavy.state, collision) >= event_weight(bundle, worker_first.state, collision) * 3


def test_credit_squeeze_build_surfaces_collections_warning(bundle, controller_factory):
    squeezed = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    squeezed.state.current_month = 12
    squeezed.state.player.credit_score = 548
    squeezed.state.player.debt = 11200
    squeezed.state.player.monthly_surplus = -220
    squeezed.state.player.cash = 120
    squeezed.state.player.savings = 0

    healthy = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    healthy.state.current_month = 12
    healthy.state.player.credit_score = 752
    healthy.state.player.debt = 2100
    healthy.state.player.monthly_surplus = 340
    healthy.state.player.cash = 2400
    healthy.state.player.savings = 1800

    squeezed_ids = {event.id for event in eligible_events(bundle, squeezed.state)}
    healthy_ids = {event.id for event in eligible_events(bundle, healthy.state)}

    assert "collections_warning" in squeezed_ids
    assert "collections_warning" not in healthy_ids

    warning = next(event for event in bundle.events if event.id == "collections_warning")
    assert event_weight(bundle, squeezed.state, warning) >= event_weight(bundle, healthy.state, warning) * 4


def test_vehicle_repair_events_do_not_show_up_without_vehicle(bundle, controller_factory):
    controller = controller_factory(opening_path_id="stay_home_stack_cash")
    controller.state.current_month = 6
    controller.state.player.transport.option_id = "transit"

    event_ids = {event.id for event in eligible_events(bundle, controller.state)}

    assert "car_repair" not in event_ids
    assert "beater_breakdown" not in event_ids
    assert "missed_shift_after_breakdown" not in event_ids


def test_prime_credit_distressed_run_gets_recovery_window_event(bundle, controller_factory):
    prime = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    prime.state.current_month = 16
    prime.state.player.credit_score = 756
    prime.state.player.debt = 8400
    prime.state.player.monthly_surplus = -120
    prime.state.player.cash = 220
    prime.state.player.savings = 140

    fair = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    fair.state.current_month = 16
    fair.state.player.credit_score = 628
    fair.state.player.debt = 8400
    fair.state.player.monthly_surplus = -120
    fair.state.player.cash = 220
    fair.state.player.savings = 140

    prime_ids = {event.id for event in eligible_events(bundle, prime.state)}
    fair_ids = {event.id for event in eligible_events(bundle, fair.state)}

    assert "prime_refi_bridge" in prime_ids
    assert "prime_refi_bridge" not in fair_ids


def test_heavy_debt_month_can_lower_credit(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        difficulty_id="hard",
        city_id="mid_size_city",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    controller.state.player.cash = 0
    controller.state.player.savings = 0
    controller.state.player.debt = 8000
    starting_credit = controller.state.player.credit_score

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.credit_score < starting_credit


def test_consequence_matrix_weights_change_event_pressure(bundle, controller_factory):
    # Transport friction contrast
    transit = controller_factory(opening_path_id="stay_home_stack_cash")
    transit.state.current_month = 6
    transit.state.player.transport.option_id = "transit"
    beater = controller_factory(opening_path_id="stay_home_stack_cash")
    beater.state.current_month = 6
    beater.state.player.transport.option_id = "beater_car"
    car_repair = next(event for event in bundle.events if event.id == "car_repair")
    assert event_weight(bundle, beater.state, car_repair) > event_weight(bundle, transit.state, car_repair)

    # Education drag contrast
    no_school = controller_factory(opening_path_id="full_time_work")
    no_school.state.current_month = 6
    in_school = controller_factory(opening_path_id="college_university")
    in_school.state.current_month = 6
    scholarship_relief = next(event for event in bundle.events if event.id == "scholarship_relief")
    assert event_weight(bundle, in_school.state, scholarship_relief) > event_weight(bundle, no_school.state, scholarship_relief)

    # Credit squeeze contrast
    fragile = controller_factory()
    fragile.state.current_month = 6
    fragile.state.player.credit_score = 520
    prime = controller_factory()
    prime.state.current_month = 6
    prime.state.player.credit_score = 760
    credit_limit_review = next(event for event in bundle.events if event.id == "credit_limit_review")
    assert event_weight(bundle, fragile.state, credit_limit_review) > event_weight(bundle, prime.state, credit_limit_review)


def test_major_risk_events_have_higher_severity_for_fragile_builds(bundle, controller_factory):
    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    resilient = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")

    fragile.state.player.cash = 0
    fragile.state.player.savings = 0
    fragile.state.player.debt = 26000
    fragile.state.player.credit_score = 520
    fragile.state.player.housing.housing_stability = 34
    fragile.state.player.transport.reliability_score = 38
    fragile.state.player.stress = 84
    fragile.state.player.energy = 22
    fragile.state.player.family_support = 22
    fragile.state.player.social_stability = 24

    resilient.state.player.cash = 4500
    resilient.state.player.savings = 3200
    resilient.state.player.debt = 1200
    resilient.state.player.credit_score = 760
    resilient.state.player.housing.housing_stability = 82
    resilient.state.player.transport.reliability_score = 92
    resilient.state.player.stress = 24
    resilient.state.player.energy = 84
    resilient.state.player.family_support = 76
    resilient.state.player.social_stability = 74

    for event_id in ("car_repair", "rent_increase", "job_layoff", "burnout_month", "credit_limit_review"):
        event = next(item for item in bundle.events if item.id == event_id)
        fragile_mult = event_severity_multiplier(bundle, fragile.state, event)
        resilient_mult = event_severity_multiplier(bundle, resilient.state, event)
        assert fragile_mult > resilient_mult


def test_credit_fragility_increases_security_deposit_shock_severity(bundle, controller_factory):
    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    resilient = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    event = next(item for item in bundle.events if item.id == "security_deposit_shock")

    fragile.state.player.credit_score = 548
    fragile.state.player.debt = 9800
    fragile.state.player.cash = 220
    fragile.state.player.savings = 100
    fragile.state.player.monthly_surplus = -140
    fragile.state.player.housing.housing_stability = 42

    resilient.state.player.credit_score = 758
    resilient.state.player.debt = 2200
    resilient.state.player.cash = 2200
    resilient.state.player.savings = 1800
    resilient.state.player.monthly_surplus = 260
    resilient.state.player.housing.housing_stability = 78

    fragile_mult = event_severity_multiplier(bundle, fragile.state, event)
    resilient_mult = event_severity_multiplier(bundle, resilient.state, event)

    assert fragile_mult > resilient_mult


def test_resolve_event_scales_car_repair_damage_by_resilience(bundle, controller_factory):
    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    resilient = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    event = next(item for item in bundle.events if item.id == "car_repair")

    fragile.state.player.cash = 2000
    fragile.state.player.savings = 0
    fragile.state.player.debt = 18000
    fragile.state.player.credit_score = 540
    fragile.state.player.transport.reliability_score = 40
    fragile.state.player.stress = 78
    fragile.state.player.energy = 28

    resilient.state.player.cash = 2000
    resilient.state.player.savings = 2000
    resilient.state.player.debt = 1200
    resilient.state.player.credit_score = 760
    resilient.state.player.transport.reliability_score = 92
    resilient.state.player.stress = 22
    resilient.state.player.energy = 82

    fragile_cash_start = fragile.state.player.cash
    resilient_cash_start = resilient.state.player.cash
    fragile_stress_start = fragile.state.player.stress
    resilient_stress_start = resilient.state.player.stress

    resolve_event(bundle, fragile.state, event)
    resolve_event(bundle, resilient.state, event)

    fragile_cash_hit = fragile_cash_start - fragile.state.player.cash
    resilient_cash_hit = resilient_cash_start - resilient.state.player.cash
    fragile_stress_gain = fragile.state.player.stress - fragile_stress_start
    resilient_stress_gain = resilient.state.player.stress - resilient_stress_start

    assert fragile_cash_hit > resilient_cash_hit
    assert fragile_stress_gain > resilient_stress_gain


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


def test_branching_available_for_retail_and_warehouse_tracks(controller_factory):
    retail = controller_factory(opening_path_id="full_time_work")
    retail.change_career("retail_service")
    retail.state.player.career.tier_index = 1
    retail.state.player.career.promotion_momentum = 62
    retail.state.player.social_stability = 60
    retail.state.player.housing.housing_stability = 55
    retail.state.player.transport.reliability_score = 70
    retail_branches = retail.available_career_branches()
    retail_ids = {branch.id for branch, _, _ in retail_branches}
    assert {"retail_management_track", "retail_sales_track", "retail_clienteling_track"} <= retail_ids

    warehouse = controller_factory(opening_path_id="full_time_work")
    warehouse.state.player.career.tier_index = 1
    warehouse.state.player.transport.reliability_score = 75
    warehouse.state.player.energy = 58
    warehouse_branches = warehouse.available_career_branches()
    warehouse_ids = {branch.id for branch, _, _ in warehouse_branches}
    assert {"warehouse_ops_track", "warehouse_dispatch_track", "warehouse_equipment_track"} <= warehouse_ids


def test_branching_available_for_office_admin_track(controller_factory):
    office = controller_factory(opening_path_id="college_university")
    office.change_career("office_admin")
    office.state.player.career.tier_index = 1
    office.state.player.social_stability = 70
    office.state.player.energy = 60

    office_branches = office.available_career_branches()
    office_ids = {branch.id for branch, _, _ in office_branches}

    assert {"office_operations_track", "office_people_track", "office_compliance_track"} <= office_ids


def test_office_branch_event_pools_diverge_by_selected_branch(bundle, controller_factory):
    operations = controller_factory(opening_path_id="college_university")
    operations.change_career("office_admin")
    operations.state.current_month = 20
    operations.state.player.career.tier_index = 1
    operations.state.player.career.branch_id = "office_operations_track"
    operations.state.player.stress = 62
    operations.state.player.energy = 56
    operations.state.player.social_stability = 58

    people = controller_factory(opening_path_id="college_university")
    people.change_career("office_admin")
    people.state.current_month = 20
    people.state.player.career.tier_index = 1
    people.state.player.career.branch_id = "office_people_track"
    people.state.player.stress = 50
    people.state.player.energy = 62
    people.state.player.social_stability = 70

    compliance = controller_factory(opening_path_id="college_university")
    compliance.change_career("office_admin")
    compliance.state.current_month = 20
    compliance.state.player.career.tier_index = 1
    compliance.state.player.career.branch_id = "office_compliance_track"
    compliance.state.player.stress = 54
    compliance.state.player.energy = 52
    compliance.state.player.credit_score = 725
    compliance.state.player.debt = 4200

    operations_ids = {event.id for event in eligible_events(bundle, operations.state)}
    people_ids = {event.id for event in eligible_events(bundle, people.state)}
    compliance_ids = {event.id for event in eligible_events(bundle, compliance.state)}

    assert "office_deadline_overflow" in operations_ids
    assert "office_automation_rollout" in operations_ids
    assert "office_deadline_overflow" not in people_ids
    assert "office_deadline_overflow" not in compliance_ids

    assert "office_team_retention_wave" in people_ids
    assert "office_team_retention_wave" not in operations_ids
    assert "office_team_retention_wave" not in compliance_ids

    assert "office_audit_window" in compliance_ids
    assert "office_audit_window" not in operations_ids
    assert "office_audit_window" not in people_ids


def test_selected_branch_changes_income_profile(bundle, controller_factory):
    mgmt = controller_factory(opening_path_id="full_time_work")
    mgmt.change_career("retail_service")
    mgmt.state.player.career.tier_index = 1
    mgmt.state.player.career.branch_id = "retail_management_track"
    sales = controller_factory(opening_path_id="full_time_work")
    sales.change_career("retail_service")
    sales.state.player.career.tier_index = 1
    sales.state.player.career.branch_id = "retail_sales_track"
    sales.state.player.social_stability = 70
    mgmt_income = current_income(bundle, mgmt.state, 1.0)
    sales_income = current_income(bundle, sales.state, 1.0)
    assert mgmt_income != sales_income


def test_phase2_retail_branches_shift_top_weighted_mix(bundle, controller_factory):
    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    management.state.current_month = 22
    management.state.player.career.tier_index = 2
    management.state.player.career.branch_id = "retail_management_track"
    management.state.player.social_stability = 62
    management.state.player.energy = 54
    management.state.player.stress = 68
    management.state.player.transport.reliability_score = 72

    sales = controller_factory(opening_path_id="full_time_work")
    sales.change_career("retail_service")
    sales.state.current_month = 22
    sales.state.player.career.tier_index = 2
    sales.state.player.career.branch_id = "retail_sales_track"
    sales.state.player.social_stability = 70
    sales.state.player.energy = 58
    sales.state.player.stress = 56
    sales.state.player.transport.reliability_score = 70

    clienteling = controller_factory(opening_path_id="full_time_work")
    clienteling.change_career("retail_service")
    clienteling.state.current_month = 22
    clienteling.state.player.career.tier_index = 2
    clienteling.state.player.career.branch_id = "retail_clienteling_track"
    clienteling.state.player.social_stability = 72
    clienteling.state.player.energy = 58
    clienteling.state.player.stress = 50
    clienteling.state.player.transport.reliability_score = 74

    management_top = _top_weighted_event_ids(bundle, management.state)
    sales_top = _top_weighted_event_ids(bundle, sales.state)
    clienteling_top = _top_weighted_event_ids(bundle, clienteling.state)

    assert "retail_inventory_crunch" in management_top
    assert "retail_leadership_offer" in management_top
    assert "sales_whale_month" in sales_top
    assert "sales_territory_offer" in sales_top
    assert "clienteling_key_account_offer" in clienteling_top
    assert "client_book_referral" in clienteling_top
    assert set(management_top) != set(sales_top)
    assert set(sales_top) != set(clienteling_top)


def test_phase2_warehouse_branches_shift_top_weighted_mix(bundle, controller_factory):
    ops = controller_factory(opening_path_id="full_time_work")
    ops.state.current_month = 24
    ops.state.player.career.tier_index = 2
    ops.state.player.career.branch_id = "warehouse_ops_track"
    ops.state.player.transport.reliability_score = 76
    ops.state.player.energy = 58
    ops.state.player.stress = 52
    ops.state.player.social_stability = 50

    dispatch = controller_factory(opening_path_id="full_time_work")
    dispatch.state.current_month = 24
    dispatch.state.player.career.tier_index = 2
    dispatch.state.player.career.branch_id = "warehouse_dispatch_track"
    dispatch.state.player.transport.reliability_score = 78
    dispatch.state.player.energy = 56
    dispatch.state.player.stress = 50
    dispatch.state.player.social_stability = 62

    equipment = controller_factory(opening_path_id="full_time_work")
    equipment.state.current_month = 24
    equipment.state.player.career.tier_index = 2
    equipment.state.player.career.branch_id = "warehouse_equipment_track"
    equipment.state.player.transport.reliability_score = 80
    equipment.state.player.energy = 60
    equipment.state.player.stress = 48
    equipment.state.player.social_stability = 56

    ops_top = _top_weighted_event_ids(bundle, ops.state)
    dispatch_top = _top_weighted_event_ids(bundle, dispatch.state)
    equipment_top = _top_weighted_event_ids(bundle, equipment.state)

    assert "warehouse_foreman_offer" in ops_top
    assert "dispatch_route_rewrite" in dispatch_top
    assert "dispatch_lead_offer" in dispatch_top
    assert "equipment_specialist_offer" in equipment_top
    assert "equipment_shift_contract" in equipment_top
    assert set(ops_top) != set(dispatch_top)
    assert set(dispatch_top) != set(equipment_top)


def test_phase2_branch_specific_promotion_blockers_diverge(bundle, controller_factory):
    management = controller_factory(opening_path_id="full_time_work")
    management.change_career("retail_service")
    management.state.player.career.tier_index = 2
    management.state.player.career.promotion_progress = 99
    management.state.player.career.branch_id = "retail_management_track"
    management.state.player.stress = 78
    management.state.player.energy = 52
    management.state.player.social_stability = 62
    management.state.player.housing.housing_stability = 58
    management.state.player.transport.reliability_score = 74

    clienteling = controller_factory(opening_path_id="full_time_work")
    clienteling.change_career("retail_service")
    clienteling.state.player.career.tier_index = 2
    clienteling.state.player.career.promotion_progress = 99
    clienteling.state.player.career.branch_id = "retail_clienteling_track"
    clienteling.state.player.stress = 56
    clienteling.state.player.energy = 54
    clienteling.state.player.social_stability = 56
    clienteling.state.player.housing.housing_stability = 46
    clienteling.state.player.transport.reliability_score = 74

    management_blockers = promotion_blockers(bundle, management.state)
    clienteling_blockers = promotion_blockers(bundle, clienteling.state)
    management_text = " ".join(management_blockers).lower()
    clienteling_text = " ".join(clienteling_blockers).lower()

    assert "management" in management_text
    assert "stress" in management_text
    assert "client" in clienteling_text
    assert "social" in clienteling_text
    assert management_text != clienteling_text


def test_phase2_branch_prerequisites_gate_fragile_profiles(controller_factory):
    retail = controller_factory(opening_path_id="full_time_work")
    retail.change_career("retail_service")
    retail.state.player.career.tier_index = 1
    retail.state.player.social_stability = 58
    retail.state.player.transport.reliability_score = 48
    retail.state.player.energy = 36

    retail_status = {branch.id: (allowed, reason) for branch, allowed, reason in retail.available_career_branches()}
    clienteling_allowed, clienteling_reason = retail_status["retail_clienteling_track"]
    assert not clienteling_allowed
    assert "social" in clienteling_reason.lower() or "transport" in clienteling_reason.lower()

    warehouse = controller_factory(opening_path_id="full_time_work")
    warehouse.state.player.career.tier_index = 1
    warehouse.state.player.transport.reliability_score = 62
    warehouse.state.player.energy = 35
    warehouse.state.player.social_stability = 46

    warehouse_status = {branch.id: (allowed, reason) for branch, allowed, reason in warehouse.available_career_branches()}
    equipment_allowed, equipment_reason = warehouse_status["warehouse_equipment_track"]
    dispatch_allowed, dispatch_reason = warehouse_status["warehouse_dispatch_track"]
    assert not equipment_allowed
    assert "transport" in equipment_reason.lower() or "energy" in equipment_reason.lower()
    assert not dispatch_allowed
    assert "social" in dispatch_reason.lower() or "energy" in dispatch_reason.lower()


def test_phase3_promotion_commitment_tags_change_access_requirements(bundle, controller_factory):
    crisis = controller_factory(opening_path_id="full_time_work")
    crisis.change_career("retail_service")
    crisis.state.player.career.tier_index = 2
    crisis.state.player.career.branch_id = "retail_management_track"
    crisis.state.player.career.promotion_progress = 99
    crisis.state.player.stress = 73
    crisis.state.player.energy = 52
    crisis.state.player.social_stability = 62
    crisis.state.player.transport.reliability_score = 72
    crisis.state.player.housing.housing_stability = 56
    crisis.state.player.persistent_tags.append("retail_management_crisis_lead_lane")

    sustainable = controller_factory(opening_path_id="full_time_work")
    sustainable.change_career("retail_service")
    sustainable.state.player.career.tier_index = 2
    sustainable.state.player.career.branch_id = "retail_management_track"
    sustainable.state.player.career.promotion_progress = 99
    sustainable.state.player.stress = 73
    sustainable.state.player.energy = 52
    sustainable.state.player.social_stability = 62
    sustainable.state.player.transport.reliability_score = 72
    sustainable.state.player.housing.housing_stability = 56
    sustainable.state.player.persistent_tags.append("retail_management_sustainable_ops_lane")

    crisis_blockers = " ".join(promotion_blockers(bundle, crisis.state)).lower()
    sustainable_blockers = " ".join(promotion_blockers(bundle, sustainable.state)).lower()

    assert "crisis-lead lane requires stress to settle" in crisis_blockers
    assert "crisis-lead lane requires stress to settle" not in sustainable_blockers


def test_phase1_contrast_builds_have_distinct_top_event_profiles(bundle, controller_factory):
    stable = controller_factory(
        opening_path_id="stay_home_stack_cash",
        city_id="hometown_low_cost",
        savings_band_id="solid",
        family_support_level_id="high",
    )
    stable.state.current_month = 14
    stable.state.player.housing.option_id = "parents"
    stable.state.player.transport.option_id = "transit"
    stable.state.player.transport.reliability_score = 86
    stable.state.player.credit_score = 748
    stable.state.player.debt = 1400
    stable.state.player.monthly_surplus = 340
    stable.state.player.selected_focus_action_id = "recovery_month"

    renter = controller_factory(
        opening_path_id="move_out_immediately",
        city_id="mid_size_city",
        savings_band_id="none",
        family_support_level_id="low",
        difficulty_id="hard",
    )
    renter.state.current_month = 14
    renter.state.player.housing.option_id = "solo_rental"
    renter.state.player.housing.housing_stability = 40
    renter.state.player.transport.option_id = "financed_car"
    renter.state.player.credit_score = 548
    renter.state.player.debt = 13200
    renter.state.player.cash = 120
    renter.state.player.savings = 0
    renter.state.player.monthly_surplus = -260
    renter.state.player.selected_focus_action_id = "overtime"

    fragile = controller_factory(
        opening_path_id="move_out_immediately",
        city_id="mid_size_city",
        savings_band_id="none",
    )
    fragile.state.current_month = 11
    fragile.state.player.housing.option_id = "roommates"
    fragile.state.player.transport.option_id = "beater_car"
    fragile.state.player.transport.reliability_score = 34
    fragile.state.player.transport.breakdown_pressure = 2
    fragile.state.player.credit_score = 598
    fragile.state.player.debt = 8600
    fragile.state.player.cash = 220
    fragile.state.player.savings = 0
    fragile.state.player.monthly_surplus = -110
    fragile.state.player.selected_focus_action_id = "side_gig"

    school = controller_factory(
        opening_path_id="college_university",
        city_id="mid_size_city",
        savings_band_id="none",
    )
    school.state.current_month = 9
    school.state.player.education.program_id = "full_time_university"
    school.state.player.education.is_active = True
    school.state.player.education.intensity_level = "intensive"
    school.state.player.selected_focus_action_id = "overtime"
    school.state.player.stress = 70
    school.state.player.energy = 40
    school.state.player.credit_score = 628
    school.state.player.debt = 5200
    school.state.player.monthly_surplus = -110
    school.state.player.housing.option_id = "student_residence"
    school.state.player.transport.option_id = "transit"

    stable_top = _top_weighted_event_ids(bundle, stable.state)
    renter_top = _top_weighted_event_ids(bundle, renter.state)
    fragile_top = _top_weighted_event_ids(bundle, fragile.state)
    school_top = _top_weighted_event_ids(bundle, school.state)

    assert "family_stability_surge" in stable_top
    assert "lease_default_warning" in renter_top
    assert "beater_total_failure" in fragile_top
    assert "exam_probation_hearing" in school_top

    assert len(set(stable_top) & set(renter_top)) <= 2
    assert len(set(stable_top) & set(fragile_top)) <= 2
    assert len(set(renter_top) & set(school_top)) <= 3


def test_phase1_contrast_builds_show_weighted_pressure_divergence(bundle, controller_factory):
    stable = controller_factory(
        opening_path_id="stay_home_stack_cash",
        city_id="hometown_low_cost",
        savings_band_id="solid",
        family_support_level_id="high",
    )
    stable.state.current_month = 14
    stable.state.player.housing.option_id = "parents"
    stable.state.player.transport.option_id = "transit"
    stable.state.player.credit_score = 748
    stable.state.player.debt = 1400
    stable.state.player.monthly_surplus = 340
    stable.state.player.selected_focus_action_id = "recovery_month"

    renter = controller_factory(
        opening_path_id="move_out_immediately",
        city_id="mid_size_city",
        savings_band_id="none",
        family_support_level_id="low",
        difficulty_id="hard",
    )
    renter.state.current_month = 14
    renter.state.player.housing.option_id = "solo_rental"
    renter.state.player.housing.housing_stability = 40
    renter.state.player.credit_score = 548
    renter.state.player.debt = 13200
    renter.state.player.cash = 120
    renter.state.player.savings = 0
    renter.state.player.monthly_surplus = -260
    renter.state.player.selected_focus_action_id = "overtime"

    fragile = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city", savings_band_id="none")
    fragile.state.current_month = 11
    fragile.state.player.transport.option_id = "beater_car"
    fragile.state.player.transport.reliability_score = 34
    fragile.state.player.transport.breakdown_pressure = 2
    fragile.state.player.credit_score = 598
    fragile.state.player.debt = 8600
    fragile.state.player.monthly_surplus = -110

    school = controller_factory(opening_path_id="college_university", city_id="mid_size_city", savings_band_id="none")
    school.state.current_month = 9
    school.state.player.education.program_id = "full_time_university"
    school.state.player.education.is_active = True
    school.state.player.education.intensity_level = "intensive"
    school.state.player.selected_focus_action_id = "overtime"
    school.state.player.stress = 70
    school.state.player.energy = 40

    lease_default = next(event for event in bundle.events if event.id == "lease_default_warning")
    beater_fail = next(event for event in bundle.events if event.id == "beater_total_failure")
    exam_probation = next(event for event in bundle.events if event.id == "exam_probation_hearing")

    assert event_weight(bundle, renter.state, lease_default) >= event_weight(bundle, stable.state, lease_default) * 3
    assert event_weight(bundle, fragile.state, beater_fail) >= event_weight(bundle, stable.state, beater_fail) * 3
    assert event_weight(bundle, school.state, exam_probation) >= event_weight(bundle, stable.state, exam_probation) * 3


def test_lease_default_warning_choice_and_chain_behavior(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.current_month = 14
    controller.state.player.housing.option_id = "solo_rental"
    controller.state.player.housing.housing_stability = 38
    controller.state.player.credit_score = 546
    controller.state.player.debt = 12800
    controller.state.player.monthly_surplus = -240
    event = next(item for item in bundle.events if item.id == "lease_default_warning")

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("borrow_to_cover_shortfall")

    assert any(pending.event_id == "lease_enforcement_notice" for pending in controller.state.pending_events)
    assert any(modifier.id == "borrowed_rent_patch" for modifier in controller.state.active_modifiers)


def test_exam_probation_hearing_choice_and_chain_behavior(bundle, controller_factory):
    controller = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    controller.state.current_month = 10
    controller.state.player.education.program_id = "full_time_university"
    controller.state.player.education.is_active = True
    controller.state.player.education.intensity_level = "intensive"
    controller.state.player.selected_focus_action_id = "overtime"
    controller.state.player.stress = 72
    controller.state.player.energy = 38
    event = next(item for item in bundle.events if item.id == "exam_probation_hearing")

    resolve_event(bundle, controller.state, event)
    controller.resolve_event_choice("cut_hours_and_recover_standing")

    assert any(pending.event_id == "academic_funding_review" for pending in controller.state.pending_events)
    assert any(modifier.id == "course_load_rebalance" for modifier in controller.state.active_modifiers)


def test_final_truth_rebalancing_workload_cuts_followup_burnout_pressure(bundle, controller_factory):
    stabilize = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    push = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")

    for controller in (stabilize, push):
        controller.state.current_month = 18
        controller.state.player.selected_focus_action_id = "overtime"
        controller.state.player.stress = 74
        controller.state.player.energy = 36
        controller.state.player.cash = 450
        controller.state.player.monthly_surplus = 120

    attrition = next(item for item in bundle.events if item.id == "overtime_attrition_warning")
    burnout = next(item for item in bundle.events if item.id == "burnout_month")

    resolve_event(bundle, stabilize.state, attrition)
    resolve_event_choice(bundle, stabilize.state, "overtime_attrition_warning", "rebalance_workload")

    resolve_event(bundle, push.state, attrition)
    resolve_event_choice(bundle, push.state, "overtime_attrition_warning", "keep_forcing_hours")

    stabilize_top = _top_weighted_event_ids(bundle, stabilize.state)
    push_top = _top_weighted_event_ids(bundle, push.state)

    assert "burnout_month" not in stabilize_top
    assert "burnout_month" in push_top
    assert event_weight(bundle, push.state, burnout) > event_weight(bundle, stabilize.state, burnout)
    assert calculate_final_score(bundle, stabilize.state).final_score > calculate_final_score(bundle, push.state).final_score
