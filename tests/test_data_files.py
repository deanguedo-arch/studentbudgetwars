from budgetwars.loaders import load_all_content
from budgetwars.validators import validate_content_bundle


def test_data_files_load_and_validate() -> None:
    bundle = load_all_content()
    validate_content_bundle(bundle)

    assert bundle.config.game_title
    assert bundle.items
    assert bundle.expenses
    assert bundle.jobs
    assert bundle.locations
    assert bundle.events
    assert bundle.presets
