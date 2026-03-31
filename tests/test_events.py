from __future__ import annotations

from budgetwars.engine.events import activate_event, prune_expired_events
from budgetwars.engine.lookups import get_event


def test_activate_event_sets_expiry_and_applies_effects(bundle, controller_factory):
    controller = controller_factory(bundle, seed=14)
    event = get_event(bundle, "sold_out_show")
    starting_heat = controller.state.player.heat
    updated = activate_event(controller.state, bundle, event, controller.state.current_day)
    assert updated.player.heat > starting_heat
    assert any(active.event_id == "sold_out_show" for active in updated.active_events)
    active = next(active for active in updated.active_events if active.event_id == "sold_out_show")
    assert active.expires_on_day == controller.state.current_day + 6


def test_one_day_event_lasts_through_next_day(bundle, controller_factory):
    controller = controller_factory(bundle, seed=33)
    event = get_event(bundle, "found_source_lead")
    cleared = controller.state.model_copy(update={"active_events": []})
    updated = activate_event(cleared, bundle, event, controller.state.current_day + 1)
    day_two = updated.model_copy(update={"current_day": 2})
    assert prune_expired_events(day_two).active_events
    day_three = updated.model_copy(update={"current_day": 3})
    assert not prune_expired_events(day_three).active_events
