from __future__ import annotations

from budgetwars.engine.careers import can_enter_career, current_income, maybe_promote
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import calculate_final_score
from budgetwars.engine.housing import monthly_housing_cost
from budgetwars.engine.transport import monthly_transport_cost
from budgetwars.models import ActiveMonthlyModifier


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


def test_recent_summary_includes_stress_and_energy_breakdown(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="full_time_work", city_id="hometown_low_cost")
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert any(line.startswith("Stress ") for line in controller.state.recent_summary)
    assert any(line.startswith("Stress drivers:") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy ") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy drivers:") for line in controller.state.recent_summary)


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
    }
    assert 0 <= summary.final_score <= 100
