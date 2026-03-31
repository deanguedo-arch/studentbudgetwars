from __future__ import annotations

import pytest

from budgetwars.loaders import validate_content_bundle


def test_new_content_bundle_loads(bundle):
    assert len(bundle.commodities) >= 8
    assert len(bundle.districts) >= 8
    assert len(bundle.gigs) >= 6
    assert len(bundle.events) >= 10


def test_validator_rejects_duplicate_exam_weeks(bundle):
    invalid = bundle.model_copy(deep=True)
    invalid.exam_weeks.append(invalid.exam_weeks[0].model_copy())
    with pytest.raises(ValueError):
        validate_content_bundle(invalid)
