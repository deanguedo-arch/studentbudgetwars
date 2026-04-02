from __future__ import annotations

import json
import shutil
from pathlib import Path

from budgetwars.core import GameSession, StartupOptions
from budgetwars.games.classic import build_classic_session
from budgetwars.games.desktop import build_desktop_session
from budgetwars.loaders import load_all_content
from budgetwars.main import build_parser


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_parser_defaults_to_classic_mode():
    args = build_parser().parse_args([])
    assert args.mode == "classic"


def test_cli_parser_preserves_mode_and_existing_args():
    args = build_parser().parse_args(["--mode", "desktop", "--name", "Dana", "--path", "full_time_work"])
    assert args.mode == "desktop"
    assert args.name == "Dana"
    assert args.opening_path == "full_time_work"


def test_session_can_create_new_game_from_startup_options():
    session = GameSession.from_startup_options(
        StartupOptions(
            mode="classic",
            player_name="Tester",
            preset_id="supported_student",
            difficulty_id="normal",
            city_id="hometown_low_cost",
            academic_level_id="average",
            family_support_level_id="medium",
            savings_band_id="some",
            opening_path_id="full_time_work",
        ),
        root=PROJECT_ROOT,
    )
    assert session.has_active_game is True
    assert session.state.player.name == "Tester"


def test_session_load_flow_round_trip_through_shared_path(tmp_path):
    started = GameSession.from_startup_options(
        StartupOptions(
            mode="classic",
            player_name="Saver",
            preset_id="supported_student",
            difficulty_id="normal",
            city_id="hometown_low_cost",
            academic_level_id="average",
            family_support_level_id="medium",
            savings_band_id="some",
            opening_path_id="full_time_work",
        ),
        root=PROJECT_ROOT,
    )
    save_path = tmp_path / "session_save.json"
    started.save_to_path(save_path)
    loaded = GameSession.load_from_path(save_path, mode="classic", root=PROJECT_ROOT)
    assert loaded.has_active_game is True
    assert loaded.state.player.name == "Saver"
    assert loaded.state.player.career.track_id == started.state.player.career.track_id


def test_content_overlay_uses_file_replacement_precedence(tmp_path):
    shutil.copytree(PROJECT_ROOT / "data", tmp_path / "data")
    (tmp_path / "content" / "shared").mkdir(parents=True)
    (tmp_path / "content" / "desktop").mkdir(parents=True)
    cities_path = tmp_path / "data" / "cities.json"
    cities = json.loads(cities_path.read_text(encoding="utf-8"))
    cities[0]["name"] = "Overlay City"
    (tmp_path / "content" / "desktop" / "cities.json").write_text(json.dumps(cities, indent=2), encoding="utf-8")

    classic_bundle = load_all_content(tmp_path, mode="classic")
    desktop_bundle = load_all_content(tmp_path, mode="desktop")

    assert classic_bundle.cities[0].name != "Overlay City"
    assert desktop_bundle.cities[0].name == "Overlay City"


def test_frontend_builders_create_real_shared_sessions():
    options = StartupOptions(
        mode="classic",
        player_name="Builder",
        preset_id="supported_student",
        difficulty_id="normal",
        city_id="hometown_low_cost",
        academic_level_id="average",
        family_support_level_id="medium",
        savings_band_id="some",
        opening_path_id="full_time_work",
    )
    classic = build_classic_session(options, root=PROJECT_ROOT)
    desktop = build_desktop_session(StartupOptions(mode="desktop", player_name="Desk"), root=PROJECT_ROOT)
    assert classic.has_active_game is True
    assert desktop.has_active_game is True
    assert classic.mode == "classic"
    assert desktop.mode == "desktop"
