from __future__ import annotations

from random import Random

from budgetwars.engine.careers import current_income, promotion_blockers
from budgetwars.engine.events import eligible_events, event_severity_multiplier, event_weight, resolve_event
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


def test_used_car_window_requires_actual_vehicle(bundle, controller_factory):
    controller = controller_factory(opening_path_id="stay_home_stack_cash")
    controller.state.current_month = 6

    controller.state.player.transport.option_id = "transit"
    transit_events = {event.id for event in eligible_events(bundle, controller.state)}
    assert "used_car_window" not in transit_events

    controller.state.player.transport.option_id = "beater_car"
    car_events = {event.id for event in eligible_events(bundle, controller.state)}
    assert "used_car_window" in car_events


def test_vehicle_repair_events_do_not_show_up_without_vehicle(bundle, controller_factory):
    controller = controller_factory(opening_path_id="stay_home_stack_cash")
    controller.state.current_month = 6
    controller.state.player.transport.option_id = "transit"

    event_ids = {event.id for event in eligible_events(bundle, controller.state)}

    assert "car_repair" not in event_ids
    assert "beater_breakdown" not in event_ids
    assert "missed_shift_after_breakdown" not in event_ids


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
    assert {"retail_management_track", "retail_sales_track"} <= retail_ids

    warehouse = controller_factory(opening_path_id="full_time_work")
    warehouse.state.player.career.tier_index = 1
    warehouse.state.player.transport.reliability_score = 75
    warehouse.state.player.energy = 58
    warehouse_branches = warehouse.available_career_branches()
    warehouse_ids = {branch.id for branch, _, _ in warehouse_branches}
    assert {"warehouse_ops_track", "warehouse_dispatch_track"} <= warehouse_ids


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
