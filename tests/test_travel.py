from __future__ import annotations


def test_travel_updates_location_resources_and_day(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="dorm_flipper", seed=18)
    starting_cash = controller.state.player.cash
    starting_energy = controller.state.player.energy
    controller.travel("main_campus")
    assert controller.state.player.current_district_id == "main_campus"
    assert controller.state.player.cash < starting_cash
    assert controller.state.player.energy < starting_energy
    assert controller.state.current_day == 2
    assert len(controller.state.current_markets) == len(quiet_bundle.districts)
