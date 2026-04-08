from __future__ import annotations

from budgetwars.games.classic.ui.main_window import (
    build_build_snapshot,
    build_monthly_forecast,
    build_pressure_summary,
    build_score_delta_summary,
)
from budgetwars.models import LiveScoreSnapshot


def test_build_snapshot_returns_structured_items(controller_factory):
    controller = controller_factory()

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert snapshot.player_name == controller.state.player.name
    assert snapshot.city_name
    assert [item.label for item in snapshot.items] == [
        "Career",
        "Education",
        "Housing",
        "Transport",
        "Budget",
        "Wealth",
        "Focus",
    ]
    assert snapshot.items[0].value
    assert snapshot.items[0].detail is not None
    assert not isinstance(snapshot.items[0], str)


def test_monthly_forecast_exposes_named_sections(controller_factory):
    controller = controller_factory()

    forecast = build_monthly_forecast(controller.state, controller.bundle)

    assert forecast.monthly_focus
    assert forecast.main_threat
    assert forecast.best_opportunity
    assert forecast.chosen_focus
    assert forecast.expected_swing
    assert isinstance(forecast.driver_notes, list)


def test_pressure_summary_prioritizes_key_metrics(controller_factory):
    controller = controller_factory()

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert summary.projected_score >= 0
    assert summary.score_tier
    assert summary.biggest_risk
    assert [metric.label for metric in summary.primary_metrics][:3] == [
        "Cash",
        "Savings",
        "Debt",
    ]
    assert summary.active_modifiers is not None
    assert summary.crisis_watch is not None


def test_score_delta_summary_compares_current_and_previous_snapshots():
    previous = LiveScoreSnapshot(
        projected_score=45.0,
        score_tier="Silver",
        biggest_risk="Debt pressure is still the softest part of the run.",
        breakdown={
            "net_worth": 38.0,
            "monthly_surplus": 62.0,
            "debt_ratio": 41.0,
            "career_tier": 55.0,
            "credentials_education": 49.0,
            "housing_stability": 58.0,
            "life_satisfaction": 44.0,
            "stress_burnout": 36.0,
        },
    )
    current = LiveScoreSnapshot(
        projected_score=52.5,
        score_tier="Silver",
        biggest_risk="Debt pressure is still the softest part of the run.",
        breakdown={
            "net_worth": 42.0,
            "monthly_surplus": 66.0,
            "debt_ratio": 48.0,
            "career_tier": 57.0,
            "credentials_education": 50.0,
            "housing_stability": 60.0,
            "life_satisfaction": 47.0,
            "stress_burnout": 39.0,
        },
    )

    delta = build_score_delta_summary(previous, current)

    assert delta.previous_score == 45.0
    assert delta.current_score == 52.5
    assert delta.delta == 7.5
    assert delta.strongest_category
    assert delta.weakest_category
    assert delta.diagnosis
