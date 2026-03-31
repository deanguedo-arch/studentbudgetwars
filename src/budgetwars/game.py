from __future__ import annotations

import re
from pathlib import Path
from typing import Callable

from rich.console import Console

from .budget import (
    add_temporary_effects,
    apply_stat_effects,
    apply_start_of_week_temporary_effects,
    apply_interest_and_fees,
    decrement_temporary_effects,
    apply_mandatory_weekly_expenses,
    apply_optional_weekly_expenses,
    apply_rest_action,
    apply_weekly_income,
)
from .economy import buy_item
from .events import resolve_event_choice, roll_event
from .jobs import get_job, switch_job
from .loaders import load_all_content
from .locations import apply_location_effects, get_location, move_location
from .models import (
    ContentBundle,
    DifficultyDefinition,
    EventDefinition,
    ExpenseDefinition,
    GameState,
    ItemDefinition,
    PlayerState,
)
from .saves import load_game, save_game
from .scoring import calculate_final_score
from .ui import (
    render_event,
    render_final_summary,
    render_game_screen,
    render_job_options,
    render_item_shop,
    render_location_options,
    render_title_screen,
)
from .utils import clamp, make_rng, trim_messages


def start_new_game(
    player_name: str = "Player",
    preset_id: str | None = None,
    difficulty_id: str = "normal",
    seed: int | None = None,
    bundle: ContentBundle | None = None,
) -> tuple[ContentBundle, GameState]:
    bundle = bundle or load_all_content()

    selected_preset = next((preset for preset in bundle.presets if preset.id == preset_id), None)
    if selected_preset is None:
        selected_preset = bundle.presets[0]

    difficulty = next((entry for entry in bundle.config.difficulties if entry.id == difficulty_id), None)
    if difficulty is None:
        raise ValueError(f"Unknown difficulty: {difficulty_id}")

    resolved_seed = bundle.config.default_seed if seed is None else seed

    player = PlayerState(
        name=player_name,
        cash=selected_preset.starting_cash + difficulty.starting_cash_bonus,
        savings=selected_preset.starting_savings,
        debt=selected_preset.starting_debt,
        stress=selected_preset.starting_stress,
        energy=selected_preset.starting_energy,
        location_id=selected_preset.starting_location_id,
        job_id=selected_preset.starting_job_id,
    )
    state = GameState(
        game_title=bundle.config.game_title,
        difficulty_id=difficulty.id,
        current_week=bundle.config.starting_week,
        term_weeks=bundle.config.term_weeks,
        max_stress=bundle.config.max_stress,
        max_energy=bundle.config.max_energy,
        low_energy_threshold=bundle.config.low_energy_threshold,
        low_energy_week_limit=bundle.config.low_energy_week_limit,
        debt_game_over_threshold=bundle.config.debt_game_over_threshold,
        max_missed_essential_weeks=bundle.config.max_missed_essential_weeks,
        seed=resolved_seed,
        player=player,
        message_log=[f"New game started on {difficulty.name} difficulty."],
    )
    return bundle, state


def load_existing_game(filename: str, saves_dir: Path | None = None) -> GameState:
    return load_game(filename, saves_dir=saves_dir)


def _lookup_difficulty(bundle: ContentBundle, difficulty_id: str) -> DifficultyDefinition:
    difficulty = next((entry for entry in bundle.config.difficulties if entry.id == difficulty_id), None)
    if difficulty is None:
        raise ValueError(f"Unknown difficulty: {difficulty_id}")
    return difficulty


def _lookup_item(bundle: ContentBundle, item_id: str) -> ItemDefinition | None:
    return next((item for item in bundle.items if item.id == item_id), None)


def _update_failure_trackers(state: GameState) -> GameState:
    low_energy_streak = state.consecutive_low_energy_weeks + 1 if state.player.energy <= state.low_energy_threshold else 0
    return state.model_copy(update={"consecutive_low_energy_weeks": low_energy_streak})


def _finalize_state(state: GameState, message_log_limit: int) -> GameState:
    player = state.player.model_copy(
        update={
            "stress": clamp(state.player.stress, 0, state.max_stress),
            "energy": clamp(state.player.energy, 0, state.max_energy),
        }
    )
    reason = _get_game_over_reason(state.model_copy(update={"player": player}))
    return state.model_copy(
        update={
            "player": player,
            "game_over_reason": reason,
            "message_log": trim_messages(state.message_log, message_log_limit),
        }
    )


