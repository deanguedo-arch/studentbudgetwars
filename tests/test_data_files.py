from budgetwars.loaders import load_all_content
from budgetwars.validators import validate_content_bundle


def test_data_files_load_and_validate() -> None:
    bundle = load_all_content()
    validate_content_bundle(bundle)

    assert bundle.config.game_title
    assert len(bundle.items) >= 10
    assert len(bundle.expenses) >= 7
    assert len(bundle.jobs) >= 5
    assert len(bundle.locations) >= 5
    assert len(bundle.events) >= 15
    assert len(bundle.presets) >= 3
