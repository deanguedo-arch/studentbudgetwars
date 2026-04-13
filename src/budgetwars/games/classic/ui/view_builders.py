from __future__ import annotations

from dataclasses import dataclass


_PERSISTENT_TAG_LABELS = {
    "scope_push_lane": "Scope Push Lane",
    "consistency_lane": "Consistency Lane",
    "retail_management_command_lane": "Retail Command Lane",
    "retail_management_stability_lane": "Retail Stability Lane",
    "dispatch_command_lane": "Dispatch Command Lane",
    "dispatch_coordination_lane": "Dispatch Coordination Lane",
    "office_scope_lane": "Office Scope Lane",
    "office_consistency_lane": "Office Consistency Lane",
    "healthcare_triage_command_lane": "Healthcare Triage Command Lane",
    "healthcare_continuity_lane": "Healthcare Continuity Lane",
    "trades_emergency_rotation_lane": "Trades Emergency Rotation Lane",
    "trades_precision_schedule_lane": "Trades Precision Schedule Lane",
}


def _format_persistent_commitments(tags: list[str]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        label = _PERSISTENT_TAG_LABELS.get(tag, tag.replace("_", " ").title())
        if label in seen:
            continue
        seen.add(label)
        labels.append(label)
    return labels


@dataclass(frozen=True)
class _Context:
    state: object
    bundle: object


def _resolve_context(source, bundle=None) -> _Context:
    if bundle is None and hasattr(source, "state") and hasattr(source, "bundle"):
        return _Context(state=source.state, bundle=source.bundle)
    if bundle is not None:
        return _Context(state=source, bundle=bundle)
    raise TypeError("Expected a controller or a (state, bundle) pair.")


def _find_label(options: list, value_id: str, default: str = "") -> str:
    for option in options:
        if option.id == value_id:
            return option.name
    return default


def _current_focus_name(controller) -> str:
    player = controller.state.player
    return _find_label(controller.bundle.focus_actions, player.selected_focus_action_id, "Focus")


def _current_focus_description(controller) -> str:
    player = controller.state.player
    for option in controller.bundle.focus_actions:
        if option.id == player.selected_focus_action_id:
            return option.description
    return "Choose a monthly focus."


def _current_career_tier_label(controller) -> str:
    state = controller.state
    track = next(track for track in controller.bundle.careers if track.id == state.player.career.track_id)
    return track.tiers[state.player.career.tier_index].label


def _current_career_track_name(controller) -> str:
    state = controller.state
    track = next(track for track in controller.bundle.careers if track.id == state.player.career.track_id)
    return track.name


def _current_city(controller) -> str:
    city = next(item for item in controller.bundle.cities if item.id == controller.state.player.current_city_id)
    return city.name
