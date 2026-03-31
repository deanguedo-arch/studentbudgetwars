from __future__ import annotations

from collections.abc import Iterable

from budgetwars.models import ContentBundle


VALID_EFFECT_KEYS = {"cash", "debt", "bank_balance", "energy", "stress", "heat", "gpa", "study_points"}


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


def _validate_effects(effects: dict[str, float], label: str) -> None:
    invalid = sorted(set(effects) - VALID_EFFECT_KEYS)
    if invalid:
        raise ValueError(f"{label} has invalid effect keys: {', '.join(invalid)}")


def validate_content_bundle(bundle: ContentBundle) -> None:
    _ensure_unique_ids(bundle.difficulties, "difficulty")
    _ensure_unique_ids(bundle.districts, "district")
    _ensure_unique_ids(bundle.commodities, "commodity")
    _ensure_unique_ids(bundle.gigs, "gig")
    _ensure_unique_ids(bundle.events, "event")
    _ensure_unique_ids(bundle.items, "item")
    _ensure_unique_ids(bundle.services, "service")
    _ensure_unique_ids(bundle.presets, "preset")
    exam_weeks_seen: set[int] = set()
    for exam_week in bundle.exam_weeks:
        if exam_week.week in exam_weeks_seen:
            raise ValueError(f"Duplicate exam week found for week {exam_week.week}")
        exam_weeks_seen.add(exam_week.week)

    district_ids = {district.id for district in bundle.districts}
    commodity_ids = {commodity.id for commodity in bundle.commodities}
    gig_ids = {gig.id for gig in bundle.gigs}
    item_ids = {item.id for item in bundle.items}
    service_ids = {service.id for service in bundle.services}

    if bundle.config.low_energy_threshold >= bundle.config.max_energy:
        raise ValueError("config.low_energy_threshold must be below config.max_energy")
    if bundle.config.minimum_survival_gpa > 4.0:
        raise ValueError("config.minimum_survival_gpa cannot exceed 4.0")
    if bundle.config.debt_interest_rate > 0.25:
        raise ValueError("config.debt_interest_rate is implausibly high")
    if bundle.config.bank_interest_rate > 0.1:
        raise ValueError("config.bank_interest_rate is implausibly high")
    if bundle.config.weekly_market_event_count > 3:
        raise ValueError("config.weekly_market_event_count is too high for the current market model")

    for district in bundle.districts:
        unknown_services = sorted(set(district.service_ids) - service_ids)
        if unknown_services:
            raise ValueError(f"District '{district.id}' references unknown services: {', '.join(unknown_services)}")
        unknown_gigs = sorted(set(district.gig_ids) - gig_ids)
        if unknown_gigs:
            raise ValueError(f"District '{district.id}' references unknown gigs: {', '.join(unknown_gigs)}")
        unknown_biases = sorted(set(district.commodity_biases) - commodity_ids)
        if unknown_biases:
            raise ValueError(f"District '{district.id}' references unknown commodity biases: {', '.join(unknown_biases)}")

    for commodity in bundle.commodities:
        if not commodity.min_price < commodity.max_price:
            raise ValueError(f"Commodity '{commodity.id}' must have min_price below max_price")
        if not commodity.typical_low <= commodity.typical_high:
            raise ValueError(f"Commodity '{commodity.id}' must have typical_low <= typical_high")
        if not commodity.min_price <= commodity.typical_low <= commodity.max_price:
            raise ValueError(f"Commodity '{commodity.id}' has a typical_low outside its min/max range")
        if not commodity.min_price <= commodity.typical_high <= commodity.max_price:
            raise ValueError(f"Commodity '{commodity.id}' has a typical_high outside its min/max range")
        unknown_districts = sorted(set(commodity.district_biases) - district_ids)
        if unknown_districts:
            raise ValueError(
                f"Commodity '{commodity.id}' references unknown district biases: {', '.join(unknown_districts)}"
            )

    for gig in bundle.gigs:
        unknown_districts = sorted(set(gig.district_ids) - district_ids)
        if unknown_districts:
            raise ValueError(f"Gig '{gig.id}' references unknown districts: {', '.join(unknown_districts)}")
        unknown_items = sorted(set(gig.required_item_ids) - item_ids)
        if unknown_items:
            raise ValueError(f"Gig '{gig.id}' references unknown required items: {', '.join(unknown_items)}")

    for event in bundle.events:
        _validate_effects(event.stat_effects, f"Event '{event.id}'")
        unknown_commodities = sorted(set(event.commodity_multipliers) - commodity_ids)
        if unknown_commodities:
            raise ValueError(f"Event '{event.id}' references unknown commodities: {', '.join(unknown_commodities)}")
        unknown_district_maps = sorted(set(event.district_commodity_multipliers) - district_ids)
        if unknown_district_maps:
            raise ValueError(
                f"Event '{event.id}' references unknown district modifiers: {', '.join(unknown_district_maps)}"
            )
        for district_id, local_map in event.district_commodity_multipliers.items():
            unknown_local = sorted(set(local_map) - commodity_ids)
            if unknown_local:
                raise ValueError(
                    f"Event '{event.id}' references unknown commodities for district '{district_id}': "
                    f"{', '.join(unknown_local)}"
                )

    for item in bundle.items:
        _validate_effects(item.use_effects, f"Item '{item.id}'")
        unknown_districts = sorted(set(item.district_ids) - district_ids)
        if unknown_districts:
            raise ValueError(f"Item '{item.id}' references unknown districts: {', '.join(unknown_districts)}")

    for service in bundle.services:
        unknown_districts = sorted(set(service.district_ids) - district_ids)
        if unknown_districts:
            raise ValueError(f"Service '{service.id}' references unknown districts: {', '.join(unknown_districts)}")
        unknown_items = sorted(set(service.item_ids) - item_ids)
        if unknown_items:
            raise ValueError(f"Service '{service.id}' references unknown items: {', '.join(unknown_items)}")

    for preset in bundle.presets:
        if preset.starting_district_id not in district_ids:
            raise ValueError(f"Preset '{preset.id}' references unknown district '{preset.starting_district_id}'")
        unknown_items = sorted(set(preset.starting_item_ids) - item_ids)
        if unknown_items:
            raise ValueError(f"Preset '{preset.id}' references unknown items: {', '.join(unknown_items)}")
        if preset.starting_gpa < bundle.config.minimum_survival_gpa / 2:
            raise ValueError(f"Preset '{preset.id}' starts with implausibly low GPA")

    for exam_week in bundle.exam_weeks:
        if exam_week.week > bundle.config.term_weeks:
            raise ValueError(f"Exam week '{exam_week.label}' falls outside the configured term")
        if exam_week.required_study_points > 14:
            raise ValueError(f"Exam week '{exam_week.label}' asks for an implausible amount of study")
