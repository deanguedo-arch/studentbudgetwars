from __future__ import annotations

from budgetwars.saves import load_game, save_game


def test_save_load_round_trip(tmp_path, controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    controller.change_focus_action("recovery_month")
    controller.change_wealth_strategy("steady_builder")
    controller.resolve_month()
    save_path = tmp_path / "after_grad_save.json"
    save_game(controller.state, save_path)
    loaded = load_game(save_path)
    assert loaded.current_month == controller.state.current_month
    assert loaded.player.career.track_id == controller.state.player.career.track_id
    assert loaded.player.education.program_id == controller.state.player.education.program_id
    assert loaded.player.selected_focus_action_id == "recovery_month"
    assert loaded.player.wealth_strategy_id == "steady_builder"
    assert loaded.player.housing.option_id == controller.state.player.housing.option_id
