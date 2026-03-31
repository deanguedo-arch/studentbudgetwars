from __future__ import annotations

from budgetwars.models import (
    CommodityDefinition,
    ContentBundle,
    DifficultyModifier,
    DistrictDefinition,
    EventDefinition,
    ExamWeekDefinition,
    GigDefinition,
    ItemDefinition,
    PresetDefinition,
    ServiceDefinition,
)


def _find(records: list[object], record_id: str, label: str) -> object:
    for record in records:
        if getattr(record, "id") == record_id:
            return record
    raise ValueError(f"Unknown {label} id '{record_id}'")


def get_difficulty(bundle: ContentBundle, difficulty_id: str) -> DifficultyModifier:
    return _find(bundle.difficulties, difficulty_id, "difficulty")  # type: ignore[return-value]


def get_preset(bundle: ContentBundle, preset_id: str) -> PresetDefinition:
    return _find(bundle.presets, preset_id, "preset")  # type: ignore[return-value]


def get_district(bundle: ContentBundle, district_id: str) -> DistrictDefinition:
    return _find(bundle.districts, district_id, "district")  # type: ignore[return-value]


def get_commodity(bundle: ContentBundle, commodity_id: str) -> CommodityDefinition:
    return _find(bundle.commodities, commodity_id, "commodity")  # type: ignore[return-value]


def get_gig(bundle: ContentBundle, gig_id: str) -> GigDefinition:
    return _find(bundle.gigs, gig_id, "gig")  # type: ignore[return-value]


def get_item(bundle: ContentBundle, item_id: str) -> ItemDefinition:
    return _find(bundle.items, item_id, "item")  # type: ignore[return-value]


def get_service(bundle: ContentBundle, service_id: str) -> ServiceDefinition:
    return _find(bundle.services, service_id, "service")  # type: ignore[return-value]


def get_event(bundle: ContentBundle, event_id: str) -> EventDefinition:
    return _find(bundle.events, event_id, "event")  # type: ignore[return-value]


def get_exam_week(bundle: ContentBundle, week: int) -> ExamWeekDefinition | None:
    for exam in bundle.exam_weeks:
        if exam.week == week:
            return exam
    return None
