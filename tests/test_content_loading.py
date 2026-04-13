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
    assert 100 <= len(bundle.events) <= 140
    assert len(bundle.learn_topics) >= 6
    assert bundle.consequence_matrix.transport_options
    assert bundle.consequence_matrix.credit_bands
    assert len(bundle.presets) == 7
    assert len(bundle.config.opening_paths) == 6
    assert len(bundle.config.budget_stances) == 4
    assert len(bundle.status_arcs) >= 3


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


def test_status_arc_content_loads_expected_proof_arcs(bundle):
    arc_ids = {arc.id for arc in bundle.status_arcs}
    assert {"transport_unstable", "credit_squeeze", "education_slipping"} <= arc_ids


def test_status_arc_content_loads_expected_wave_2_arcs(bundle):
    arc_ids = {arc.id for arc in bundle.status_arcs}
    assert {"lease_pressure", "burnout_risk", "promotion_window_open"} <= arc_ids

    arcs = {arc.id: arc for arc in bundle.status_arcs}
    assert arcs["lease_pressure"].followup_event_ids
    assert arcs["lease_pressure"].resolution_hint
    assert arcs["burnout_risk"].followup_event_ids
    assert arcs["burnout_risk"].resolution_hint
    assert arcs["promotion_window_open"].followup_event_ids
    assert arcs["promotion_window_open"].resolution_hint


def test_invalid_status_arc_modifier_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.status_arcs[0].linked_modifier_ids.append("missing_modifier")
    with pytest.raises(ValueError, match="status arc.*modifier ids"):
        validate_content_bundle(broken)


def test_invalid_status_arc_followup_reference_fails_validation(bundle):
    broken = bundle.model_copy(deep=True)
    broken.status_arcs[0].followup_event_ids.append("missing_event")
    with pytest.raises(ValueError, match="status arc.*follow-up event ids"):
        validate_content_bundle(broken)


def test_new_game_initializes_empty_active_status_arcs(controller_factory):
    controller = controller_factory()
    assert controller.state.active_status_arcs == []


def test_all_careers_exist_and_keep_five_tiers(bundle):
    track_ids = {track.id for track in bundle.careers}
    assert track_ids == {
        "retail_service",
        "warehouse_logistics",
        "delivery_gig",
        "office_admin",
        "trades_apprenticeship",
        "healthcare_support",
        "sales",
        "degree_gated_professional",
    }
    assert all(len(track.tiers) == 5 for track in bundle.careers)
