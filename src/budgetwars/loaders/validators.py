from __future__ import annotations

from collections.abc import Iterable
from math import isclose

from budgetwars.models import ContentBundle


VALID_STAT_EFFECT_KEYS = {
    "cash",
    "savings",
    "high_interest_savings",
    "index_fund",
    "aggressive_growth_fund",
    "debt",
    "stress",
    "energy",
    "life_satisfaction",
    "family_support",
    "social_stability",
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
    _ensure_unique_ids(bundle.config.academic_levels, "academic level")
    _ensure_unique_ids(bundle.config.family_support_levels, "family support level")
    _ensure_unique_ids(bundle.config.savings_bands, "savings band")
    _ensure_unique_ids(bundle.config.market_regimes, "market regime")
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
    if bundle.config.crisis_warning_housing_streak > bundle.config.housing_miss_limit:
        raise ValueError("crisis_warning_housing_streak cannot exceed housing_miss_limit")
    if not any(regime.id == bundle.config.default_market_regime_id for regime in bundle.config.market_regimes):
        raise ValueError("default_market_regime_id must exist in market_regimes")

    career_ids = {career.id for career in bundle.careers}
    education_ids = {program.id for program in bundle.education_programs}
    housing_ids = {housing.id for housing in bundle.housing_options}
    transport_ids = {transport.id for transport in bundle.transport_options}
    city_ids = {city.id for city in bundle.cities}
    opening_path_ids = {path.id for path in bundle.config.opening_paths}
    budget_stance_ids = {stance.id for stance in bundle.config.budget_stances}
    focus_action_ids = {focus.id for focus in bundle.focus_actions}
    credential_ids = {program.credential_id for program in bundle.education_programs if program.credential_id}

    if not isclose(sum(bundle.scoring_weights.model_dump().values()), 1.0, abs_tol=1e-9):
        raise ValueError("Scoring weights must sum to 1.0")

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
        if career.stability_profile + career.volatility_profile < 70:
            raise ValueError(f"Career '{career.id}' must have meaningful stability/volatility identity")
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
        if program.uses_gpa and program.pass_state_program:
            raise ValueError(f"Education program '{program.id}' cannot use GPA and pass-state simultaneously")

    for housing in bundle.housing_options:
        if housing.requires_hometown and housing.id != "parents":
            raise ValueError("Only parents housing may require the hometown city in this version")
        if housing.student_only and housing.id != "student_residence":
            raise ValueError("Only student_residence may be student-only in this version")

    for transport in bundle.transport_options:
        if transport.breakdown_risk > transport.repair_event_weight + 0.4:
            raise ValueError(f"Transport '{transport.id}' has a breakdown risk too large for its event weight")

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
        if opening_path.starting_focus_action_id not in focus_action_ids:
            raise ValueError(
                f"Opening path '{opening_path.id}' references unknown focus action '{opening_path.starting_focus_action_id}'"
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
        if sorted(set(event.eligible_opening_path_ids) - opening_path_ids):
            raise ValueError(f"Event '{event.id}' references unknown opening paths")
        if event.eligible_market_regime_ids:
            valid_regime_ids = {regime.id for regime in bundle.config.market_regimes}
            if sorted(set(event.eligible_market_regime_ids) - valid_regime_ids):
                raise ValueError(f"Event '{event.id}' references unknown market regimes")
        if event.modifier:
            _validate_effects(event.modifier.stat_effects, f"Event modifier '{event.modifier.id}'")
            if event.modifier.duration_months > 12:
                raise ValueError(f"Event modifier '{event.modifier.id}' lasts too long for this version")

    for stance in bundle.config.budget_stances:
        allocation_total = (
            stance.savings_contribution_rate
            + stance.safe_savings_rate
            + stance.index_invest_rate
            + stance.growth_invest_rate
            + stance.extra_debt_payment_rate
        )
        if allocation_total > 1.0:
            raise ValueError(f"Budget stance '{stance.id}' allocates more than 100% of available cash")

    for preset in bundle.presets:
        if preset.starting_energy > bundle.config.max_energy:
            raise ValueError(f"Preset '{preset.id}' starts with too much energy")
        if preset.starting_stress > bundle.config.max_stress:
            raise ValueError(f"Preset '{preset.id}' starts with too much stress")
        if preset.starting_life_satisfaction > bundle.config.max_life_satisfaction:
            raise ValueError(f"Preset '{preset.id}' starts with too much life satisfaction")
        if preset.starting_family_support > bundle.config.max_family_support:
            raise ValueError(f"Preset '{preset.id}' starts with too much family support")
        if preset.starting_social_stability > bundle.config.max_social_stability:
            raise ValueError(f"Preset '{preset.id}' starts with too much social stability")
