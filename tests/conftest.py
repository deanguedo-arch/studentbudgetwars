from __future__ import annotations

from pathlib import Path

import pytest

from budgetwars.engine import GameController
from budgetwars.loaders import load_all_content


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle():
    return load_all_content(PROJECT_ROOT)


@pytest.fixture
def controller_factory(bundle):
    def _make(
        *,
        preset_id: str = "supported_student",
        difficulty_id: str = "normal",
        city_id: str = "hometown",
        opening_path_id: str = "full_time_work",
        seed: int = 42,
    ) -> GameController:
        return GameController.new_game(
            bundle,
            "Tester",
            preset_id=preset_id,
            difficulty_id=difficulty_id,
            city_id=city_id,
            opening_path_id=opening_path_id,
            seed=seed,
        )

    return _make
