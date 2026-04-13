from __future__ import annotations

from budgetwars.engine.events import eligible_events, event_weight
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
