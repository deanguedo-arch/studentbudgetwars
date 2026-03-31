from __future__ import annotations

from collections.abc import Iterable

from .models import ContentBundle


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

    for event in bundle.events:
        _ensure_unique_ids(event.choices, f"event choice for {event.id}")

    for job in bundle.jobs:
        if job.location_id not in location_ids:
            raise ValueError(f"Job '{job.id}' references unknown location '{job.location_id}'")

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
