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
def quiet_bundle(bundle):
    quiet = bundle.model_copy(deep=True)
    quiet.config = quiet.config.model_copy(update={"daily_event_chance": 0.0, "weekly_market_event_count": 0})
    return quiet


@pytest.fixture
def controller_factory():
    def _make(bundle, *, preset_id: str = "dorm_flipper", difficulty_id: str = "normal", seed: int = 123):
        return GameController.new_game(bundle, "Tester", preset_id, difficulty_id, seed)

    return _make
