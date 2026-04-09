from __future__ import annotations

from budgetwars.games.classic.ui.main_window import build_setup_summary_lines


def test_setup_summary_uses_run_picker_language(bundle) -> None:
    selections = {
        "preset_id": "supported_student",
        "city_id": "hometown_low_cost",
        "academic_level_id": "average",
        "family_support_level_id": "medium",
        "savings_band_id": "some",
        "opening_path_id": "full_time_work",
        "difficulty_id": "normal",
    }

    lines = build_setup_summary_lines(bundle, selections, "PreviewPlayer")

    joined = "\n".join(lines)
    assert "Your Start" in joined
    assert "Your Pressure" in joined
    assert "Your Best Edge" in joined
    assert "Forecast:" in joined
    assert "Tags:" in joined
