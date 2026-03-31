from __future__ import annotations

from budgetwars.engine.scoring import calculate_final_score


def test_weekly_tick_hits_after_seventh_day(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="commuter_hustler", seed=5)
    starting_cash = controller.state.player.cash
    for _ in range(7):
        controller.rest()
    assert controller.state.current_day == 8
    assert controller.state.player.cash == starting_cash - 123


def test_exam_week_penalizes_missing_study(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="scholarship_grinder", seed=6)
    starting_gpa = controller.state.player.gpa
    for _ in range(14):
        controller.rest()
    assert controller.state.current_day == 15
    assert controller.state.player.gpa < starting_gpa


def test_low_energy_streak_causes_game_over(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, seed=11)
    controller.state = controller.state.model_copy(
        update={
            "low_energy_streak": quiet_bundle.config.low_energy_streak_limit - 1,
            "player": controller.state.player.model_copy(update={"energy": 4}),
        }
    )
    controller.study()
    assert controller.state.game_over_reason == "Energy collapse dragged on too long"


def test_final_score_can_be_survival_success(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="commuter_hustler", seed=7)
    controller.state = controller.state.model_copy(
        update={
            "current_day": controller.state.total_days + 1,
            "player": controller.state.player.model_copy(update={"cash": 400, "bank_balance": 120, "debt": 80, "gpa": 3.1}),
            "game_over_reason": None,
        }
    )
    summary = calculate_final_score(controller.state, quiet_bundle)
    assert summary.survived_term is True
