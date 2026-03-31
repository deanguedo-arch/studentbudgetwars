import pytest

from budgetwars.loaders import load_all_content
from budgetwars.validators import validate_content_bundle


def test_validator_rejects_invalid_effect_keys() -> None:
    bundle = load_all_content()
    invalid_item = bundle.items[0].model_copy(update={"effects": {"luck": 5}})
    invalid_bundle = bundle.model_copy(update={"items": [invalid_item, *bundle.items[1:]]})

    with pytest.raises(ValueError, match="invalid effect keys"):
        validate_content_bundle(invalid_bundle)


def test_validator_rejects_duplicate_event_choice_ids() -> None:
    bundle = load_all_content()
    event = bundle.events[0]
    duplicate_choices = [
        event.choices[0],
        event.choices[0].model_copy(update={"label": "Duplicate label"}),
    ]
    invalid_event = event.model_copy(update={"choices": duplicate_choices})
    invalid_bundle = bundle.model_copy(update={"events": [invalid_event, *bundle.events[1:]]})

    with pytest.raises(ValueError, match="Duplicate event choice"):
        validate_content_bundle(invalid_bundle)