def _default_choice_id(event: EventDefinition) -> str | None:
    return event.choices[0].id if event.choices else None


def _make_week_rng(state: GameState):
    return make_rng((state.seed * 1000) + state.current_week)


def _location_modifier_text(location_modifiers: dict[str, int]) -> str:
    if not location_modifiers:
        return "neutral"
    return ", ".join(f"{stat} {delta:+d}" for stat, delta in location_modifiers.items())


def build_week_outlook(state: GameState, bundle: ContentBundle) -> list[str]:
    difficulty = _lookup_difficulty(bundle, state.difficulty_id)
    lines: list[str] = []

    location = get_location(bundle.locations, state.player.location_id)
    if location is not None:
        lines.append(f"Location pressure: {location.name} ({_location_modifier_text(location.modifiers)}).")
    else:
        lines.append("Location pressure: unknown location, effects may be skipped.")

    current_job = get_job(bundle.jobs, state.player.job_id)
    if current_job is not None:
        weekly_pay = int(round(current_job.hourly_pay * current_job.hours_per_week * difficulty.income_multiplier))
        strain = current_job.energy_cost + max(current_job.stress_delta, 0)
        lines.append(f"Job reality: {current_job.name} pays about {weekly_pay}/week, strain {strain}.")
        if state.player.location_id != current_job.location_id and state.player.energy <= state.low_energy_threshold + 10:
            lines.append(
                "Working offsite will increase strain this week. Move closer or rest if energy is tight."
            )
    else:
        lines.append("Job reality: no active job income this week.")

    if state.player.debt >= int(state.debt_game_over_threshold * 0.7):
        lines.append("Debt pressure is high. Work income or lower-cost choices are urgent.")
    elif state.player.debt >= int(state.debt_game_over_threshold * 0.5):
        lines.append("Debt is climbing. Watch optional spending and missed essentials.")

    if state.player.energy <= state.low_energy_threshold + 6:
        lines.append("Energy is low. Resting or a lower-pressure location is safer.")
    if state.player.stress >= state.max_stress - 15:
        lines.append("Stress is near the red zone. Recovery choices should be prioritized.")

    optional_expenses = [expense for expense in bundle.expenses if expense.cadence == "weekly" and not expense.mandatory]
    if optional_expenses:
        average_optional_cost = int(round(sum(expense.amount for expense in optional_expenses) / len(optional_expenses)))
        lines.append(
            f"Optional pressure: {len(optional_expenses)} choices this week (about {average_optional_cost} average each)."
        )

    if state.temporary_effects:
        active_labels = ", ".join(effect.label for effect in state.temporary_effects[:3])
        extra_count = max(0, len(state.temporary_effects) - 3)
        suffix = f" (+{extra_count} more)" if extra_count else ""
        lines.append(f"Carryover active: {active_labels}{suffix}.")

    return lines[:6]


def compress_week_messages(messages: list[str], start_index: int) -> list[str]:
    if start_index >= len(messages):
        return messages

    prior_messages = messages[:start_index]
    week_messages = messages[start_index:]

    paid_count = 0
    paid_total = 0
    debt_backed_count = 0
    optional_paid_count = 0
    optional_skipped_count = 0
    active_effect_count = 0
    created_effect_count = 0
    carryover_appended_count = 0
    important_messages: list[str] = []

    for message in week_messages:
        if message.startswith("Resolving week "):
            continue
        if message.startswith("Paid "):
            paid_count += 1
            match = re.search(r"\(([-]?\d+)\)", message)
            if match:
                paid_total += int(match.group(1))
            if "and debt" in message:
                debt_backed_count += 1
            continue
        if message.startswith("Skipped optional expense:"):
            optional_skipped_count += 1
            continue
        if message.startswith("Optional expense paid ("):
            optional_paid_count += 1
            continue
        if message.startswith("Optional expense skipped ("):
            optional_skipped_count += 1
            continue
        if message.startswith("Temporary effect active ("):
            active_effect_count += 1
            continue
        if "created temporary effect" in message:
            created_effect_count += 1
            continue
        if message.startswith("Job carryover ("):
            carryover_appended_count += 1
            continue
        if message.startswith("Event effects ("):
            continue
        important_messages.append(message)

    summary_messages: list[str] = []
    if paid_count:
        debt_text = f", debt-backed {debt_backed_count}" if debt_backed_count else ""
        summary_messages.append(f"Weekly essentials: {paid_count} charge(s), total {paid_total}{debt_text}.")
    if optional_paid_count or optional_skipped_count:
        summary_messages.append(
            f"Optional choices: paid {optional_paid_count}, skipped {optional_skipped_count}."
        )
    if active_effect_count:
        summary_messages.append(f"Carryover effects applied this week: {active_effect_count}.")
    if created_effect_count or carryover_appended_count:
        summary_messages.append(
            f"New carryover effects queued: {created_effect_count + carryover_appended_count}."
        )

    return [*prior_messages, *summary_messages, *important_messages]


