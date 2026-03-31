from __future__ import annotations

import math

from budgetwars.models import ContentBundle, GameState, PlayerState, SupportItemEntry
from budgetwars.utils import clamp

from .effects import append_log, trim_log
from .events import prune_expired_events, roll_daily_event, roll_weekly_events
from .lookups import get_difficulty, get_exam_week, get_preset
from .market import generate_daily_markets


def _set_recent_summary(state: GameState, prior_log_length: int) -> GameState:
    return state.model_copy(update={"recent_summary": state.log_messages[prior_log_length:][-8:]})


def _refresh_markets(state: GameState, bundle: ContentBundle) -> GameState:
    markets = generate_daily_markets(state, bundle)
    return state.model_copy(update={"current_markets": markets})


def _check_game_over(state: GameState) -> GameState:
    if state.game_over_reason:
        return state
    if state.player.debt >= state.debt_game_over_threshold:
        return state.model_copy(update={"game_over_reason": "Debt spiral overwhelmed you"})
    if state.player.stress >= state.max_stress:
        return state.model_copy(update={"game_over_reason": "Stress breakdown ended the run"})
    if state.player.heat >= state.max_heat:
        return state.model_copy(update={"game_over_reason": "Too much attention closed your lanes"})
    if state.low_energy_streak >= state.low_energy_streak_limit:
        return state.model_copy(update={"game_over_reason": "Energy collapse dragged on too long"})
    if state.player.gpa <= 0.5:
        return state.model_copy(update={"game_over_reason": "Academic standing collapsed"})
    return state


def _update_low_energy_streak(state: GameState) -> GameState:
    streak = state.low_energy_streak + 1 if state.player.energy <= state.low_energy_threshold else 0
    return state.model_copy(update={"low_energy_streak": streak})


def _spend_or_add_debt(state: GameState, amount: int, label: str) -> GameState:
    if amount <= 0:
        return state
    if state.player.cash >= amount:
        updated_player = state.player.model_copy(update={"cash": state.player.cash - amount})
        state = state.model_copy(update={"player": updated_player})
        return append_log(state, f"Paid ${amount} for {label}.")
    shortfall = amount - state.player.cash
    updated_player = state.player.model_copy(update={"cash": 0, "debt": state.player.debt + shortfall})
    state = state.model_copy(update={"player": updated_player})
    return append_log(state, f"{label} cost ${amount}; ${shortfall} rolled into debt.")


def _apply_exam_check(state: GameState, bundle: ContentBundle) -> GameState:
    exam = get_exam_week(bundle, state.current_week)
    if exam is None:
        return state.model_copy(update={"weekly_study_points": 0})
    difficulty = get_difficulty(bundle, state.difficulty_id)
    required_points = math.ceil(exam.required_study_points * difficulty.study_requirement_multiplier)
    if state.weekly_study_points >= required_points:
        updated_player = state.player.model_copy(
            update={"gpa": float(clamp(state.player.gpa + exam.gpa_reward, 0.0, 4.0))}
        )
        state = state.model_copy(update={"player": updated_player, "weekly_study_points": 0})
        return append_log(state, f"{exam.label}: you kept pace academically and steadied your GPA.")
    updated_player = state.player.model_copy(
        update={
            "gpa": float(clamp(state.player.gpa - exam.gpa_penalty, 0.0, 4.0)),
            "stress": int(clamp(state.player.stress + exam.stress_delta, 0, state.max_stress)),
        }
    )
    state = state.model_copy(update={"player": updated_player, "weekly_study_points": 0})
    return append_log(state, f"{exam.label}: you fell short on study time and paid for it.")


