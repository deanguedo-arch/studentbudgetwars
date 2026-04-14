from __future__ import annotations

from budgetwars.engine.careers import can_enter_career, current_income, maybe_promote
from budgetwars.engine.events import resolve_event, resolve_event_choice
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import calculate_final_score
from budgetwars.engine.status_arcs import start_status_arc
from budgetwars.engine.housing import monthly_housing_cost
from budgetwars.engine.transport import monthly_transport_cost
from budgetwars.models import ActiveMonthlyModifier, PendingEvent


def test_start_state_from_full_setup_modifiers(controller_factory):
    controller = controller_factory(
        preset_id="broke_but_ambitious",
        city_id="high_opportunity_metro",
        academic_level_id="strong",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    state = controller.state
    assert state.player.current_city_id == "high_opportunity_metro"
    assert state.player.opening_path_id == "move_out_immediately"
    assert state.player.housing_id == "roommates"
    assert state.player.transport_id == "transit"
    assert state.player.career.track_id == "retail_service"
    assert state.player.academic_strength > 70


def test_housing_change_affects_cost_and_state(bundle, controller_factory):
    controller = controller_factory(city_id="hometown_low_cost")
    parents_cost = monthly_housing_cost(bundle, controller.state)
    controller.change_housing("roommates")
    roommate_cost = monthly_housing_cost(bundle, controller.state)
    assert controller.state.player.housing_id == "roommates"
    assert roommate_cost > parents_cost


def test_transport_change_affects_access_and_cost(bundle, controller_factory):
    controller = controller_factory()
    transit_cost = monthly_transport_cost(bundle, controller.state)
    controller.change_transport("beater_car")
    car_cost = monthly_transport_cost(bundle, controller.state)
    assert controller.state.player.transport_id == "beater_car"
    assert car_cost > transit_cost


def test_phase_status_arc_transport_trigger_events_start_and_refresh_arc(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    state = controller.state
    state.player.transport.option_id = "beater_car"
    state.player.transport.reliability_score = 42

    car_repair = next(item for item in bundle.events if item.id == "car_repair")
    beater_breakdown = next(item for item in bundle.events if item.id == "beater_breakdown")

    resolve_event(bundle, state, car_repair)

    assert len(state.active_status_arcs) == 1
    first_arc = state.active_status_arcs[0]
    assert first_arc.arc_id == "transport_unstable"
    assert first_arc.source_event_id == "car_repair"
    first_months = first_arc.remaining_months

    resolve_event(bundle, state, beater_breakdown)

    assert len(state.active_status_arcs) == 1
    assert state.active_status_arcs[0].source_event_id == "beater_breakdown"
    assert state.active_status_arcs[0].remaining_months > first_months
    assert state.active_status_arcs[0].severity >= 2


def test_phase_status_arc_credit_starts_from_warning_and_refinance_can_clear_it(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.player.debt = 9600
    state.player.credit_score = 575

    warning = next(item for item in bundle.events if item.id == "collections_warning")
    refinance = next(item for item in bundle.events if item.id == "refinance_window")

    resolve_event(bundle, state, warning)

    assert any(arc.arc_id == "credit_squeeze" for arc in state.active_status_arcs)

    resolve_event_choice(bundle, state, "collections_warning", "stabilize_now")
    state.player.credit_score = 720

    resolve_event(bundle, state, refinance)
    resolve_event_choice(bundle, state, "refinance_window", "refinance_now")

    assert not any(arc.arc_id == "credit_squeeze" for arc in state.active_status_arcs)


def test_phase_status_arc_education_starts_from_school_collision_and_protect_grades_softens_it(bundle, controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    state = controller.state
    state.player.education.program_id = "full_time_university"
    state.player.education.is_active = True
    state.player.education.intensity_level = "intensive"
    state.player.stress = 70
    state.player.energy = 38

    collision = next(item for item in bundle.events if item.id == "overtime_exam_collision")

    resolve_event(bundle, state, collision)

    assert any(arc.arc_id == "education_slipping" for arc in state.active_status_arcs)
    assert next(arc for arc in state.active_status_arcs if arc.arc_id == "education_slipping").severity >= 2

    resolve_event_choice(bundle, state, "overtime_exam_collision", "protect_grades")

    arc = next(arc for arc in state.active_status_arcs if arc.arc_id == "education_slipping")
    assert arc.severity == 1


def test_credit_tighten_up_creates_better_rebuild_footing_than_coast(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    tightening = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    coasting = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (tightening, coasting):
        state = controller.state
        state.player.debt = 9600
        state.player.credit_score = 575
        state.player.credit_utilization_pressure = 86
        start_status_arc(
            bundle,
            state,
            "credit_squeeze",
            source_event_id="credit_limit_review",
            duration_months=4,
            severity=3,
        )

    review = next(item for item in bundle.events if item.id == "credit_limit_review")

    resolve_event(bundle, tightening.state, review)
    resolve_event_choice(bundle, tightening.state, "credit_limit_review", "tighten_up")

    resolve_event(bundle, coasting.state, review)
    resolve_event_choice(bundle, coasting.state, "credit_limit_review", "coast")

    resolve_month(quiet_bundle, tightening.state, tightening.rng)
    resolve_month(quiet_bundle, coasting.state, coasting.rng)

    assert tightening.state.player.credit_rebuild_streak > coasting.state.player.credit_rebuild_streak
    assert tightening.state.player.credit_utilization_pressure <= coasting.state.player.credit_utilization_pressure - 4


def test_education_recovery_choice_outperforms_pushthrough_on_next_quiet_month(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    recovery = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    push = controller_factory(opening_path_id="college_university", city_id="mid_size_city")

    for controller in (recovery, push):
        state = controller.state
        state.player.education.program_id = "full_time_university"
        state.player.education.is_active = True
        state.player.education.intensity_level = "intensive"
        state.player.selected_focus_action_id = "overtime"
        state.player.stress = 72
        state.player.energy = 38
        start_status_arc(
            bundle,
            state,
            "education_slipping",
            source_event_id="exam_probation_hearing",
            duration_months=3,
            severity=3,
        )

    probation = next(item for item in bundle.events if item.id == "exam_probation_hearing")

    resolve_event(bundle, recovery.state, probation)
    resolve_event_choice(bundle, recovery.state, "exam_probation_hearing", "cut_hours_and_recover_standing")

    resolve_event(bundle, push.state, probation)
    resolve_event_choice(bundle, push.state, "exam_probation_hearing", "push_through_probation")

    resolve_month(quiet_bundle, recovery.state, recovery.rng)
    resolve_month(quiet_bundle, push.state, push.rng)

    recovery_score = calculate_final_score(bundle, recovery.state).final_score
    push_score = calculate_final_score(bundle, push.state).final_score

    assert recovery.state.player.education.standing > push.state.player.education.standing
    assert recovery_score > push_score


def test_phase_status_arc_education_drag_hurts_standing_in_quiet_month(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    clean = controller_factory(opening_path_id="college_university")
    slipping = controller_factory(opening_path_id="college_university")
    for controller in (clean, slipping):
        controller.state.player.education.program_id = "full_time_university"
        controller.state.player.education.is_active = True
        controller.state.player.education.intensity_level = "standard"
        controller.state.player.stress = 58
        controller.state.player.energy = 46

    start_status_arc(
        bundle,
        slipping.state,
        "education_slipping",
        source_event_id="overtime_exam_collision",
        duration_months=3,
        severity=2,
    )

    resolve_month(quiet_bundle, clean.state, clean.rng)
    resolve_month(quiet_bundle, slipping.state, slipping.rng)

    assert slipping.state.player.education.standing < clean.state.player.education.standing


def test_phase_status_arc_lease_warning_starts_and_enforcement_escalates_arc(bundle, controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    state = controller.state
    state.current_month = 14
    state.player.housing.option_id = "solo_rental"
    state.player.housing.housing_stability = 36
    state.player.credit_score = 552
    state.player.debt = 12600
    state.player.cash = 140
    state.player.savings = 0
    state.player.monthly_surplus = -220

    lease_warning = next(item for item in bundle.events if item.id == "lease_default_warning")
    enforcement = next(item for item in bundle.events if item.id == "lease_enforcement_notice")

    resolve_event(bundle, state, lease_warning)

    assert len(state.active_status_arcs) == 1
    first_arc = state.active_status_arcs[0]
    assert first_arc.arc_id == "lease_pressure"
    assert first_arc.source_event_id == "lease_default_warning"
    first_months = first_arc.remaining_months

    resolve_event_choice(bundle, state, "lease_default_warning", "borrow_to_cover_shortfall")
    resolve_event(bundle, state, enforcement)

    assert len(state.active_status_arcs) == 1
    lease_arc = state.active_status_arcs[0]
    assert lease_arc.arc_id == "lease_pressure"
    assert lease_arc.source_event_id == "lease_enforcement_notice"
    assert lease_arc.remaining_months > first_months
    assert lease_arc.severity == 3


def test_phase_status_arc_burnout_warning_starts_and_burnout_month_escalates_arc(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    state = controller.state
    state.current_month = 10
    state.player.selected_focus_action_id = "overtime"
    state.player.stress = 74
    state.player.energy = 32

    attrition = next(item for item in bundle.events if item.id == "overtime_attrition_warning")
    burnout = next(item for item in bundle.events if item.id == "burnout_month")

    resolve_event(bundle, state, attrition)

    assert len(state.active_status_arcs) == 1
    first_arc = state.active_status_arcs[0]
    assert first_arc.arc_id == "burnout_risk"
    assert first_arc.source_event_id == "overtime_attrition_warning"
    assert first_arc.severity == 2

    resolve_event_choice(bundle, state, "overtime_attrition_warning", "rebalance_workload")
    softened = state.active_status_arcs[0]
    assert softened.arc_id == "burnout_risk"
    assert softened.severity == 1

    resolve_event(bundle, state, burnout)

    assert len(state.active_status_arcs) == 1
    burnout_arc = state.active_status_arcs[0]
    assert burnout_arc.arc_id == "burnout_risk"
    assert burnout_arc.source_event_id == "burnout_month"
    assert burnout_arc.severity == 3


def test_career_tracks_produce_distinct_monthly_income(bundle, controller_factory):
    warehouse = controller_factory(opening_path_id="full_time_work")
    sales = controller_factory(opening_path_id="gap_year_mixed_hustle", city_id="high_opportunity_metro")
    sales.change_career("sales")
    warehouse_income = current_income(bundle, warehouse.state, 1.0)
    sales_income = current_income(bundle, sales.state, 1.0)
    assert warehouse_income != sales_income


def test_education_path_changes_finances_and_progress(bundle, controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    starting_months = controller.state.player.education.months_completed
    starting_cash = controller.state.player.cash
    controller.resolve_month()
    assert controller.state.player.education.months_completed > starting_months
    assert controller.state.player.cash <= starting_cash + controller.state.player.monthly_income
    assert controller.state.player.monthly_expenses > 0


def test_study_push_improves_school_performance_without_speeding_calendar(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    baseline = controller_factory(opening_path_id="college_university")
    pushed = controller_factory(opening_path_id="college_university")
    baseline.state.player.selected_focus_action_id = "social_maintenance"
    pushed.state.player.selected_focus_action_id = "study_push"
    resolve_month(quiet_bundle, baseline.state, baseline.rng)
    resolve_month(quiet_bundle, pushed.state, pushed.rng)
    assert baseline.state.player.education.months_completed == 1
    assert pushed.state.player.education.months_completed == 1
    assert pushed.state.player.education.standing >= baseline.state.player.education.standing
    assert pushed.state.player.education.college_gpa >= baseline.state.player.education.college_gpa


def test_budget_stances_meaningfully_differ(controller_factory):
    balanced = controller_factory()
    payoff = controller_factory()
    payoff.change_budget_stance("aggressive_debt_payoff")
    balanced.resolve_month()
    payoff.resolve_month()
    assert payoff.state.player.debt <= balanced.state.player.debt
    assert payoff.state.player.life_satisfaction <= balanced.state.player.life_satisfaction


def test_focus_actions_meaningfully_differ(controller_factory):
    overtime = controller_factory()
    recover = controller_factory()
    recover.change_focus_action("recovery_month")
    overtime.resolve_month()
    recover.resolve_month()
    assert recover.state.player.energy >= overtime.state.player.energy
    assert recover.state.player.life_satisfaction >= overtime.state.player.life_satisfaction


def test_recovery_month_can_lower_stress_in_supportive_setup(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="full_time_work", city_id="hometown_low_cost")
    controller.state.player.stress = 42
    controller.state.player.selected_focus_action_id = "recovery_month"
    starting_stress = controller.state.player.stress
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert controller.state.player.stress < starting_stress


def test_easy_mode_recovery_month_can_stabilize_stress(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        opening_path_id="stay_home_stack_cash",
        difficulty_id="easy",
        city_id="hometown_low_cost",
        family_support_level_id="high",
        savings_band_id="solid",
    )
    controller.change_focus_action("recovery_month")
    controller.change_budget_stance("quality_of_life")
    starting_stress = controller.state.player.stress
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert controller.state.player.stress < starting_stress


def test_easy_mode_risky_month_can_still_raise_stress(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        difficulty_id="easy",
        city_id="mid_size_city",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    controller.state.player.selected_focus_action_id = "overtime"
    starting_stress = controller.state.player.stress
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert controller.state.player.stress > starting_stress


def test_easy_mode_big_city_recovery_can_reduce_stress(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        difficulty_id="easy",
        city_id="high_opportunity_metro",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    controller.state.player.selected_focus_action_id = "recovery_month"
    controller.state.player.stress = 66
    controller.state.player.energy = 62
    controller.state.player.housing.housing_stability = 58
    controller.state.player.transport.reliability_score = 72
    controller.state.player.debt = 3800
    controller.state.player.credit_score = 660
    controller.state.player.social_stability = 56
    controller.state.player.family_support = 36
    starting_stress = controller.state.player.stress

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.stress < starting_stress


def test_easy_big_city_recovery_reports_easing_pressure_trend(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        difficulty_id="easy",
        city_id="high_opportunity_metro",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    player = controller.state.player
    player.selected_focus_action_id = "recovery_month"
    player.stress = 82
    player.energy = 24
    player.housing.housing_stability = 46
    player.transport.reliability_score = 54
    player.debt = 14000
    player.credit_score = 620
    player.social_stability = 40
    player.family_support = 30
    player.cash = 100
    player.savings = 50

    resolve_month(quiet_bundle, controller.state, controller.rng)

    trend_line = next((line for line in controller.state.recent_summary if line.startswith("Pressure trend:")), "")
    assert "easing" in trend_line


def test_normal_mode_same_stable_recovery_setup_is_easier_in_hometown_than_metro(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    hometown = controller_factory(
        difficulty_id="normal",
        city_id="hometown_low_cost",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="move_out_immediately",
    )
    metro = controller_factory(
        difficulty_id="normal",
        city_id="high_opportunity_metro",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="move_out_immediately",
    )

    for controller in (hometown, metro):
        player = controller.state.player
        player.selected_focus_action_id = "recovery_month"
        player.stress = 60
        player.energy = 58
        player.housing.housing_stability = 62
        player.transport.reliability_score = 76
        player.debt = 4200
        player.credit_score = 650
        player.social_stability = 58
        player.family_support = 44

    hometown_start = hometown.state.player.stress
    metro_start = metro.state.player.stress

    resolve_month(quiet_bundle, hometown.state, hometown.rng)
    resolve_month(quiet_bundle, metro.state, metro.rng)

    hometown_drop = hometown_start - hometown.state.player.stress
    metro_drop = metro_start - metro.state.player.stress

    assert hometown_drop > 0
    assert metro_drop > 0
    assert hometown_drop > metro_drop


def test_severe_burnout_arc_cuts_metro_recovery_capacity(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    clean = controller_factory(
        difficulty_id="normal",
        city_id="high_opportunity_metro",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="move_out_immediately",
    )
    strained = controller_factory(
        difficulty_id="normal",
        city_id="high_opportunity_metro",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="move_out_immediately",
    )

    for controller in (clean, strained):
        player = controller.state.player
        player.selected_focus_action_id = "recovery_month"
        player.stress = 60
        player.energy = 58
        player.housing.housing_stability = 62
        player.transport.reliability_score = 76
        player.debt = 4200
        player.credit_score = 650
        player.social_stability = 58
        player.family_support = 44

    start_status_arc(
        bundle,
        strained.state,
        "burnout_risk",
        source_event_id="burnout_month",
        duration_months=3,
        severity=3,
    )

    clean_start = clean.state.player.stress
    strained_start = strained.state.player.stress

    resolve_month(quiet_bundle, clean.state, clean.rng)
    resolve_month(quiet_bundle, strained.state, strained.rng)

    clean_drop = clean_start - clean.state.player.stress
    strained_drop = strained_start - strained.state.player.stress

    assert clean_drop > strained_drop


def test_recent_summary_reports_recovery_balance_reason(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    controller = controller_factory(
        difficulty_id="normal",
        city_id="high_opportunity_metro",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="move_out_immediately",
    )
    player = controller.state.player
    player.selected_focus_action_id = "recovery_month"
    player.stress = 62
    player.energy = 54
    player.housing.housing_stability = 60
    player.transport.reliability_score = 72
    player.debt = 5600
    player.credit_score = 640
    player.social_stability = 54
    player.family_support = 42

    start_status_arc(
        bundle,
        controller.state,
        "burnout_risk",
        source_event_id="burnout_month",
        duration_months=2,
        severity=2,
    )

    resolve_month(quiet_bundle, controller.state, controller.rng)

    balance_line = next((line for line in controller.state.recent_summary if line.startswith("Recovery balance:")), "")
    assert balance_line
    assert any(keyword in balance_line.lower() for keyword in ("recovery", "pressure", "city", "arc"))


def test_stress_pressure_map_rises_for_fragile_build_and_relieves_for_stable_build(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    fragile = controller_factory(
        difficulty_id="normal",
        city_id="mid_size_city",
        family_support_level_id="low",
        savings_band_id="none",
        opening_path_id="move_out_immediately",
    )
    stable = controller_factory(
        difficulty_id="easy",
        city_id="hometown_low_cost",
        family_support_level_id="high",
        savings_band_id="solid",
        opening_path_id="stay_home_stack_cash",
    )

    fragile.state.player.selected_focus_action_id = "overtime"
    fragile.state.player.stress = 62
    fragile.state.player.energy = 30
    fragile.state.player.housing.housing_stability = 34
    fragile.state.player.transport.reliability_score = 42
    fragile.state.player.debt = 19000
    fragile.state.player.credit_score = 540

    stable.state.player.selected_focus_action_id = "recovery_month"
    stable.state.player.stress = 52
    stable.state.player.energy = 70
    stable.state.player.housing.housing_stability = 82
    stable.state.player.transport.reliability_score = 90
    stable.state.player.debt = 800
    stable.state.player.credit_score = 760

    fragile_start = fragile.state.player.stress
    stable_start = stable.state.player.stress

    resolve_month(quiet_bundle, fragile.state, fragile.rng)
    resolve_month(quiet_bundle, stable.state, stable.rng)

    assert fragile.state.player.stress > fragile_start
    assert stable.state.player.stress < stable_start
    assert any("Pressure map:" in line for line in fragile.state.recent_summary)
    assert any("Pressure trend:" in line for line in fragile.state.recent_summary)


def test_credit_drift_penalizes_missed_obligations_and_rewards_clean_month(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    missed = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    clean = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost", difficulty_id="easy")

    missed.state.player.cash = 0
    missed.state.player.savings = 0
    missed.state.player.debt = 24000
    missed.state.player.credit_score = 660
    missed.state.player.selected_focus_action_id = "overtime"

    clean.state.player.cash = 2200
    clean.state.player.savings = 1400
    clean.state.player.debt = 1200
    clean.state.player.credit_score = 660
    clean.state.player.selected_focus_action_id = "recovery_month"

    missed_start = missed.state.player.credit_score
    clean_start = clean.state.player.credit_score

    resolve_month(quiet_bundle, missed.state, missed.rng)
    resolve_month(quiet_bundle, clean.state, clean.rng)

    assert missed.state.player.credit_score < missed_start
    assert clean.state.player.credit_score > clean_start
    assert any("Credit drift:" in line for line in missed.state.log_messages)


def test_repeated_clean_months_can_rebuild_fragile_credit_to_fair(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    controller = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost", difficulty_id="easy")
    controller.state.player.credit_score = 560
    controller.state.player.debt = 3200
    controller.state.player.cash = 2600
    controller.state.player.savings = 1800
    controller.state.player.selected_focus_action_id = "recovery_month"

    start_credit = controller.state.player.credit_score
    for _ in range(4):
        resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.credit_score >= 580
    assert controller.state.player.credit_score >= start_credit + 20


def test_phase4_credit_profile_tracks_missed_and_rebuild_streaks(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    missed = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    missed.state.player.cash = 0
    missed.state.player.savings = 0
    missed.state.player.debt = 22000
    missed.state.player.credit_score = 640
    missed.state.player.credit_rebuild_streak = 2
    missed.state.player.credit_missed_obligation_streak = 0
    missed.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="phase4_forced_credit_miss",
            label="Forced Credit Miss",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1600,
        )
    )

    clean = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost", difficulty_id="easy")
    clean.state.player.cash = 2400
    clean.state.player.savings = 1800
    clean.state.player.debt = 2600
    clean.state.player.credit_score = 610
    clean.state.player.selected_focus_action_id = "recovery_month"
    clean.state.player.credit_rebuild_streak = 0
    clean.state.player.credit_missed_obligation_streak = 2

    resolve_month(quiet_bundle, missed.state, missed.rng)
    resolve_month(quiet_bundle, clean.state, clean.rng)

    assert missed.state.player.credit_missed_obligation_streak >= 1
    assert missed.state.player.credit_rebuild_streak == 0
    assert clean.state.player.credit_rebuild_streak >= 1
    assert clean.state.player.credit_missed_obligation_streak == 0


def test_recent_summary_includes_stress_and_energy_breakdown(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="full_time_work", city_id="hometown_low_cost")
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert any(line.startswith("Stress ") for line in controller.state.recent_summary)
    assert any(line.startswith("Stress drivers:") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy ") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy drivers:") for line in controller.state.recent_summary)
    assert any(line.startswith("Credit ") for line in controller.state.recent_summary)
    assert any(line.startswith("Credit tier:") for line in controller.state.recent_summary)
    assert any(line.startswith("Situation family:") for line in controller.state.recent_summary)


def test_recent_summary_surfaces_recovery_route_and_blocked_doors(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 690
    controller.state.player.debt = 16500
    controller.state.player.monthly_surplus = -120
    controller.state.player.stress = 81
    controller.state.player.social_stability = 82
    controller.state.player.family_support = 70
    controller.state.player.last_social_lifeline_year = 0

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert any(line.startswith("Recovery route:") for line in controller.state.recent_summary)
    assert any(line.startswith("Blocked door:") for line in controller.state.recent_summary)


def test_degree_track_requires_real_gpa_and_credential(controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    controller.state.player.education.earned_credential_ids.append("university_degree")
    controller.state.player.education.is_active = False
    controller.state.player.education.college_gpa = 2.8
    allowed, reason = can_enter_career(controller.bundle, controller.state, "degree_gated_professional")
    assert allowed is False
    assert "GPA" in reason


def test_trades_promotion_waits_for_pass_state(controller_factory):
    controller = controller_factory(opening_path_id="trades_apprenticeship")
    controller.state.player.career.promotion_progress = 10
    maybe_promote(controller.bundle, controller.state)
    assert controller.state.player.career.tier_index == 0
    controller.state.player.education.training_passed = True
    controller.state.player.education.earned_credential_ids.append("apprenticeship_certificate")
    maybe_promote(controller.bundle, controller.state)
    assert controller.state.player.career.tier_index == 1


def test_branched_track_promotion_waits_for_branch_choice(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    controller.change_career("retail_service")
    controller.state.player.career.tier_index = 1
    controller.state.player.career.promotion_progress = 999
    controller.state.player.housing.housing_stability = 60
    controller.state.player.transport.reliability_score = 75
    controller.state.player.social_stability = 65
    controller.state.player.energy = 70
    controller.state.player.stress = 40
    maybe_promote(controller.bundle, controller.state)
    assert controller.state.player.career.tier_index == 1
    assert controller.state.pending_promotion_branch_track_id == "retail_service"
    assert any(item[1] for item in controller.pending_promotion_branch_choices())


def test_selecting_branch_unblocks_promotion(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    controller.change_career("retail_service")
    controller.state.player.career.tier_index = 1
    controller.state.player.career.promotion_progress = 999
    controller.state.player.housing.housing_stability = 60
    controller.state.player.transport.reliability_score = 75
    controller.state.player.social_stability = 65
    controller.state.player.energy = 70
    controller.state.player.stress = 40
    maybe_promote(controller.bundle, controller.state)
    controller.choose_career_branch("retail_management_track")
    maybe_promote(controller.bundle, controller.state)
    assert controller.state.player.career.tier_index == 2
    assert controller.state.pending_promotion_branch_track_id is None


def test_budget_signatures_change_shortfall_pressure(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    survival = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    balanced = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    balanced.change_budget_stance("balanced")
    for state in (survival.state, balanced.state):
        state.player.cash = 0
        state.player.savings = 0
        state.active_modifiers.append(
            ActiveMonthlyModifier(
                id="forced_shortfall",
                label="Forced Shortfall",
                remaining_months=2,
                income_multiplier=0.25,
                housing_cost_delta=2200,
            )
        )
    resolve_month(quiet_bundle, survival.state, survival.rng)
    resolve_month(quiet_bundle, balanced.state, balanced.rng)
    assert survival.state.player.stress > balanced.state.player.stress
    assert any("cash shock pressure" in line.lower() for line in survival.state.log_messages)


def test_market_chaser_takes_harder_correction_months(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(
        update={
            "primary_event_chance": 0.0,
            "secondary_event_chance": 0.0,
            "default_market_regime_id": "correction",
            "market_regimes": [regime for regime in bundle.config.market_regimes if regime.id == "correction"],
        }
    )
    cushion = controller_factory(opening_path_id="stay_home_stack_cash")
    chaser = controller_factory(opening_path_id="stay_home_stack_cash")
    chaser.change_wealth_strategy("market_chaser")
    for state in (cushion.state, chaser.state):
        state.player.index_fund = 5000
        state.player.aggressive_growth_fund = 3000
        state.player.cash = 0
    resolve_month(quiet_bundle, cushion.state, cushion.rng)
    resolve_month(quiet_bundle, chaser.state, chaser.rng)
    assert chaser.state.player.stress >= cushion.state.player.stress
    assert chaser.state.player.life_satisfaction <= cushion.state.player.life_satisfaction


def test_market_chaser_liquidation_hurts_more_than_cushion_first(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser.change_wealth_strategy("market_chaser")
    for controller in (cushion, chaser):
        controller.state.player.cash = 0
        controller.state.player.savings = 0
        controller.state.player.high_interest_savings = 300
        controller.state.player.index_fund = 1500
        controller.state.player.aggressive_growth_fund = 900
        controller.state.player.debt = 9000
        controller.state.active_modifiers.append(
            ActiveMonthlyModifier(
                id="forced_shortfall",
                label="Forced Shortfall",
                remaining_months=1,
                income_multiplier=0.15,
                housing_cost_delta=1800,
            )
        )
    resolve_month(quiet_bundle, cushion.state, cushion.rng)
    resolve_month(quiet_bundle, chaser.state, chaser.rng)
    assert chaser.state.player.stress > cushion.state.player.stress
    assert chaser.state.player.life_satisfaction <= cushion.state.player.life_satisfaction


def test_market_margin_cut_risk_now_reduces_credit_pressure_vs_hold_line_next_month(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    cut = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    hold = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller in (cut, hold):
        state = controller.state
        state.current_month = 18
        state.current_market_regime_id = "correction"
        state.player.wealth_strategy_id = "market_chaser"
        state.player.cash = 100
        state.player.savings = 80
        state.player.index_fund = 3500
        state.player.aggressive_growth_fund = 2000
        state.player.debt = 9800
        state.player.credit_score = 575
        state.player.credit_utilization_pressure = 84
        state.player.monthly_surplus = -120
        start_status_arc(
            bundle,
            state,
            "credit_squeeze",
            source_event_id="credit_limit_review",
            duration_months=4,
            severity=3,
        )

    margin_call = next(item for item in bundle.events if item.id == "market_margin_call")

    resolve_event(bundle, cut.state, margin_call)
    resolve_event_choice(bundle, cut.state, "market_margin_call", "cut_risk_now")

    resolve_event(bundle, hold.state, margin_call)
    resolve_event_choice(bundle, hold.state, "market_margin_call", "hold_the_line")

    resolve_month(quiet_bundle, cut.state, cut.rng)
    resolve_month(quiet_bundle, hold.state, hold.rng)

    assert cut.state.player.credit_utilization_pressure <= hold.state.player.credit_utilization_pressure - 4
    assert calculate_final_score(bundle, cut.state).final_score > calculate_final_score(bundle, hold.state).final_score


def test_steady_compound_automation_creates_clearer_next_month_advantage_than_flexibility(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    automated = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")
    flexible = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost")

    for controller in (automated, flexible):
        state = controller.state
        state.current_month = 16
        state.current_market_regime_id = "strong"
        state.player.wealth_strategy_id = "steady_builder"
        state.player.cash = 2200
        state.player.savings = 1800
        state.player.high_interest_savings = 1200
        state.player.credit_score = 710
        state.player.monthly_surplus = 260
        state.player.debt = 3200

    compound = next(item for item in bundle.events if item.id == "steady_compound_window")

    resolve_event(bundle, automated.state, compound)
    resolve_event_choice(bundle, automated.state, "steady_compound_window", "automate_compound")

    resolve_event(bundle, flexible.state, compound)
    resolve_event_choice(bundle, flexible.state, "steady_compound_window", "keep_flexibility")

    resolve_month(quiet_bundle, automated.state, automated.rng)
    resolve_month(quiet_bundle, flexible.state, flexible.rng)

    automated_invested = automated.state.player.index_fund + automated.state.player.aggressive_growth_fund
    flexible_invested = flexible.state.player.index_fund + flexible.state.player.aggressive_growth_fund

    assert automated_invested >= flexible_invested + 220
    assert calculate_final_score(bundle, automated.state).final_score >= calculate_final_score(bundle, flexible.state).final_score + 0.5


def test_phase4_cushion_first_softens_lease_pressure_faster_than_market_chaser(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    cushion = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    chaser = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller, strategy_id in ((cushion, "cushion_first"), (chaser, "market_chaser")):
        state = controller.state
        state.player.wealth_strategy_id = strategy_id
        state.player.cash = 90
        state.player.savings = 500
        state.player.high_interest_savings = 1200
        state.player.index_fund = 900
        state.player.aggressive_growth_fund = 350
        state.player.debt = 8800
        state.player.credit_score = 624
        state.player.stress = 70
        state.player.housing.option_id = "roommates"
        state.player.housing.housing_stability = 28
        state.player.housing.missed_payment_streak = 1
        start_status_arc(
            bundle,
            state,
            "lease_pressure",
            source_event_id="lease_default_warning",
            duration_months=3,
            severity=2,
        )

    resolve_month(quiet_bundle, cushion.state, cushion.rng)
    resolve_month(quiet_bundle, chaser.state, chaser.rng)

    cushion_arc = next(arc for arc in cushion.state.active_status_arcs if arc.arc_id == "lease_pressure")
    chaser_arc = next(arc for arc in chaser.state.active_status_arcs if arc.arc_id == "lease_pressure")

    assert cushion_arc.severity < chaser_arc.severity
    assert cushion.state.player.housing.housing_stability > chaser.state.player.housing.housing_stability


def test_phase4_debt_crusher_softens_credit_squeeze_faster_than_steady_builder(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    crusher = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    steady = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")

    for controller, strategy_id in ((crusher, "debt_crusher"), (steady, "steady_builder")):
        state = controller.state
        state.player.wealth_strategy_id = strategy_id
        state.player.cash = 520
        state.player.savings = 350
        state.player.high_interest_savings = 480
        state.player.index_fund = 900
        state.player.aggressive_growth_fund = 250
        state.player.debt = 14600
        state.player.credit_score = 592
        state.player.credit_utilization_pressure = 84
        state.player.credit_missed_obligation_streak = 0
        state.player.stress = 66
        start_status_arc(
            bundle,
            state,
            "credit_squeeze",
            source_event_id="credit_limit_review",
            duration_months=3,
            severity=2,
        )

    resolve_month(quiet_bundle, crusher.state, crusher.rng)
    resolve_month(quiet_bundle, steady.state, steady.rng)

    crusher_arc = next(arc for arc in crusher.state.active_status_arcs if arc.arc_id == "credit_squeeze")
    steady_arc = next(arc for arc in steady.state.active_status_arcs if arc.arc_id == "credit_squeeze")

    assert crusher_arc.severity < steady_arc.severity
    assert crusher.state.player.credit_score > steady.state.player.credit_score


def test_liquid_buffer_recovery_route_can_stabilize_housing(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.wealth_strategy_id = "cushion_first"
    controller.state.player.cash = 50
    controller.state.player.savings = 1300
    controller.state.player.high_interest_savings = 900
    controller.state.player.housing.option_id = "roommates"
    controller.state.player.housing.housing_stability = 30
    controller.state.player.housing.missed_payment_streak = 1
    controller.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.15,
            housing_cost_delta=1800,
        )
    )

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.housing.housing_stability >= 40
    assert controller.state.player.housing.missed_payment_streak == 0
    assert any("cash reserve" in line.lower() or "buffer" in line.lower() for line in controller.state.log_messages)


def test_transport_downgrade_recovery_route_can_stop_financed_trap(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.transport.option_id = "financed_car"
    controller.state.player.debt = 12600
    controller.state.player.credit_score = 602
    controller.state.player.cash = 80
    controller.state.player.savings = 120
    controller.state.player.stress = 74
    controller.state.player.monthly_surplus = -220
    controller.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1400,
            transport_cost_delta=220,
        )
    )

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.transport.option_id in {"transit", "bike"}
    assert any("transport downgrade" in line.lower() for line in controller.state.log_messages)


def test_education_pause_recovery_route_triggers_under_burnout_and_cash_pressure(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    controller.state.player.education.program_id = "full_time_university"
    controller.state.player.education.is_active = True
    controller.state.player.education.is_paused = False
    controller.state.player.stress = 88
    controller.state.player.energy = 20
    controller.state.player.cash = 60
    controller.state.player.savings = 80
    controller.state.player.monthly_surplus = -180
    controller.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1500,
        )
    )

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.education.is_active is False
    assert controller.state.player.education.is_paused is True
    assert any("paused education" in line.lower() for line in controller.state.log_messages)


def test_phase6_family_fallback_route_exists_for_hometown_support_and_not_for_metro(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    fallback = controller_factory(opening_path_id="move_out_immediately", city_id="hometown_low_cost")
    fallback.state.player.housing.option_id = "roommates"
    fallback.state.player.housing.housing_stability = 30
    fallback.state.player.family_support = 82
    fallback.state.player.cash = 60
    fallback.state.player.savings = 80
    fallback.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1300,
        )
    )

    no_fallback = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    no_fallback.state.player.housing.option_id = "roommates"
    no_fallback.state.player.housing.housing_stability = 30
    no_fallback.state.player.family_support = 82
    no_fallback.state.player.cash = 60
    no_fallback.state.player.savings = 80
    no_fallback.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1300,
        )
    )

    resolve_month(quiet_bundle, fallback.state, fallback.rng)
    resolve_month(quiet_bundle, no_fallback.state, no_fallback.rng)

    assert fallback.state.player.housing.option_id == "parents"
    assert no_fallback.state.player.housing.option_id != "parents"


def test_phase6_education_deintensify_route_keeps_school_lane_alive(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="college_university", city_id="mid_size_city")
    controller.state.player.education.program_id = "full_time_university"
    controller.state.player.education.is_active = True
    controller.state.player.education.is_paused = False
    controller.state.player.education.intensity_level = "intensive"
    controller.state.player.stress = 78
    controller.state.player.energy = 34
    controller.state.player.cash = 520
    controller.state.player.savings = 380
    controller.state.player.monthly_surplus = -20

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.education.is_active is True
    assert controller.state.player.education.intensity_level in {"standard", "light"}
    assert any("de-intensif" in line.lower() for line in controller.state.log_messages)


def test_phase6_branch_reset_recovery_route_is_build_dependent(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    reset = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    reset.change_career("retail_service")
    reset.state.current_month = 24
    reset.state.player.career.branch_id = "retail_management_track"
    reset.state.player.career.tier_index = 2
    reset.state.player.career.promotion_momentum = 28
    reset.state.player.stress = 88
    reset.state.player.energy = 22
    reset.state.player.monthly_surplus = -180
    reset.state.player.debt = 12600
    reset.state.player.cash = 60
    reset.state.player.savings = 40
    reset.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="forced_shortfall",
            label="Forced Shortfall",
            remaining_months=1,
            income_multiplier=0.2,
            housing_cost_delta=1400,
        )
    )

    stable = controller_factory(opening_path_id="full_time_work", city_id="mid_size_city")
    stable.change_career("retail_service")
    stable.state.current_month = 24
    stable.state.player.career.branch_id = "retail_management_track"
    stable.state.player.career.tier_index = 2
    stable.state.player.career.promotion_momentum = 62
    stable.state.player.stress = 54
    stable.state.player.energy = 56
    stable.state.player.monthly_surplus = 180
    stable.state.player.debt = 5200
    stable.state.player.cash = 1200
    stable.state.player.savings = 900

    resolve_month(quiet_bundle, reset.state, reset.rng)
    resolve_month(quiet_bundle, stable.state, stable.rng)

    assert reset.state.player.career.branch_id is None
    assert stable.state.player.career.branch_id == "retail_management_track"
    assert any("branch reset" in line.lower() for line in reset.state.log_messages)


def test_clean_credit_rebuild_route_applies_in_fragile_band(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="stay_home_stack_cash", city_id="hometown_low_cost", difficulty_id="easy")
    controller.state.player.credit_score = 565
    controller.state.player.debt = 3200
    controller.state.player.cash = 1900
    controller.state.player.savings = 1400
    controller.state.player.monthly_surplus = 220
    controller.state.player.housing.missed_payment_streak = 0
    controller.state.player.stress = 48
    start_credit = controller.state.player.credit_score

    resolve_month(quiet_bundle, controller.state, controller.rng)

    assert controller.state.player.credit_score > start_credit
    assert any("credit rebuild" in line.lower() for line in controller.state.log_messages)


def test_transport_signature_can_boost_promotion_momentum(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    reliable = controller_factory(opening_path_id="full_time_work")
    fragile = controller_factory(opening_path_id="full_time_work")
    reliable.change_transport("reliable_used_car")
    reliable.state.player.transport.reliability_score = 90
    fragile.state.player.transport.reliability_score = 62
    for state in (reliable.state, fragile.state):
        state.player.energy = 70
        state.player.stress = 40
    resolve_month(quiet_bundle, reliable.state, reliable.rng)
    resolve_month(quiet_bundle, fragile.state, fragile.rng)
    assert reliable.state.player.career.promotion_momentum > fragile.state.player.career.promotion_momentum


def test_education_signature_changes_career_momentum(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    healthy = controller_factory(opening_path_id="college_university")
    strained = controller_factory(opening_path_id="college_university")
    healthy.state.player.education.standing = 78
    healthy.state.player.stress = 48
    healthy.state.player.energy = 62
    strained.state.player.education.standing = 46
    strained.state.player.stress = 82
    strained.state.player.energy = 24
    resolve_month(quiet_bundle, healthy.state, healthy.rng)
    resolve_month(quiet_bundle, strained.state, strained.rng)
    assert healthy.state.player.career.promotion_momentum > strained.state.player.career.promotion_momentum


def test_pause_resume_education_is_safe(controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    controller.change_education("full_time_university")
    assert controller.state.player.education.is_active is False
    controller.change_education("full_time_university")
    assert controller.state.player.education.is_active is True


def test_collections_failure_triggers(bundle, controller_factory):
    controller = controller_factory()
    controller.state.player.debt = controller.state.debt_game_over_threshold
    resolve_month(bundle, controller.state, controller.rng)
    assert controller.state.game_over_reason == "collections"


def test_housing_loss_failure_triggers(controller_factory):
    controller = controller_factory(city_id="mid_size_city", opening_path_id="move_out_immediately")
    controller.state.player.housing.missed_payment_streak = controller.state.housing_miss_limit
    controller.state.player.cash = 0
    controller.state.player.savings = 0
    controller.state.active_modifiers.append(
        ActiveMonthlyModifier(
            id="rent_spike",
            label="Rent Spike",
            remaining_months=2,
            income_multiplier=0.01,
            housing_cost_delta=5000,
        )
    )
    controller.resolve_month()
    assert controller.state.game_over_reason == "housing_loss"


def test_annual_milestone_records_every_12_months(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(
        preset_id="supported_student",
        difficulty_id="easy",
        opening_path_id="stay_home_stack_cash",
        family_support_level_id="high",
        savings_band_id="solid",
    )
    controller.change_focus_action("recovery_month")
    controller.change_budget_stance("quality_of_life")
    for _ in range(12):
        if controller.is_finished():
            break
        resolve_month(quiet_bundle, controller.state, controller.rng)
    assert len(controller.state.annual_milestones) == 1
    assert controller.state.annual_milestones[0].age == 19


def test_crisis_warning_logic(controller_factory):
    controller = controller_factory()
    controller.state.player.debt = int(controller.state.debt_game_over_threshold * 0.8)
    controller.state.player.stress = 82
    controller.state.player.energy = 20
    controller.state.player.housing.missed_payment_streak = 1
    warnings = controller.build_crisis_warnings()
    assert any("Debt" in warning for warning in warnings)
    assert any("Stress" in warning for warning in warnings)
    assert any("Energy" in warning for warning in warnings)


def test_crisis_warnings_surface_blocked_credit_doors(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 690
    controller.state.player.debt = 16500
    controller.state.player.monthly_surplus = -120

    warnings = controller.build_crisis_warnings()

    assert any("solo rental" in warning.lower() for warning in warnings)
    assert any("financed car" in warning.lower() for warning in warnings)


def test_scoring_returns_weighted_summary(bundle, controller_factory):
    controller = controller_factory(difficulty_id="easy", opening_path_id="stay_home_stack_cash")
    for _ in range(6):
        if controller.is_finished():
            break
        controller.resolve_month()
    summary = calculate_final_score(bundle, controller.state)
    assert summary.ending_label in {
        "Financially Secure Builder",
        "Burned-Out High Earner",
        "Educated but Overleveraged",
        "Stable Blue-Collar Grinder",
        "Drifting Survivor",
        "Late Bloomer With Momentum",
        "Crushed by Bad Decisions",
        "Dispatch-Built Stabilizer",
        "Equipment Track Builder",
        "Floor Operations Grinder",
        "Retail Operations Climber",
        "Commission-Driven Climber",
        "Client Book Builder",
    }
    assert 0 <= summary.final_score <= 100


def test_scoring_rewards_stable_recovery_over_fragile_liquidation(bundle, controller_factory):
    stable = controller_factory(opening_path_id="stay_home_stack_cash")
    fragile = controller_factory(opening_path_id="stay_home_stack_cash")

    for controller in (stable, fragile):
        player = controller.state.player
        player.cash = 22000
        player.savings = 12000
        player.high_interest_savings = 4000
        player.index_fund = 8000
        player.aggressive_growth_fund = 3000
        player.debt = 2500
        player.monthly_surplus = 520
        player.career.tier_index = 3
        player.education.completed_program_ids = ["certificate"]
        player.education.earned_credential_ids = ["certificate_ops"]

    stable.state.player.credit_score = 755
    stable.state.player.housing.housing_stability = 82
    stable.state.player.social_stability = 74
    stable.state.player.stress = 28
    stable.state.player.energy = 80
    stable.state.player.emergency_liquidation_count = 0

    fragile.state.player.credit_score = 610
    fragile.state.player.housing.housing_stability = 42
    fragile.state.player.social_stability = 38
    fragile.state.player.stress = 72
    fragile.state.player.energy = 34
    fragile.state.player.emergency_liquidation_count = 3

    stable_summary = calculate_final_score(bundle, stable.state)
    fragile_summary = calculate_final_score(bundle, fragile.state)

    assert stable_summary.final_score > fragile_summary.final_score


def test_phase5_score_reflects_wealth_signature_alignment(bundle, controller_factory):
    debt_crusher = controller_factory(opening_path_id="stay_home_stack_cash")
    market_chaser = controller_factory(opening_path_id="stay_home_stack_cash")

    for controller in (debt_crusher, market_chaser):
        player = controller.state.player
        player.cash = 8000
        player.savings = 5000
        player.high_interest_savings = 1500
        player.index_fund = 4500
        player.aggressive_growth_fund = 1000
        player.debt = 2200
        player.monthly_surplus = 260
        player.credit_score = 710
        player.housing.housing_stability = 74
        player.social_stability = 60
        player.stress = 36
        player.energy = 72
        player.career.tier_index = 2

    debt_crusher.state.player.wealth_strategy_id = "debt_crusher"
    market_chaser.state.player.wealth_strategy_id = "market_chaser"

    crusher_score = calculate_final_score(bundle, debt_crusher.state).final_score
    chaser_score = calculate_final_score(bundle, market_chaser.state).final_score

    assert crusher_score > chaser_score


def test_final_truth_stable_metro_recovery_beats_arc_stacked_pressure(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})

    stable = controller_factory(opening_path_id="move_out_immediately", city_id="high_opportunity_metro")
    stacked = controller_factory(opening_path_id="move_out_immediately", city_id="high_opportunity_metro")

    for controller in (stable, stacked):
        player = controller.state.player
        player.selected_focus_action_id = "recovery_month"
        player.stress = 62
        player.energy = 58
        player.housing.housing_stability = 64
        player.transport.reliability_score = 76
        player.debt = 4800
        player.credit_score = 684
        player.social_stability = 58
        player.family_support = 42
        player.cash = 650
        player.savings = 320
        player.monthly_surplus = 110

    start_status_arc(
        bundle,
        stacked.state,
        "lease_pressure",
        source_event_id="lease_default_warning",
        duration_months=3,
        severity=3,
    )
    start_status_arc(
        bundle,
        stacked.state,
        "burnout_risk",
        source_event_id="overtime_attrition_warning",
        duration_months=3,
        severity=3,
    )

    stable_start = stable.state.player.stress
    stacked_start = stacked.state.player.stress

    resolve_month(quiet_bundle, stable.state, stable.rng)
    resolve_month(quiet_bundle, stacked.state, stacked.rng)

    stable_drop = stable_start - stable.state.player.stress
    stacked_drop = stacked_start - stacked.state.player.stress

    assert stable_drop >= 4
    assert stable_drop > stacked_drop
    assert calculate_final_score(bundle, stable.state).final_score > calculate_final_score(bundle, stacked.state).final_score


def test_phase7_similar_money_fragility_and_branch_quality_split_scores(bundle, controller_factory):
    strong = controller_factory(opening_path_id="full_time_work")
    fragile = controller_factory(opening_path_id="full_time_work")

    for controller in (strong, fragile):
        player = controller.state.player
        player.cash = 22000
        player.savings = 12000
        player.high_interest_savings = 4000
        player.index_fund = 7000
        player.aggressive_growth_fund = 2000
        player.debt = 4500
        player.monthly_surplus = 360
        player.career.track_id = "warehouse_logistics"
        player.career.tier_index = 3
        player.career.promotion_progress = 6

    strong.state.player.career.branch_id = "warehouse_dispatch_track"
    strong.state.player.career.promotion_momentum = 74
    strong.state.player.credit_score = 742
    strong.state.player.housing.housing_stability = 80
    strong.state.player.social_stability = 70
    strong.state.player.stress = 34
    strong.state.player.energy = 76
    strong.state.player.emergency_liquidation_count = 0

    fragile.state.player.career.branch_id = None
    fragile.state.player.career.promotion_momentum = 34
    fragile.state.player.credit_score = 610
    fragile.state.player.housing.housing_stability = 46
    fragile.state.player.housing.missed_payment_streak = 1
    fragile.state.player.social_stability = 40
    fragile.state.player.stress = 76
    fragile.state.player.energy = 32
    fragile.state.player.emergency_liquidation_count = 2

    strong_score = calculate_final_score(bundle, strong.state).final_score
    fragile_score = calculate_final_score(bundle, fragile.state).final_score

    assert strong_score >= fragile_score + 8


def test_phase7_final_summary_names_built_worked_and_held_back(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    player = controller.state.player
    player.career.track_id = "warehouse_logistics"
    player.career.branch_id = "warehouse_dispatch_track"
    player.career.tier_index = 3
    player.cash = 24000
    player.savings = 12000
    player.high_interest_savings = 5000
    player.index_fund = 8000
    player.debt = 2600
    player.monthly_surplus = 520
    player.credit_score = 736
    player.housing.housing_stability = 78
    player.social_stability = 66
    player.stress = 40
    player.energy = 72

    summary = calculate_final_score(bundle, controller.state)

    assert "Built:" in summary.outcome
    assert "Worked:" in summary.outcome
    assert "Held back:" in summary.outcome


def test_scoring_rewards_committed_branch_identity(bundle, controller_factory):
    unbranched = controller_factory(opening_path_id="full_time_work")
    branched = controller_factory(opening_path_id="full_time_work")

    for controller in (unbranched, branched):
        player = controller.state.player
        player.cash = 18000
        player.savings = 10000
        player.high_interest_savings = 3000
        player.index_fund = 5000
        player.debt = 3500
        player.monthly_surplus = 420
        player.credit_score = 720
        player.housing.housing_stability = 74
        player.social_stability = 60
        player.stress = 34
        player.energy = 72
        player.career.tier_index = 2
        player.career.promotion_progress = 5

    branched.state.player.career.branch_id = "warehouse_dispatch_track"

    unbranched_summary = calculate_final_score(bundle, unbranched.state)
    branched_summary = calculate_final_score(bundle, branched.state)

    assert branched_summary.final_score > unbranched_summary.final_score


def test_final_score_summary_mentions_branch_identity_in_outcome(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    player = controller.state.player
    player.career.track_id = "warehouse_logistics"
    player.career.branch_id = "warehouse_dispatch_track"
    player.career.tier_index = 3
    player.cash = 24000
    player.savings = 14000
    player.high_interest_savings = 6000
    player.index_fund = 9000
    player.debt = 1800
    player.monthly_surplus = 620
    player.credit_score = 742
    player.housing.housing_stability = 80
    player.social_stability = 72
    player.stress = 32
    player.energy = 78
    controller.state.current_month = controller.state.total_months + 1

    summary = calculate_final_score(bundle, controller.state)

    assert "Dispatch Coordination" in summary.outcome


def test_branch_run_receives_branch_aware_ending_label(bundle, controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    player = controller.state.player
    player.career.track_id = "warehouse_logistics"
    player.career.branch_id = "warehouse_dispatch_track"
    player.career.tier_index = 3
    player.cash = 22000
    player.savings = 12000
    player.high_interest_savings = 5000
    player.index_fund = 8000
    player.debt = 2500
    player.monthly_surplus = 580
    player.credit_score = 730
    player.housing.housing_stability = 76
    player.social_stability = 64
    player.stress = 38
    player.energy = 74

    summary = calculate_final_score(bundle, controller.state)

    assert summary.ending_label == "Dispatch-Built Stabilizer"


def test_scoring_penalizes_unresolved_consequence_pressure(bundle, controller_factory):
    stable = controller_factory(opening_path_id="full_time_work")
    unstable = controller_factory(opening_path_id="full_time_work")

    for controller in (stable, unstable):
        player = controller.state.player
        player.cash = 32000
        player.savings = 18000
        player.high_interest_savings = 7000
        player.index_fund = 12000
        player.aggressive_growth_fund = 4000
        player.debt = 2800
        player.monthly_surplus = 520
        player.credit_score = 744
        player.housing.housing_stability = 78
        player.social_stability = 70
        player.stress = 34
        player.energy = 76
        player.career.tier_index = 3
        player.career.branch_id = "warehouse_dispatch_track"

    unstable.state.pending_events.append(
        PendingEvent(
            event_id="credit_limit_review",
            months_remaining=1,
            source_event_id="collections_warning",
        )
    )
    unstable.state.pending_user_choice_event_id = "collections_warning"
    unstable.state.player.housing.missed_payment_streak = 1
    unstable.state.player.emergency_liquidation_count = 2

    stable_score = calculate_final_score(bundle, stable.state).final_score
    unstable_score = calculate_final_score(bundle, unstable.state).final_score

    assert stable_score > unstable_score


def test_scoring_penalizes_pending_fallout_even_with_matching_stats(bundle, controller_factory):
    clean = controller_factory(opening_path_id="full_time_work")
    pending = controller_factory(opening_path_id="full_time_work")

    for controller in (clean, pending):
        player = controller.state.player
        player.cash = 26000
        player.savings = 12000
        player.high_interest_savings = 5000
        player.index_fund = 7000
        player.aggressive_growth_fund = 2500
        player.debt = 2400
        player.monthly_surplus = 420
        player.credit_score = 736
        player.housing.housing_stability = 74
        player.social_stability = 63
        player.stress = 38
        player.energy = 72
        player.career.tier_index = 3
        player.career.track_id = "warehouse_logistics"
        player.career.branch_id = "warehouse_dispatch_track"

    pending.state.pending_events.append(
        PendingEvent(
            event_id="credit_limit_review",
            months_remaining=1,
            source_event_id="collections_warning",
        )
    )
    pending.state.pending_user_choice_event_id = "collections_warning"

    clean_score = calculate_final_score(bundle, clean.state).final_score
    pending_score = calculate_final_score(bundle, pending.state).final_score

    assert clean_score > pending_score
