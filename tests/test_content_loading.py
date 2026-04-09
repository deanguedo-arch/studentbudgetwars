from __future__ import annotations

import pytest

from budgetwars.loaders import validate_content_bundle


def test_content_bundle_loads_expected_v2_sets(bundle):
    assert bundle.config.total_months == 120
    assert len(bundle.cities) == 3
    assert len(bundle.careers) == 8
    assert len(bundle.education_programs) == 6
    assert len(bundle.housing_options) == 4
    assert len(bundle.transport_options) == 8
    assert len(bundle.focus_actions) == 7
    assert len(bundle.wealth_strategies) == 4
    assert 24 <= len(bundle.events) <= 50
    assert len(bundle.learn_topics) >= 6
    assert bundle.consequence_matrix.transport_options
    assert bundle.consequence_matrix.credit_bands
    assert len(bundle.presets) == 7
    assert len(bundle.config.opening_paths) == 6
    assert len(bundle.config.budget_stances) == 4


def test_learn_topics_load_with_required_sections(bundle):
    topic_ids = {topic.id for topic in bundle.learn_topics}
    assert {"credit", "stress", "housing", "transport", "career", "education"} <= topic_ids

    stress_topic = next(topic for topic in bundle.learn_topics if topic.id == "stress")
    assert stress_topic.what_it_is
    assert stress_topic.how_to_raise
    assert stress_topic.how_to_lower
    assert stress_topic.why_it_matters


def test_invalid_city_career_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.cities[0].career_income_biases["missing_track"] = 1.2
    with pytest.raises(ValueError, match="unknown careers"):
        validate_content_bundle(broken)


def test_invalid_event_opening_path_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].eligible_opening_path_ids.append("missing_path")
    with pytest.raises(ValueError, match="opening paths"):
        validate_content_bundle(broken)


def test_invalid_event_branch_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].eligible_branch_ids.append("missing_branch")
    with pytest.raises(ValueError, match="branch ids"):
        validate_content_bundle(broken)


def test_invalid_event_wealth_strategy_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].eligible_wealth_strategy_ids.append("missing_strategy")
    with pytest.raises(ValueError, match="wealth strategies"):
        validate_content_bundle(broken)


def test_invalid_event_modifier_duration_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].modifier.duration_months = 13
    with pytest.raises(ValueError, match="lasts too long"):
        validate_content_bundle(broken)


def test_invalid_market_regime_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].eligible_market_regime_ids = ["missing_regime"]
    with pytest.raises(ValueError, match="market regimes"):
        validate_content_bundle(broken)


def test_invalid_budget_allocation_total_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.config.budget_stances[0].safe_savings_rate = 0.7
    broken.config.budget_stances[0].index_invest_rate = 0.4
    with pytest.raises(ValueError, match="allocates more than 100%"):
        validate_content_bundle(broken)


def test_invalid_event_modifier_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.events[0].eligible_modifier_ids = ["missing_modifier"]
    with pytest.raises(ValueError, match="modifier ids"):
        validate_content_bundle(broken)


def test_invalid_consequence_matrix_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.consequence_matrix.transport_options["missing_transport"] = (
        broken.consequence_matrix.transport_options["none"].model_copy(deep=True)
    )
    with pytest.raises(ValueError, match="unknown transport option"):
        validate_content_bundle(broken)
