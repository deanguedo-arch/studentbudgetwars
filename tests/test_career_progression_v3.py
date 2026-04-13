from __future__ import annotations


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