def _apply_weekly_tick(state: GameState, bundle: ContentBundle) -> GameState:
    difficulty = get_difficulty(bundle, state.difficulty_id)
    housing = int(round(bundle.config.weekly_costs.housing * difficulty.rent_multiplier))
    state = append_log(state, f"Week {state.current_week} closeout.")
    state = _spend_or_add_debt(state, housing, "housing")
    state = _spend_or_add_debt(state, bundle.config.weekly_costs.utilities, "utilities")
    state = _spend_or_add_debt(state, bundle.config.weekly_costs.phone, "phone")

    interest_rate = bundle.config.debt_interest_rate * difficulty.debt_interest_multiplier
    debt_interest = int(round(state.player.debt * interest_rate))
    bank_growth = int(round(state.player.bank_balance * bundle.config.bank_interest_rate))
    updated_player = state.player.model_copy(
        update={
            "debt": state.player.debt + debt_interest,
            "bank_balance": state.player.bank_balance + bank_growth,
            "heat": max(0, state.player.heat - bundle.config.heat_decay_per_week),
        }
    )
    state = state.model_copy(update={"player": updated_player})
    state = append_log(state, f"Debt interest +${debt_interest}; bank interest +${bank_growth}.")
    return _apply_exam_check(state, bundle)


def initialize_new_game(
    bundle: ContentBundle,
    player_name: str,
    preset_id: str | None,
    difficulty_id: str,
    seed: int | None,
) -> GameState:
    preset = get_preset(bundle, preset_id or bundle.presets[0].id)
    difficulty = get_difficulty(bundle, difficulty_id)
    state = GameState(
        game_title=bundle.config.game_title,
        player_name=player_name,
        difficulty_id=difficulty.id,
        seed=seed if seed is not None else bundle.config.default_seed,
        current_day=1,
        total_days=bundle.config.total_days,
        days_per_week=bundle.config.days_per_week,
        max_stress=bundle.config.max_stress,
        max_energy=bundle.config.max_energy,
        max_heat=bundle.config.max_heat,
        low_energy_threshold=bundle.config.low_energy_threshold,
        low_energy_streak_limit=bundle.config.low_energy_streak_limit,
        debt_game_over_threshold=bundle.config.debt_game_over_threshold,
        minimum_survival_gpa=bundle.config.minimum_survival_gpa,
        minimum_survival_net_worth=bundle.config.minimum_survival_net_worth,
        player=PlayerState(
            name=player_name,
            cash=preset.starting_cash + difficulty.cash_bonus,
            debt=max(0, preset.starting_debt + difficulty.debt_bonus),
            bank_balance=preset.starting_bank_balance,
            energy=int(clamp(preset.starting_energy, 0, bundle.config.max_energy)),
            stress=int(clamp(preset.starting_stress, 0, bundle.config.max_stress)),
            heat=int(clamp(preset.starting_heat, 0, bundle.config.max_heat)),
            gpa=preset.starting_gpa,
            current_district_id=preset.starting_district_id,
            backpack_capacity=preset.starting_backpack_capacity,
            item_inventory=[
                SupportItemEntry(item_id=item_id, quantity=quantity)
                for item_id, quantity in preset.starting_item_ids.items()
                if quantity > 0
            ],
        ),
    )
    state = append_log(state, f"Started a new run as {preset.name}.")
    state = roll_weekly_events(state, bundle)
    state = _refresh_markets(state, bundle)
    state = trim_log(state, bundle.config.message_log_limit)
    return state.model_copy(update={"recent_summary": state.log_messages[-6:]})


def advance_after_action(state: GameState, bundle: ContentBundle, prior_log_length: int) -> GameState:
    state = _update_low_energy_streak(state)
    state = _check_game_over(state)
    if state.game_over_reason:
        state = trim_log(state, bundle.config.message_log_limit)
        return _set_recent_summary(state, prior_log_length)

    state = roll_daily_event(state, bundle)
    state = _check_game_over(state)
    if state.game_over_reason:
        state = trim_log(state, bundle.config.message_log_limit)
        return _set_recent_summary(state, prior_log_length)

    if state.current_day % state.days_per_week == 0:
        state = _apply_weekly_tick(state, bundle)
        state = _check_game_over(state)
        if state.game_over_reason:
            state = trim_log(state, bundle.config.message_log_limit)
            return _set_recent_summary(state, prior_log_length)

    state = state.model_copy(update={"current_day": state.current_day + 1})
    state = prune_expired_events(state)

    if state.current_day <= state.total_days:
        if (state.current_day - 1) % state.days_per_week == 0:
            state = roll_weekly_events(state, bundle)
        state = _refresh_markets(state, bundle)

    state = _check_game_over(state)
    state = trim_log(state, bundle.config.message_log_limit)
    return _set_recent_summary(state, prior_log_length)
