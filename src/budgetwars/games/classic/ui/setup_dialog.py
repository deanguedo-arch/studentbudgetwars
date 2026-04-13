from __future__ import annotations

from .choice_previews import _money


def _lookup_option(options: list[tuple[str, str, str]], value_id: str | None) -> tuple[str, str, str]:
    if value_id is not None:
        for option in options:
            if option[1] == value_id:
                return option
    return options[0]


def compute_setup_dialog_geometry(
    *,
    parent_x: int,
    parent_y: int,
    parent_width: int,
    parent_height: int,
    screen_width: int,
    screen_height: int,
) -> tuple[int, int, int, int]:
    margin = 24
    width_cap = max(640, min(parent_width - margin * 2, screen_width - margin * 2, 1320))
    height_cap = max(560, min(parent_height - margin * 2, screen_height - margin * 2, 860))
    width = min(max(860, int(parent_width * 0.84)), width_cap)
    height = min(max(600, int(parent_height * 0.84)), height_cap)
    x = parent_x + max(margin, (parent_width - width) // 2)
    y = parent_y + max(margin, (parent_height - height) // 2)
    x = max(0, min(x, screen_width - width))
    y = max(0, min(y, screen_height - height))
    return x, y, width, height


def build_setup_summary_lines(bundle, selections: dict[str, str], player_name: str) -> list[str]:
    preset = next(item for item in bundle.presets if item.id == selections["preset_id"])
    city = next(item for item in bundle.cities if item.id == selections["city_id"])
    academic = next(item for item in bundle.config.academic_levels if item.id == selections["academic_level_id"])
    support = next(item for item in bundle.config.family_support_levels if item.id == selections["family_support_level_id"])
    savings = next(item for item in bundle.config.savings_bands if item.id == selections["savings_band_id"])
    path = next(item for item in bundle.config.opening_paths if item.id == selections["opening_path_id"])
    difficulty = next(item for item in bundle.difficulties if item.id == selections["difficulty_id"])
    opening_cash = preset.starting_cash + savings.cash_delta
    opening_savings = preset.starting_savings + savings.savings_delta
    opening_debt = preset.starting_debt + savings.debt_delta
    opening_net = opening_cash + opening_savings - opening_debt
    tags: list[str] = []
    if opening_net >= 0:
        tags.append("Safe Start")
    if opening_debt > opening_cash + opening_savings:
        tags.append("Debt Risk")
    if support.name.lower() in {"high", "strong", "best", "excellent"} or support.description.lower().find("family") >= 0:
        tags.append("Beginner Friendly")
    if academic.name.lower() in {"average", "strong", "excellent"}:
        tags.append("High Upside")
    if not tags:
        tags.append("Rough Start")
    forecast = "You can likely absorb a mistake early." if opening_net >= 0 else "You will need to protect cash flow early."
    return [
        f"Player: {player_name or 'Player'}",
        "",
        "Opening Identity",
        "Your Start",
        f"Preset: {preset.name}",
        f"City: {city.name}",
        "",
        "Opening Lane",
        "Your Pressure",
        f"Path: {path.name}",
        f"Academics: {academic.name}",
        f"Family support: {support.name}",
        f"Starting cushion: {savings.name}",
        "",
        "Run Preview",
        "Your Best Edge",
        f"Cash: {_money(opening_cash)} | Savings: {_money(opening_savings)} | Debt: {_money(opening_debt)}",
        f"Opening net worth: {_money(opening_net)}",
        f"Forecast: {forecast}",
        f"Tags: {', '.join(tags)}",
        f"Difficulty: {difficulty.name}",
    ]
