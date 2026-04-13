from __future__ import annotations

import pytest

from budgetwars.engine.careers import add_promotion_progress, current_income, maybe_promote
from budgetwars.engine.events import eligible_events, event_weight
from budgetwars.engine.lookups import get_career_track
from budgetwars.engine.scoring import build_live_score_snapshot


ALL_CAREER_IDS = [
    "retail_service",
    "warehouse_logistics",
    "delivery_gig",
    "office_admin",
    "trades_apprenticeship",
    "healthcare_support",
    "sales",
    "degree_gated_professional",
]


def _seed_track_state(bundle, controller, track_id: str, *, max_tier: bool = False) -> None:
    state = controller.state
    track = get_career_track(bundle, track_id)
    state.player.career.track_id = track_id
    state.player.career.branch_id = track.branches[0].id if track.branches else None
    state.player.career.tier_index = len(track.tiers) - 1 if max_tier else 0
    state.player.career.promotion_progress = 0
    state.player.career.promotion_momentum = 74
    state.player.career.recent_performance_tag = "uptrend"
    state.player.career.months_at_tier = 6 if max_tier else 0
    state.player.energy = 72
    state.player.stress = 26
    state.player.social_stability = 72
    state.player.housing.housing_stability = 72
    state.player.transport.reliability_score = 78
    state.player.education.college_gpa = 3.4
    state.player.education.training_passed = True
    credentials = []
    if track_id == "trades_apprenticeship":
        credentials = ["apprenticeship_certificate"]
    elif track_id == "healthcare_support":
        credentials = ["support_certificate"]
    elif track_id == "degree_gated_professional":
        credentials = ["university_degree"]
    state.player.education.earned_credential_ids = credentials


def _top_weighted_event_ids(bundle, state, *, limit: int = 8) -> list[str]:
    scored = sorted(
        ((event_weight(bundle, state, event), event.id) for event in eligible_events(bundle, state)),
        reverse=True,
    )
    return [event_id for _weight, event_id in scored[:limit]]


def test_all_careers_have_three_branches(bundle):
    branches_by_track = {track.id: [branch.id for branch in track.branches] for track in bundle.careers}

    assert len(branches_by_track["retail_service"]) >= 3
    assert len(branches_by_track["warehouse_logistics"]) >= 3
    assert len(branches_by_track["office_admin"]) >= 3
    assert branches_by_track["delivery_gig"] == [
        "delivery_route_grind_track",
        "delivery_platform_optimizer_track",
        "delivery_independent_operator_track",
    ]
    assert branches_by_track["trades_apprenticeship"] == [
        "trades_field_crew_track",
        "trades_precision_specialist_track",
        "trades_estimator_supervisor_track",
    ]
    assert branches_by_track["healthcare_support"] == [
        "healthcare_floor_care_track",
        "healthcare_technical_support_track",
        "healthcare_scheduling_coordination_track",
    ]
    assert branches_by_track["sales"] == [
        "sales_volume_closer_track",
        "sales_account_manager_track",
        "sales_enterprise_strategy_track",
    ]
    assert branches_by_track["degree_gated_professional"] == [
        "professional_technical_specialist_track",
        "professional_client_lead_track",
        "professional_people_ops_track",
    ]


def test_all_careers_have_deeper_promotion_targets(bundle):
    for track in bundle.careers:
        targets = [tier.promotion_target for tier in track.tiers]
        assert targets == sorted(targets)
        assert targets[0] >= 7
        assert targets[-1] >= 24


@pytest.mark.parametrize("track_id", ALL_CAREER_IDS)
def test_routine_promotion_progress_is_tempered_across_all_careers(bundle, controller_factory, track_id):
    controller = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, controller, track_id, max_tier=False)

    add_promotion_progress(bundle, controller.state, 1)

    assert controller.state.player.career.promotion_progress <= 4


@pytest.mark.parametrize("track_id", ALL_CAREER_IDS)
def test_max_tier_progress_converts_into_role_band_instead_of_dead_end(bundle, controller_factory, track_id):
    controller = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, controller, track_id, max_tier=True)
    track = get_career_track(bundle, track_id)
    controller.state.player.persistent_tags = ["scope_push_lane"]
    controller.state.player.career.promotion_progress = track.tiers[-1].promotion_target

    maybe_promote(bundle, controller.state)

    assert controller.state.player.career.role_band_id == "stretch_scope_band"
    assert controller.state.player.career.post_cap_advancement_level == 1


@pytest.mark.parametrize("track_id", ALL_CAREER_IDS)
def test_post_cap_role_bands_create_distinct_income_profiles(bundle, controller_factory, track_id):
    stretch = controller_factory(opening_path_id="full_time_work")
    stable = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, stretch, track_id, max_tier=True)
    _seed_track_state(bundle, stable, track_id, max_tier=True)
    track = get_career_track(bundle, track_id)

    stretch.state.player.persistent_tags = ["scope_push_lane"]
    stable.state.player.persistent_tags = ["consistency_lane"]
    stretch.state.player.career.promotion_progress = track.tiers[-1].promotion_target
    stable.state.player.career.promotion_progress = track.tiers[-1].promotion_target

    maybe_promote(bundle, stretch.state)
    maybe_promote(bundle, stable.state)

    stretch_income = current_income(bundle, stretch.state, 1.0)
    stable_income = current_income(bundle, stable.state, 1.0)

    assert stretch.state.player.career.role_band_id == "stretch_scope_band"
    assert stable.state.player.career.role_band_id == "stability_anchor_band"
    assert stretch_income > stable_income


