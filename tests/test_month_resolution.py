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
    cushion.change_wealth_strategy("cushion_first")
    chaser.change_wealth_strategy("market_chaser")
    for state in (cushion.state, chaser.state):
        state.player.index_fund = 5000
        state.player.aggressive_growth_fund = 3000
        state.player.cash = 0
    resolve_month(quiet_bundle, cushion.state, cushion.rng)
    resolve_month(quiet_bundle, chaser.state, chaser.rng)
    assert chaser.state.player.stress >= cushion.state.player.stress
    assert chaser.state.player.life_satisfaction <= cushion.state.player.life_satisfaction


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