def _compress_state_messages_for_week(state: GameState, start_index: int) -> GameState:
    return state.model_copy(update={"message_log": compress_week_messages(state.message_log, start_index)})


def advance_week(
    state: GameState,
    bundle: ContentBundle,
    action: str,
    optional_expense_resolver: Callable[[ExpenseDefinition], bool] | None = None,
    choice_resolver: Callable[[EventDefinition], str | None] | None = None,
) -> GameState:
    difficulty = _lookup_difficulty(bundle, state.difficulty_id)
    week_log_start_index = len(state.message_log)
    updated_state = state.model_copy(update={"message_log": [*state.message_log, f"Resolving week {state.current_week}."]})
    active_effects_at_week_start = len(updated_state.temporary_effects)

    updated_state = apply_start_of_week_temporary_effects(updated_state)

    updated_state = apply_mandatory_weekly_expenses(
        updated_state,
        bundle.expenses,
        expense_multiplier=difficulty.expense_multiplier,
    )
    optional_decisions = {}
    for expense in bundle.expenses:
        if expense.cadence == "weekly" and not expense.mandatory:
            optional_decisions[expense.id] = optional_expense_resolver(expense) if optional_expense_resolver else True
    updated_state = apply_optional_weekly_expenses(
        updated_state,
        bundle.expenses,
        decisions=optional_decisions,
        expense_multiplier=difficulty.expense_multiplier,
    )

    if action == "work":
        current_job = get_job(bundle.jobs, updated_state.player.job_id)
        updated_state = apply_weekly_income(
            updated_state,
            current_job,
            income_multiplier=difficulty.income_multiplier,
            stress_multiplier=difficulty.stress_multiplier,
        )
        if current_job is not None:
            if (
                updated_state.player.location_id != current_job.location_id
                and (bundle.config.offsite_work_energy_penalty > 0 or bundle.config.offsite_work_stress_penalty > 0)
            ):
                updated_state = apply_stat_effects(
                    updated_state,
                    {
                        "energy": -bundle.config.offsite_work_energy_penalty,
                        "stress": bundle.config.offsite_work_stress_penalty,
                    },
                    f"Offsite work strain ({current_job.name})",
                )
            updated_state = add_temporary_effects(
                updated_state,
                current_job.work_temporary_effects,
                f"Job carryover ({current_job.name})",
            )
    elif action == "rest":
        updated_state = apply_rest_action(updated_state)
    else:
        raise ValueError(f"Unknown action: {action}")

    location = get_location(bundle.locations, updated_state.player.location_id)
    updated_state = apply_location_effects(updated_state, location)

    event = roll_event(_make_week_rng(state), bundle.events, bundle.config.weekly_event_chance)
    if event is not None:
        selected_choice_id = choice_resolver(event) if choice_resolver else _default_choice_id(event)
        updated_state = resolve_event_choice(updated_state, event, selected_choice_id)

    updated_state = apply_interest_and_fees(
        updated_state,
        interest_rate=bundle.config.debt_interest_rate,
        overdraft_fee=bundle.config.overdraft_fee,
    )
    updated_state = decrement_temporary_effects(updated_state, active_effects_at_week_start=active_effects_at_week_start)
    updated_state = _compress_state_messages_for_week(updated_state, week_log_start_index)

    updated_state = _update_failure_trackers(updated_state)
    updated_state = updated_state.model_copy(update={"current_week": state.current_week + 1})
    updated_state = _finalize_state(updated_state, bundle.config.message_log_limit)
    return updated_state


def _get_game_over_reason(state: GameState) -> str | None:
    if state.player.stress >= state.max_stress:
        return "Stress hit the breaking point."
    if state.consecutive_low_energy_weeks >= state.low_energy_week_limit:
        return "Energy stayed critically low for too many weeks."
    if state.player.debt >= state.debt_game_over_threshold:
        return "Debt spiraled out of control."
    if state.missed_essential_weeks >= state.max_missed_essential_weeks:
        return "You relied on debt for essentials too many times."
    return None


