from __future__ import annotations

from budgetwars.engine.events import eligible_events, event_weight, resolve_event, resolve_event_choice
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import calculate_final_score
from budgetwars.engine.status_arcs import start_status_arc
from budgetwars.games.classic.ui.main_window import build_pressure_summary


def _top_weighted_event_ids(bundle, state, *, limit: int = 5) -> list[str]:
    scored = sorted(
        ((event_weight(bundle, state, event), event.id) for event in eligible_events(bundle, state)),
        reverse=True,
    )
    return [event_id for _weight, event_id in scored[:limit]]


def _build_finish_pass_archetypes(controller_factory):
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

    transport_fragile = controller_factory(
        opening_path_id="move_out_immediately",
        city_id="mid_size_city",
        savings_band_id="none",
    )
    transport_fragile.state.current_month = 11
    transport_fragile.state.player.housing.option_id = "roommates"
    transport_fragile.state.player.transport.option_id = "beater_car"
    transport_fragile.state.player.transport.reliability_score = 34
    transport_fragile.state.player.transport.breakdown_pressure = 2
    transport_fragile.state.player.credit_score = 598
    transport_fragile.state.player.debt = 8600
    transport_fragile.state.player.cash = 220
    transport_fragile.state.player.savings = 0
    transport_fragile.state.player.monthly_surplus = -110
    transport_fragile.state.player.selected_focus_action_id = "side_gig"

    school_heavy = controller_factory(
        opening_path_id="college_university",
        city_id="mid_size_city",
        savings_band_id="none",
    )
    school_heavy.state.current_month = 9
    school_heavy.state.player.education.program_id = "full_time_university"
    school_heavy.state.player.education.is_active = True
    school_heavy.state.player.education.intensity_level = "intensive"
    school_heavy.state.player.selected_focus_action_id = "overtime"
    school_heavy.state.player.stress = 70
    school_heavy.state.player.energy = 40
    school_heavy.state.player.credit_score = 628
    school_heavy.state.player.debt = 5200
    school_heavy.state.player.monthly_surplus = -110
    school_heavy.state.player.housing.option_id = "student_residence"
    school_heavy.state.player.transport.option_id = "transit"

    weak_credit = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    weak_credit.state.current_month = 14
    weak_credit.state.player.credit_score = 556
    weak_credit.state.player.debt = 12800
    weak_credit.state.player.cash = 120
    weak_credit.state.player.savings = 0
    weak_credit.state.player.monthly_surplus = -150
    weak_credit.state.player.credit_missed_obligation_streak = 3
    weak_credit.state.player.credit_utilization_pressure = 84
    weak_credit.state.player.transport.option_id = "beater_car"

    strong_credit = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    strong_credit.state.current_month = 14
    strong_credit.state.player.credit_score = 754
    strong_credit.state.player.debt = 2600
    strong_credit.state.player.cash = 2400
    strong_credit.state.player.savings = 1600
    strong_credit.state.player.monthly_surplus = 320
    strong_credit.state.player.credit_missed_obligation_streak = 0
    strong_credit.state.player.credit_rebuild_streak = 2
    strong_credit.state.player.credit_utilization_pressure = 34
    strong_credit.state.player.transport.option_id = "transit"

    return {
        "stable_at_home_saver": stable,
        "debt_heavy_renter": renter,
        "transport_fragile_worker": transport_fragile,
        "school_heavy_climber": school_heavy,
        "weak_credit_fragile_build": weak_credit,
        "strong_credit_stable_build": strong_credit,
    }


def test_finish_pass_archetypes_split_event_pools_doors_and_scores(bundle, controller_factory):
    archetypes = _build_finish_pass_archetypes(controller_factory)

    stable = archetypes["stable_at_home_saver"]
    renter = archetypes["debt_heavy_renter"]
    transport_fragile = archetypes["transport_fragile_worker"]
    school_heavy = archetypes["school_heavy_climber"]

    stable_top = _top_weighted_event_ids(bundle, stable.state)
    renter_top = _top_weighted_event_ids(bundle, renter.state)
    transport_top = _top_weighted_event_ids(bundle, transport_fragile.state)
    school_top = _top_weighted_event_ids(bundle, school_heavy.state)

    stable_summary = build_pressure_summary(stable.state, bundle)
    renter_summary = build_pressure_summary(renter.state, bundle)
    transport_summary = build_pressure_summary(transport_fragile.state, bundle)
    school_summary = build_pressure_summary(school_heavy.state, bundle)

    assert "family_stability_surge" in stable_top
    assert "lease_default_warning" in renter_top
    assert "beater_total_failure" in transport_top
    assert "exam_probation_hearing" in school_top

    assert not stable_summary.blocked_doors
    assert transport_summary.blocked_doors
    assert school_summary.blocked_doors

    assert stable_summary.projected_score > renter_summary.projected_score
    assert stable_summary.projected_score > transport_summary.projected_score
    assert school_summary.projected_score > transport_summary.projected_score

    assert len(set(stable_top) & set(renter_top)) <= 2
    assert len(set(renter_top) & set(transport_top)) <= 3
    assert len(set(transport_top) & set(school_top)) <= 2


