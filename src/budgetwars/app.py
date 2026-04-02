from __future__ import annotations

from budgetwars.core import StartupOptions
from budgetwars.launcher import launch_mode


def run_app(
    player_name: str = "Player",
    preset_id: str | None = None,
    difficulty_id: str | None = None,
    city_id: str | None = None,
    academic_level_id: str | None = None,
    family_support_level_id: str | None = None,
    savings_band_id: str | None = None,
    opening_path_id: str | None = None,
    seed: int | None = None,
    load_name: str | None = None,
) -> None:
    launch_mode(
        StartupOptions(
            mode="classic",
            player_name=player_name,
            preset_id=preset_id,
            difficulty_id=difficulty_id,
            city_id=city_id,
            academic_level_id=academic_level_id,
            family_support_level_id=family_support_level_id,
            savings_band_id=savings_band_id,
            opening_path_id=opening_path_id,
            seed=seed,
            load_name=load_name,
        )
    )
