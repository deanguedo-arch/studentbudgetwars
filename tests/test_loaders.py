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
    assert len(load_items()) >= 1
    assert len(load_expenses()) >= 1
    assert len(load_jobs()) >= 1
    assert len(load_locations()) >= 1
    events = load_events()
    assert len(events) >= 1
    assert events[0].choices
    assert len(load_presets()) >= 1
    assert load_scoring().survival_bonus >= 0