def test_finish_pass_credit_polarity_changes_doors_recovery_route_and_score(bundle, controller_factory):
    archetypes = _build_finish_pass_archetypes(controller_factory)
    weak = archetypes["weak_credit_fragile_build"]
    strong = archetypes["strong_credit_stable_build"]

    weak_top = _top_weighted_event_ids(bundle, weak.state)
    strong_top = _top_weighted_event_ids(bundle, strong.state)
    weak_summary = build_pressure_summary(weak.state, bundle)
    strong_summary = build_pressure_summary(strong.state, bundle)

    assert "collections_warning" in weak_top
    assert "refinance_window" not in weak_top
    assert "refinance_window" in strong_top

    assert weak_summary.blocked_doors
    assert not strong_summary.blocked_doors
    assert weak_summary.recovery_route is None
    assert strong_summary.recovery_route is not None
    assert "strong credit" in strong_summary.recovery_route.lower()
    assert strong_summary.projected_score - weak_summary.projected_score >= 20


def test_finish_pass_credit_recovery_score_gap_beats_fragile_balance(bundle, controller_factory):
    archetypes = _build_finish_pass_archetypes(controller_factory)
    renter = archetypes["debt_heavy_renter"]
    weak = archetypes["weak_credit_fragile_build"]
    strong = archetypes["strong_credit_stable_build"]

    renter_summary = build_pressure_summary(renter.state, bundle)
    weak_summary = build_pressure_summary(weak.state, bundle)
    strong_summary = build_pressure_summary(strong.state, bundle)

    assert renter_summary.projected_score < strong_summary.projected_score
    assert weak_summary.projected_score < strong_summary.projected_score
    assert renter_summary.biggest_risk != strong_summary.biggest_risk or renter_summary.blocked_doors != strong_summary.blocked_doors


def test_finish_pass_recovery_choice_changes_next_month_pressure_and_score(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    recovery = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    masking = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")

    for controller in (recovery, masking):
        state = controller.state
        state.current_month = 18
        state.player.selected_focus_action_id = "overtime"
        state.player.stress = 84
        state.player.energy = 22
        state.player.cash = 480
        state.player.monthly_surplus = 90

    burnout = next(event for event in bundle.events if event.id == "burnout_month")

    resolve_event(bundle, recovery.state, burnout)
    resolve_event_choice(bundle, recovery.state, "burnout_month", "take_real_recovery")

    resolve_event(bundle, masking.state, burnout)
    resolve_event_choice(bundle, masking.state, "burnout_month", "mask_and_push")

    resolve_month(quiet_bundle, recovery.state, recovery.rng)
    resolve_month(quiet_bundle, masking.state, masking.rng)

    recovery_summary = build_pressure_summary(recovery.state, bundle)
    masking_summary = build_pressure_summary(masking.state, bundle)
    recovery_burnout = next((arc for arc in recovery.state.active_status_arcs if arc.arc_id == "burnout_risk"), None)
    masking_burnout = next((arc for arc in masking.state.active_status_arcs if arc.arc_id == "burnout_risk"), None)

    assert recovery.state.player.stress <= masking.state.player.stress - 8
    assert recovery.state.player.energy >= masking.state.player.energy + 8
    assert recovery_burnout is not None
    assert masking_burnout is not None
    assert recovery_burnout.severity < masking_burnout.severity
    assert recovery_summary.projected_score > masking_summary.projected_score


def test_finish_pass_wealth_identity_changes_pressure_and_rescue_shape(bundle, controller_factory):
    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (cushion, chaser):
        state = controller.state
        state.current_month = 20
        state.current_market_regime_id = "correction"
        state.player.housing.option_id = "solo_rental"
        state.player.housing.housing_stability = 38
        state.player.credit_score = 660
        state.player.debt = 9200
        state.player.monthly_surplus = -120
        state.player.cash = 400
        start_status_arc(
            bundle,
            state,
            "lease_pressure",
            source_event_id="lease_default_warning",
            duration_months=3,
            severity=2,
        )

    cushion.state.player.wealth_strategy_id = "cushion_first"
    cushion.state.player.high_interest_savings = 1800
    cushion.state.player.index_fund = 400
    cushion.state.player.aggressive_growth_fund = 0

    chaser.state.player.wealth_strategy_id = "market_chaser"
    chaser.state.player.high_interest_savings = 150
    chaser.state.player.index_fund = 900
    chaser.state.player.aggressive_growth_fund = 1150

    cushion_summary = build_pressure_summary(cushion.state, bundle)
    chaser_summary = build_pressure_summary(chaser.state, bundle)
    reserve_window = next(event for event in bundle.events if event.id == "reserve_deployment_window")
    margin_call = next(event for event in bundle.events if event.id == "market_margin_call")

    assert event_weight(bundle, cushion.state, reserve_window) > event_weight(bundle, chaser.state, reserve_window)
    assert event_weight(bundle, chaser.state, margin_call) > event_weight(bundle, cushion.state, margin_call)
    assert cushion_summary.projected_score > chaser_summary.projected_score