def check_game_over(state: GameState) -> bool:
    return state.current_week > state.term_weeks or _get_game_over_reason(state) is not None


def _prompt_item_purchase(console: Console, bundle: ContentBundle, state: GameState) -> GameState:
    render_item_shop(console, bundle.items)
    choice = console.input("Enter an item id to buy, or press Enter to cancel: ").strip()
    if not choice:
        return state

    item = _lookup_item(bundle, choice)
    if item is None:
        return state.model_copy(update={"message_log": [*state.message_log, f"Unknown item: {choice}."]})
    return buy_item(state, item)


def _prompt_event_choice(console: Console, event: EventDefinition) -> str | None:
    render_event(console, event)
    if not event.choices:
        console.input("Press Enter to continue...")
        return None

    raw = console.input("Choose event option number: ").strip()
    if raw.isdigit():
        index = int(raw) - 1
        if 0 <= index < len(event.choices):
            return event.choices[index].id
    return _default_choice_id(event)


def _prompt_optional_expense_decision(console: Console, expense: ExpenseDefinition) -> bool:
    raw = console.input(
        f"Optional expense '{expense.name}' ({expense.amount}) - pay or skip? [p/s, default p]: "
    ).strip().lower()
    return raw not in {"s", "skip"}


def _prompt_job_switch(console: Console, bundle: ContentBundle, state: GameState) -> GameState:
    render_job_options(console, bundle.jobs, current_job_id=state.player.job_id)
    choice = console.input("Enter a job id to switch, or press Enter to cancel: ").strip()
    if not choice:
        return state
    return switch_job(
        state,
        bundle.jobs,
        choice,
        stress_penalty=bundle.config.job_switch_stress_penalty,
        sync_location_to_job=True,
    )


def _prompt_location_move(console: Console, bundle: ContentBundle, state: GameState) -> GameState:
    render_location_options(console, bundle.locations, current_location_id=state.player.location_id)
    choice = console.input("Enter a location id to move, or press Enter to cancel: ").strip()
    if not choice:
        return state
    return move_location(
        state,
        bundle.locations,
        choice,
        stress_penalty=bundle.config.location_move_stress_penalty,
    )


def run_game_loop(
    state: GameState,
    bundle: ContentBundle | None = None,
    console: Console | None = None,
    saves_dir: Path | None = None,
) -> GameState:
    active_console = console or Console()
    content = bundle or load_all_content()
    render_title_screen(active_console, state.game_title)

    while not check_game_over(state):
        try:
            active_console.clear()
        except Exception:
            pass

        render_game_screen(active_console, state, outlook_lines=build_week_outlook(state, content), recent_log_limit=8)
        choice = active_console.input("Choose an action: ").strip().lower()

        if choice == "1":
            state = advance_week(
                state,
                content,
                action="work",
                optional_expense_resolver=lambda expense: _prompt_optional_expense_decision(active_console, expense),
                choice_resolver=lambda event: _prompt_event_choice(active_console, event),
            )
            save_game(state, content.config.autosave_name, saves_dir=saves_dir)
        elif choice == "2":
            state = advance_week(
                state,
                content,
                action="rest",
                optional_expense_resolver=lambda expense: _prompt_optional_expense_decision(active_console, expense),
                choice_resolver=lambda event: _prompt_event_choice(active_console, event),
            )
            save_game(state, content.config.autosave_name, saves_dir=saves_dir)
        elif choice == "3":
            state = _prompt_location_move(active_console, content, state)
            state = _finalize_state(state, content.config.message_log_limit)
        elif choice == "4":
            state = _prompt_job_switch(active_console, content, state)
            state = _finalize_state(state, content.config.message_log_limit)
        elif choice == "5":
            state = _prompt_item_purchase(active_console, content, state)
            state = _finalize_state(state, content.config.message_log_limit)
        elif choice == "6":
            save_game(state, content.config.autosave_name, saves_dir=saves_dir)
            active_console.print("Game saved. Exiting.")
            return state
        else:
            state = state.model_copy(update={"message_log": [*state.message_log, "Unknown menu choice."]})
            state = _finalize_state(state, content.config.message_log_limit)

    score = calculate_final_score(state, content.scoring)
    render_final_summary(active_console, state, score)
    if state.current_week > state.term_weeks and state.game_over_reason is None:
        active_console.print("You made it through the term.")
    return state
