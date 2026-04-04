from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from budgetwars.models import ContentBundle

GameMode = Literal["classic", "desktop"]


def normalize_mode(mode: str | None) -> GameMode:
    return "desktop" if mode == "desktop" else "classic"


@dataclass
class StartupOptions:
    mode: GameMode = "classic"
    player_name: str = "Player"
    preset_id: str | None = None
    difficulty_id: str | None = None
    city_id: str | None = None
    academic_level_id: str | None = None
    family_support_level_id: str | None = None
    savings_band_id: str | None = None
    opening_path_id: str | None = None
    seed: int | None = None
    load_name: str | None = None

    def is_new_game_complete(self) -> bool:
        return all(
            [
                self.preset_id,
                self.difficulty_id,
                self.city_id,
                self.academic_level_id,
                self.family_support_level_id,
                self.savings_band_id,
                self.opening_path_id,
            ]
        )

    def with_mode(self, mode: str | None) -> StartupOptions:
        return replace(self, mode=normalize_mode(mode))

    def completed_with_defaults(self, bundle: ContentBundle, *, default_player_name: str | None = None) -> StartupOptions:
        def pick(explicit: str | None, records, fallback_id: str | None = None) -> str:
            if explicit:
                return explicit
            if fallback_id and any(item.id == fallback_id for item in records):
                return fallback_id
            return records[0].id

        return StartupOptions(
            mode=self.mode,
            player_name=self.player_name or default_player_name or "Player",
            preset_id=pick(self.preset_id, bundle.presets, "supported_student"),
            difficulty_id=pick(self.difficulty_id, bundle.difficulties, "normal"),
            city_id=pick(self.city_id, bundle.cities, "hometown_low_cost"),
            academic_level_id=pick(self.academic_level_id, bundle.config.academic_levels, "average"),
            family_support_level_id=pick(self.family_support_level_id, bundle.config.family_support_levels, "medium"),
            savings_band_id=pick(self.savings_band_id, bundle.config.savings_bands, "some"),
            opening_path_id=pick(self.opening_path_id, bundle.config.opening_paths, "full_time_work"),
            seed=self.seed,
            load_name=self.load_name,
        )
