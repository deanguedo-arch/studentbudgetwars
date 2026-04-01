from __future__ import annotations

from budgetwars.models import ActiveMonthlyModifier
from budgetwars.engine.month_resolution import resolve_month
from budgetwars.engine.scoring import calculate_final_score
from budgetwars.engine.careers import can_enter_career, current_income
from budgetwars.engine.education import education_monthly_cost
from budgetwars.engine.housing import monthly_housing_cost
from budgetwars.engine.transport import monthly_transport_cost


def test_start_state_from_preset_city_and_path(controller_factory):
    controller = controller_factory(
        preset_id="broke_but_ambitious",
        city_id="big_metro",
        opening_path_id="move_out_immediately",
    )
    state = controller.state
    assert state.player.current_city_id == "big_metro"
    assert state.player.opening_path_id == "move_out_immediately"
    assert state.player.housing_id == "roommates"
    assert state.player.transport_id == "transit"
    assert state.player.career.track_id == "service_retail"


def test_housing_change_affects_cost_and_state(bundle, controller_factory):
    controller = controller_factory(city_id="hometown")
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
    service = controller_factory(opening_path_id="full_time_work")
    service.change_career("service_retail")
    warehouse_income = current_income(bundle, warehouse.state, 1.0)
    service_income = current_income(bundle, service.state, 1.0)
    assert warehouse_income != service_income


def test_education_path_changes_finances_and_progress(bundle, controller_factory):
    controller = controller_factory(opening_path_id="college")
    starting_months = controller.state.player.education.months_completed
    starting_cash = controller.state.player.cash
    cost = education_monthly_cost(bundle, controller.state)
    controller.resolve_month()
    assert cost > 0
    assert controller.state.player.education.months_completed > starting_months
    assert controller.state.player.cash <= starting_cash + 3000


def test_budget_stances_meaningfully_differ(controller_factory):
    balanced = controller_factory()
    future = controller_factory()
    future.change_budget_stance("future_focused")
    balanced.resolve_month()
    future.resolve_month()
    assert future.state.player.savings >= balanced.state.player.savings
    assert future.state.player.life_satisfaction <= balanced.state.player.life_satisfaction


def test_focus_actions_meaningfully_differ(controller_factory):
    stack_cash = controller_factory()
    recover = controller_factory()
    recover.change_focus_action("recover")
    stack_cash.resolve_month()
    recover.resolve_month()
    assert recover.state.player.energy >= stack_cash.state.player.energy
    assert recover.state.player.life_satisfaction >= stack_cash.state.player.life_satisfaction


def test_recover_can_lower_stress_in_supportive_setup(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="full_time_work", city_id="hometown")
    controller.state.player.stress = 40
    controller.state.player.selected_focus_action_id = "recover"
    starting_stress = controller.state.player.stress
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert controller.state.player.stress < starting_stress


def test_recent_summary_includes_stress_and_energy_breakdown(bundle, controller_factory):
    quiet_bundle = bundle.model_copy(deep=True)
    quiet_bundle.config = quiet_bundle.config.model_copy(update={"primary_event_chance": 0.0, "secondary_event_chance": 0.0})
    controller = controller_factory(opening_path_id="full_time_work", city_id="hometown")
    resolve_month(quiet_bundle, controller.state, controller.rng)
    assert any(line.startswith("Stress ") for line in controller.state.recent_summary)
    assert any(line.startswith("Stress drivers:") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy ") for line in controller.state.recent_summary)
    assert any(line.startswith("Energy drivers:") for line in controller.state.recent_summary)


def test_office_track_requires_real_college_gpa(controller_factory):
    controller = controller_factory(opening_path_id="college")
    controller.state.player.education.earned_credential_ids.append("college_credential")
    controller.state.player.education.is_active = False
    controller.state.player.education.college_gpa = 2.4
    allowed, reason = can_enter_career(controller.bundle, controller.state, "office_professional")
    assert allowed is False
    assert "GPA" in reason


def test_high_college_gpa_opens_office_track(controller_factory):
    controller = controller_factory(opening_path_id="college")
    controller.state.player.education.earned_credential_ids.append("college_credential")
    controller.state.player.education.is_active = False
    controller.state.player.education.college_gpa = 3.3
    controller.change_career("office_professional")
    assert controller.state.player.career.track_id == "office_professional"


def test_collections_failure_triggers(bundle, controller_factory):
    controller = controller_factory()
    controller.state.player.debt = controller.state.debt_game_over_threshold
    resolve_month(bundle, controller.state, controller.rng)
    assert controller.state.game_over_reason == "collections"


def test_housing_loss_failure_triggers(controller_factory):
    controller = controller_factory(city_id="mid_size_city", opening_path_id="move_out_immediately")
    controller.state.missed_housing_payments = controller.state.housing_miss_limit
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


def test_scoring_returns_weighted_summary(bundle, controller_factory):
    controller = controller_factory()
    for _ in range(6):
        if controller.is_finished():
            break
        controller.resolve_month()
    summary = calculate_final_score(bundle, controller.state)
    assert summary.ending_label in {
        "Financially Secure Builder",
        "Stable Grinder",
        "Overleveraged Achiever",
        "Burned-Out Striver",
        "Drifting Survivor",
    }
    assert 0 <= summary.final_score <= 100
