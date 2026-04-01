from __future__ import annotations

from budgetwars.models import (
    AcademicLevelDefinition,
    BudgetStanceDefinition,
    CareerTierDefinition,
    CareerTrackDefinition,
    CityDefinition,
    ContentBundle,
    DifficultyModifier,
    EducationProgramDefinition,
    EventDefinition,
    FamilySupportLevelDefinition,
    FocusActionDefinition,
    GameState,
    HousingOptionDefinition,
    OpeningPathDefinition,
    PresetDefinition,
    SavingsBandDefinition,
    TransportOptionDefinition,
)


def _get_by_id(collection, item_id: str, label: str):
    for item in collection:
        if item.id == item_id:
            return item
    raise ValueError(f"Unknown {label}: {item_id}")


def get_city(bundle: ContentBundle, city_id: str) -> CityDefinition:
    return _get_by_id(bundle.cities, city_id, "city")


def get_career_track(bundle: ContentBundle, career_id: str) -> CareerTrackDefinition:
    return _get_by_id(bundle.careers, career_id, "career track")


def get_current_career_tier(bundle: ContentBundle, state: GameState) -> CareerTierDefinition:
    track = get_career_track(bundle, state.player.career.track_id)
    return track.tiers[state.player.career.tier_index]


def get_education_program(bundle: ContentBundle, program_id: str) -> EducationProgramDefinition:
    return _get_by_id(bundle.education_programs, program_id, "education program")


def get_housing_option(bundle: ContentBundle, housing_id: str) -> HousingOptionDefinition:
    return _get_by_id(bundle.housing_options, housing_id, "housing option")


def get_transport_option(bundle: ContentBundle, transport_id: str) -> TransportOptionDefinition:
    return _get_by_id(bundle.transport_options, transport_id, "transport option")


def get_focus_action(bundle: ContentBundle, focus_id: str) -> FocusActionDefinition:
    return _get_by_id(bundle.focus_actions, focus_id, "focus action")


def get_event(bundle: ContentBundle, event_id: str) -> EventDefinition:
    return _get_by_id(bundle.events, event_id, "event")


def get_preset(bundle: ContentBundle, preset_id: str) -> PresetDefinition:
    return _get_by_id(bundle.presets, preset_id, "preset")


def get_difficulty(bundle: ContentBundle, difficulty_id: str) -> DifficultyModifier:
    return _get_by_id(bundle.difficulties, difficulty_id, "difficulty")


def get_budget_stance(bundle: ContentBundle, stance_id: str) -> BudgetStanceDefinition:
    return _get_by_id(bundle.config.budget_stances, stance_id, "budget stance")


def get_opening_path(bundle: ContentBundle, opening_path_id: str) -> OpeningPathDefinition:
    return _get_by_id(bundle.config.opening_paths, opening_path_id, "opening path")


def get_academic_level(bundle: ContentBundle, option_id: str) -> AcademicLevelDefinition:
    return _get_by_id(bundle.config.academic_levels, option_id, "academic level")


def get_family_support_level(bundle: ContentBundle, option_id: str) -> FamilySupportLevelDefinition:
    return _get_by_id(bundle.config.family_support_levels, option_id, "family support level")


def get_savings_band(bundle: ContentBundle, option_id: str) -> SavingsBandDefinition:
    return _get_by_id(bundle.config.savings_bands, option_id, "savings band")