def test_all_career_branches_have_branch_specific_events(bundle):
    branch_event_map = {
        branch.id: {event.id for event in bundle.events if branch.id in event.eligible_branch_ids}
        for track in bundle.careers
        for branch in track.branches
    }

    assert all(branch_event_map.values())


def test_all_careers_have_persistent_tag_followup_events(bundle):
    track_tag_events = {
        track.id: {
            event.id
            for event in bundle.events
            if track.id in event.eligible_career_ids and event.eligible_persistent_tags
        }
        for track in bundle.careers
    }

    assert all(track_tag_events.values())


@pytest.mark.parametrize(
    ("track_id", "branch_a", "branch_b", "expected_a", "expected_b"),
    [
        (
            "delivery_gig",
            "delivery_route_grind_track",
            "delivery_independent_operator_track",
            "delivery_route_crush_week",
            "delivery_operator_contract_bid",
        ),
        (
            "trades_apprenticeship",
            "trades_field_crew_track",
            "trades_precision_specialist_track",
            "trades_field_crew_weather_crunch",
            "trades_precision_quote_window",
        ),
        (
            "healthcare_support",
            "healthcare_floor_care_track",
            "healthcare_scheduling_coordination_track",
            "healthcare_floor_care_double_shift",
            "healthcare_schedule_gap_cascade",
        ),
        (
            "sales",
            "sales_volume_closer_track",
            "sales_account_manager_track",
            "sales_volume_sprint_window",
            "sales_renewal_book_window",
        ),
        (
            "degree_gated_professional",
            "professional_technical_specialist_track",
            "professional_client_lead_track",
            "professional_deep_work_breakthrough",
            "professional_stakeholder_pitch_cycle",
        ),
    ],
)
def test_new_career_families_have_branch_specific_event_pool_contrast(
    bundle,
    controller_factory,
    track_id,
    branch_a,
    branch_b,
    expected_a,
    expected_b,
):
    controller_a = controller_factory(opening_path_id="full_time_work")
    controller_b = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, controller_a, track_id, max_tier=False)
    _seed_track_state(bundle, controller_b, track_id, max_tier=False)
    controller_a.state.current_month = 24
    controller_b.state.current_month = 24
    controller_a.state.player.career.tier_index = 2
    controller_b.state.player.career.tier_index = 2
    controller_a.state.player.career.branch_id = branch_a
    controller_b.state.player.career.branch_id = branch_b

    top_a = _top_weighted_event_ids(bundle, controller_a.state)
    top_b = _top_weighted_event_ids(bundle, controller_b.state)

    assert expected_a in top_a
    assert expected_b in top_b
    assert set(top_a) != set(top_b)


@pytest.mark.parametrize("track_id", ALL_CAREER_IDS)
def test_late_career_role_band_improves_live_score_signal(bundle, controller_factory, track_id):
    flat = controller_factory(opening_path_id="full_time_work")
    banded = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, flat, track_id, max_tier=True)
    _seed_track_state(bundle, banded, track_id, max_tier=True)

    banded.state.player.career.role_band_id = "stretch_scope_band"
    banded.state.player.career.post_cap_advancement_level = 2

    flat_snapshot = build_live_score_snapshot(bundle, flat.state)
    banded_snapshot = build_live_score_snapshot(bundle, banded.state)

    assert banded_snapshot.projected_score > flat_snapshot.projected_score


@pytest.mark.parametrize(
    ("track_id", "branch_id", "tag", "expected_event_id"),
    [
        (
            "delivery_gig",
            "delivery_platform_optimizer_track",
            "delivery_margin_control_lane",
            "delivery_margin_discipline_compound",
        ),
        (
            "sales",
            "sales_account_manager_track",
            "sales_book_builder_lane",
            "sales_book_compound_window",
        ),
        (
            "degree_gated_professional",
            "professional_technical_specialist_track",
            "professional_specialist_lane",
            "professional_specialist_reputation_dividend",
        ),
    ],
)
def test_new_career_commitment_tags_open_followup_event_pools(
    bundle,
    controller_factory,
    track_id,
    branch_id,
    tag,
    expected_event_id,
):
    controller = controller_factory(opening_path_id="full_time_work")
    _seed_track_state(bundle, controller, track_id, max_tier=False)
    controller.state.current_month = 26
    controller.state.player.career.tier_index = 2
    controller.state.player.career.branch_id = branch_id
    controller.state.player.persistent_tags = [tag]

    top_ids = _top_weighted_event_ids(bundle, controller.state)

    assert expected_event_id in top_ids
