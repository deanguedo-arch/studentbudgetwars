from __future__ import annotations


def test_available_gigs_respect_requirements(quiet_bundle, controller_factory):
    scholarship = controller_factory(quiet_bundle, preset_id="scholarship_grinder", seed=55)
    gigs = {gig.id for gig in scholarship.available_gigs()}
    assert "library_shift" in gigs
    assert "tutor_intro_stats" in gigs

    hustler = controller_factory(quiet_bundle, preset_id="dorm_flipper", seed=55)
    dorm_gigs = {gig.id for gig in hustler.available_gigs()}
    assert dorm_gigs == {"move_out_haul"}


def test_working_a_gig_changes_state(quiet_bundle, controller_factory):
    controller = controller_factory(quiet_bundle, preset_id="scholarship_grinder", seed=64)
    starting_cash = controller.state.player.cash
    starting_energy = controller.state.player.energy
    controller.work_gig("library_shift")
    assert controller.state.player.cash > starting_cash
    assert controller.state.player.energy < starting_energy
    assert controller.state.current_day == 2
