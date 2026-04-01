from __future__ import annotations

import pytest

from budgetwars.loaders import validate_content_bundle


def test_content_bundle_loads_expected_v1_sets(bundle):
    assert bundle.config.total_months == 120
    assert len(bundle.cities) == 3
    assert len(bundle.careers) == 4
    assert len(bundle.education_programs) == 3
    assert len(bundle.housing_options) == 3
    assert len(bundle.transport_options) == 4
    assert len(bundle.focus_actions) == 3
    assert 6 <= len(bundle.events) <= 10
    assert len(bundle.presets) == 4


def test_invalid_city_career_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.cities[0].career_income_biases["missing_track"] = 1.2
    with pytest.raises(ValueError, match="unknown careers"):
        validate_content_bundle(broken)


def test_invalid_event_modifier_duration_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].modifier.duration_months = 13
    with pytest.raises(ValueError, match="lasts too long"):
        validate_content_bundle(broken)
