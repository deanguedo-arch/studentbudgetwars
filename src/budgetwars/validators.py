from __future__ import annotations

from collections.abc import Iterable

from .models import ContentBundle

VALID_EFFECT_KEYS = {"cash", "savings", "debt", "stress", "energy"}


def _ensure_unique_ids(records: Iterable[object], label: str) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for record in records:
        record_id = getattr(record, "id")
        if record_id in seen:
            duplicates.add(record_id)
        seen.add(record_id)
    if duplicates:
        joined = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate {label} ids found: {joined}")


def _validate_effect_mapping(effects: dict[str, int], label: str) -> None:
    invalid_keys = sorted(set(effects) - VALID_EFFECT_KEYS)
    if invalid_keys:
        joined = ", ".join(invalid_keys)
        raise ValueError(f"{label} has invalid effect keys: {joined}")


def _validate_range(value: float, minimum: float, maximum: float, label: str) -> None:
    if not minimum <= value <= maximum:
        raise ValueError(f"{label} must be between {minimum} and {maximum}")


def validate_content_bundle(bundle: ContentBundle) -> None:
    _ensure_unique_ids(bundle.items, "item")
    _ensure_unique_ids(bundle.expenses, "expense")
    _ensure_unique_ids(bundle.jobs, "job")
    _ensure_unique_ids(bundle.locations, "location")
    _ensure_unique_ids(bundle.events, "event")
    _ensure_unique_ids(bundle.presets, "preset")
    _ensure_unique_ids(bundle.config.difficulties, "difficulty")

    location_ids = {location.id for location in bundle.locations}
    job_ids = {job.id for job in bundle.jobs}

    if not bundle.config.difficulties:
        raise ValueError("config.difficulties must include at least one difficulty")

    if bundle.config.starting_location_id not in location_ids:
        raise ValueError("config.starting_location_id must reference a known location")
    if bundle.config.starting_week > bundle.config.term_weeks:
        raise ValueError("config.starting_week cannot be greater than config.term_weeks")
    if bundle.config.low_energy_threshold >= bundle.config.max_energy:
        raise ValueError("config.low_energy_threshold must be below config.max_energy")

    for event in bundle.events:
        _ensure_unique_ids(event.choices, f"event choice for {event.id}")
        _validate_effect_mapping(event.effects, f"Event '{event.id}'")
        if not event.choices:
            raise ValueError(f"Event '{event.id}' must include at least one choice")
        if event.weight > 100:
            raise ValueError(f"Event '{event.id}' weight is implausibly high")
        for choice in event.choices:
            _validate_effect_mapping(choice.effects, f"Event '{event.id}' choice '{choice.id}'")

    for item in bundle.items:
        _validate_effect_mapping(item.effects, f"Item '{item.id}'")
        if item.price > 200:
            raise ValueError(f"Item '{item.id}' price is implausibly high")

    for location in bundle.locations:
        _validate_effect_mapping(location.modifiers, f"Location '{location.id}'")

    for expense in bundle.expenses:
        if expense.amount > 500:
            raise ValueError(f"Expense '{expense.id}' amount is implausibly high")

    for job in bundle.jobs:
        if job.location_id not in location_ids:
            raise ValueError(f"Job '{job.id}' references unknown location '{job.location_id}'")
        if job.hourly_pay > 50:
            raise ValueError(f"Job '{job.id}' hourly_pay is implausibly high")
        if job.hours_per_week > 40:
            raise ValueError(f"Job '{job.id}' hours_per_week is implausibly high")
        if job.energy_cost > bundle.config.max_energy:
            raise ValueError(f"Job '{job.id}' energy_cost exceeds config.max_energy")

    for difficulty in bundle.config.difficulties:
        _validate_range(difficulty.income_multiplier, 0.5, 1.5, f"Difficulty '{difficulty.id}' income_multiplier")
        _validate_range(
            difficulty.expense_multiplier,
            0.5,
            1.5,
            f"Difficulty '{difficulty.id}' expense_multiplier",
        )
        _validate_range(difficulty.stress_multiplier, 0.5, 1.5, f"Difficulty '{difficulty.id}' stress_multiplier")
        if abs(difficulty.starting_cash_bonus) > 150:
            raise ValueError(f"Difficulty '{difficulty.id}' starting_cash_bonus is implausibly large")

    for preset in bundle.presets:
        if preset.starting_location_id not in location_ids:
            raise ValueError(
                f"Preset '{preset.id}' references unknown location '{preset.starting_location_id}'"
            )
        if preset.starting_job_id not in job_ids:
            raise ValueError(
                f"Preset '{preset.id}' references unknown job '{preset.starting_job_id}'"
            )

        if preset.starting_stress > bundle.config.max_stress:
            raise ValueError(f"Preset '{preset.id}' exceeds config.max_stress")
        if preset.starting_energy > bundle.config.max_energy:
            raise ValueError(f"Preset '{preset.id}' exceeds config.max_energy")
        if preset.starting_debt >= bundle.config.debt_game_over_threshold:
            raise ValueError(f"Preset '{preset.id}' starts at or above the debt game-over threshold")
