from __future__ import annotations

from budgetwars.saves import load_game, save_game


def test_save_round_trip_preserves_state(quiet_bundle, controller_factory, tmp_path):
    controller = controller_factory(quiet_bundle, preset_id="dorm_flipper", seed=17)
    controller.rest()
    save_path = tmp_path / "city_hustle_save.json"
    save_game(controller.state, save_path)
    loaded = load_game(save_path)
    assert loaded == controller.state
