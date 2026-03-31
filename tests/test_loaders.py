from budgetwars.loaders import (
    load_config,
    load_events,
    load_expenses,
    load_items,
    load_jobs,
    load_locations,
    load_presets,
    load_scoring,
)


def test_individual_loaders_parse_expected_shapes() -> None:
    config = load_config()
    assert config.term_weeks > 0
    assert config.difficulties
    assert len(load_items()) >= 10
    assert len(load_expenses()) >= 7
    assert len(load_jobs()) >= 5
    assert len(load_locations()) >= 5
    events = load_events()
    assert len(events) >= 15
    assert events[0].choices
    assert len(load_presets()) >= 3
    assert load_scoring().survival_bonus >= 0
