from __future__ import annotations

from collections.abc import Iterable

from budgetwars.models import ContentBundle


VALID_STAT_EFFECT_KEYS = {
    "cash",
    "savings",
    "debt",
    "stress",
    "energy",
    "life_satisfaction",
    "family_support",
    "promotion_progress",
    "education_progress",
}


def _ensure_unique_ids(records: Iterable[object], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        record_id = getattr(record, "id")
        if record_id in seen:
            duplicates.add(record_id)
        seen.add(record_id)
    if duplicates:
        raise ValueError(f"Duplicate {label} ids found: {', '.join(sorted(duplicates))}")


def _validate_effects(effects: dict[str, float], label: str) -> None:
    invalid = sorted(set(effects) - VALID_STAT_EFFECT_KEYS)
    if invalid:
        raise ValueError(f"{label} has invalid effect keys: {', '.join(invalid)}")


def validate_content_bundle(bundle: ContentBundle) -> None:
    _ensure_unique_ids(bundle.config.budget_stances, "budget stance")
    _ensure_unique_ids(bundle.config.opening_paths, "opening path")
    _ensure_unique_ids(bundle.difficulties, "difficulty")
    _ensure_unique_ids(bundle.cities, "city")
    _ensure_unique_ids(bundle.careers, "career")
    _ensure_unique_ids(bundle.education_programs, "education program")
    _ensure_unique_ids(bundle.housing_options, "housing")
    _ensure_unique_ids(bundle.transport_options, "transport")
    _ensure_unique_ids(bundle.focus_actions, "focus action")
    _ensure_unique_ids(bundle.events, "event")
    _ensure_unique_ids(bundle.presets, "preset")

    if bundle.config.primary_event_chance < bundle.config.secondary_event_chance:
        raise ValueError("primary_event_chance should be greater than or equal to secondary_event_chance")
    if bundle.config.minimum_parent_fallback_support > bundle.config.max_family_support:
        raise ValueError("minimum_parent_fallback_support cannot exceed max_family_support")

    career_ids = {career.id for career in bundle.careers}
    education_ids = {program.id for program in bundle.education_programs}
    housing_ids = {housing.id for housing in bundle.housing_options}
    transport_ids = {transport.id for transport in bundle.transport_options}
    city_ids = {city.id for city in bundle.cities}
    opening_path_ids = {path.id for path in bundle.config.opening_paths}
    budget_stance_ids = {stance.id for stance in bundle.config.budget_stances}
    focus_action_ids = {focus.id for focus in bundle.focus_actions}
    credential_ids = {program.credential_id for program in bundle.education_programs if program.credential_id}

    if sum(bundle.scoring_weights.model_dump().values()) != 1.0:
        raise ValueError("Scoring weights must sum exactly to 1.0")

    for city in bundle.cities:
        unknown_careers = sorted(set(city.career_income_biases) - career_ids)
        if unknown_careers:
            raise ValueError(f"City '{city.id}' references unknown careers: {', '.join(unknown_careers)}")

    for career in bundle.careers:
        unknown_paths = sorted(set(career.entry_path_ids) - opening_path_ids)
        if unknown_paths:
            raise ValueError(f"Career '{career.id}' references unknown opening paths: {', '.join(unknown_paths)}")
        unknown_credentials = sorted(set(career.entry_required_credential_ids) - credential_ids)
        if unknown_credentials:
            raise ValueError(f"Career '{career.id}' references unknown credentials: {', '.join(unknown_credentials)}")
        if career.entry_required_education_program_id and career.entry_required_education_program_id not in education_ids:
            raise ValueError(
                f"Career '{career.id}' references unknown education program '{career.entry_required_education_program_id}'"
            )
        if len(career.tiers) < 2:
            raise ValueError(f"Career '{career.id}' must define at least two tiers")
        for tier in career.tiers:
            unknown_tier_credentials = sorted(set(tier.required_credential_ids) - credential_ids)
            if unknown_tier_credentials:
                raise ValueError(
                    f"Career '{career.id}' tier '{tier.label}' references unknown credentials: "
                    f"{', '.join(unknown_tier_credentials)}"
                )

    for program in bundle.education_programs:
        unknown_paths = sorted(set(program.entry_path_ids) - opening_path_ids)
        if unknown_paths:
            raise ValueError(f"Education program '{program.id}' references unknown opening paths: {', '.join(unknown_paths)}")
        unknown_careers = sorted(set(program.applicable_career_ids) - career_ids)
        if unknown_careers:
            raise ValueError(
                f"Education program '{program.id}' references unknown careers: {', '.join(unknown_careers)}"
            )

    for housing in bundle.housing_options:
        if housing.requires_hometown and housing.id != "parents":
            raise ValueError("Only parents housing may require the hometown city in v1")

    for opening_path in bundle.config.opening_paths:
        if opening_path.starting_career_track_id not in career_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown career '{opening_path.starting_career_track_id}'"
            )
        if opening_path.starting_education_program_id not in education_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown education '{opening_path.starting_education_program_id}'"
            )
        if opening_path.starting_housing_id not in housing_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown housing '{opening_path.starting_housing_id}'"
            )
        if opening_path.starting_transport_id not in transport_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown transport '{opening_path.starting_transport_id}'"
            )
        if opening_path.starting_budget_stance_id not in budget_stance_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown budget stance '{opening_path.starting_budget_stance_id}'"
            )

    for event in bundle.events:
        _validate_effects(event.immediate_effects, f"Event '{event.id}'")
        if event.min_month > bundle.config.total_months:
            raise ValueError(f"Event '{event.id}' starts after the game ends")
        if sorted(set(event.eligible_city_ids) - city_ids):
            raise ValueError(f"Event '{event.id}' references unknown cities")
        if sorted(set(event.eligible_housing_ids) - housing_ids):
            raise ValueError(f"Event '{event.id}' references unknown housing ids")
        if sorted(set(event.eligible_transport_ids) - transport_ids):
            raise ValueError(f"Event '{event.id}' references unknown transport ids")
        if sorted(set(event.eligible_career_ids) - career_ids):
            raise ValueError(f"Event '{event.id}' references unknown career ids")
        if sorted(set(event.eligible_education_ids) - education_ids):
            raise ValueError(f"Event '{event.id}' references unknown education ids")
        if event.modifier:
            _validate_effects(event.modifier.stat_effects, f"Event modifier '{event.modifier.id}'")
            if event.modifier.duration_months > 12:
                raise ValueError(f"Event modifier '{event.modifier.id}' lasts too long for v1")

    for preset in bundle.presets:
        if preset.starting_energy > bundle.config.max_energy:
            raise ValueError(f"Preset '{preset.id}' starts with too much energy")
        if preset.starting_stress > bundle.config.max_stress:
            raise ValueError(f"Preset '{preset.id}' starts with too much stress")
        if preset.starting_life_satisfaction > bundle.config.max_life_satisfaction:
            raise ValueError(f"Preset '{preset.id}' starts with too much life satisfaction")
        if preset.starting_family_support > bundle.config.max_family_support:
            raise ValueError(f"Preset '{preset.id}' starts with too much family support")

    for focus_action in bundle.focus_actions:
        if focus_action.id not in focus_action_ids:
            raise ValueError("Invalid focus action configuration")
