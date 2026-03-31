from __future__ import annotations

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import EventDefinition, FinalScoreSummary, GameState, ItemDefinition, JobDefinition, LocationDefinition


def render_title_screen(console: Console, title: str) -> None:
    console.print(Panel.fit(title, title="Welcome", border_style="cyan"))


def render_summary(console: Console, state: GameState) -> None:
    table = Table(title="Current Summary")
    table.add_column("Field")
    table.add_column("Value", justify="right")
    table.add_row("Week", f"{state.current_week}/{state.term_weeks}")
    table.add_row("Difficulty", state.difficulty_id)
    table.add_row("Player", state.player.name)
    table.add_row("Cash", str(state.player.cash))
    table.add_row("Savings", str(state.player.savings))
    table.add_row("Debt", str(state.player.debt))
    table.add_row("Stress", str(state.player.stress))
    table.add_row("Energy", str(state.player.energy))
    table.add_row("Low Energy Streak", str(state.consecutive_low_energy_weeks))
    table.add_row("Essential Misses", str(state.missed_essential_weeks))
    table.add_row("Location", state.player.location_id)
    table.add_row("Job", state.player.job_id or "None")
    active_effects = ", ".join(
        f"{effect.label} ({effect.remaining_weeks}w)" for effect in state.temporary_effects
    ) or "None"
    table.add_row("Temporary Effects", active_effects)
    console.print(table)


def render_message_log(console: Console, messages: list[str]) -> None:
    if not messages:
        console.print(Panel("No messages yet.", title="Message Log"))
        return
    log_text = "\n".join(f"- {message}" for message in messages)
    console.print(Panel(log_text, title="Message Log"))


def render_actions(console: Console) -> None:
    console.print(
        Panel(
            "1. Work week\n2. Rest week\n3. Move location\n4. Switch job\n5. Buy item\n6. Save and quit",
            title="Actions",
            border_style="green",
        )
    )


def render_game_screen(
    console: Console,
    state: GameState,
    *,
    outlook_lines: list[str],
    recent_log_limit: int = 8,
) -> None:
    resource_table = Table(show_header=False, box=None, pad_edge=False)
    resource_table.add_column("Field")
    resource_table.add_column("Value", justify="right")
    resource_table.add_row("Week", f"{state.current_week}/{state.term_weeks}")
    resource_table.add_row("Difficulty", state.difficulty_id)
    resource_table.add_row("Cash", str(state.player.cash))
    resource_table.add_row("Savings", str(state.player.savings))
    resource_table.add_row("Debt", str(state.player.debt))
    resource_table.add_row("Stress", str(state.player.stress))
    resource_table.add_row("Energy", str(state.player.energy))
    resource_table.add_row("Low Energy Streak", str(state.consecutive_low_energy_weeks))
    resource_table.add_row("Essential Misses", str(state.missed_essential_weeks))

    active_effects = ", ".join(
        f"{effect.label} ({effect.remaining_weeks}w)" for effect in state.temporary_effects
    ) or "None"
    context_text = (
        f"Player: {state.player.name}\n"
        f"Location: {state.player.location_id}\n"
        f"Job: {state.player.job_id or 'None'}\n"
        f"Temporary: {active_effects}"
    )
    outlook_text = "\n".join(f"- {line}" for line in outlook_lines) if outlook_lines else "- No major signals this week."

    recent_messages = state.message_log[-recent_log_limit:]
    log_text = "\n".join(f"- {message}" for message in recent_messages) if recent_messages else "- No recent activity."

    actions_text = (
        "1. Work week\n"
        "2. Rest week\n"
        "3. Move location\n"
        "4. Switch job\n"
        "5. Buy item\n"
        "6. Save and quit"
    )

    console.print(Panel.fit(state.game_title, title="Student Budget Wars", border_style="cyan"))
    console.print(
        Columns(
            [
                Panel(resource_table, title="Status", border_style="blue"),
                Panel(context_text, title="Position", border_style="magenta"),
            ],
            equal=True,
            expand=True,
        )
    )
    console.print(
        Columns(
            [
                Panel(outlook_text, title="Week Outlook", border_style="yellow"),
                Panel(log_text, title=f"Recent Activity ({len(recent_messages)})", border_style="green"),
            ],
            equal=True,
            expand=True,
        )
    )
    console.print(Panel(actions_text, title="Actions", border_style="white"))


def render_item_shop(console: Console, items: list[ItemDefinition]) -> None:
    table = Table(title="Item Shop")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Price", justify="right")
    table.add_column("Effect")
    for item in items:
        effect_text = ", ".join(f"{key} {value:+d}" for key, value in item.effects.items()) or "None"
        table.add_row(item.id, item.name, str(item.price), effect_text)
    console.print(table)


def render_job_options(console: Console, jobs: list[JobDefinition], current_job_id: str | None) -> None:
    table = Table(title="Switch Job")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Pay", justify="right")
    table.add_column("Hours", justify="right")
    table.add_column("Energy", justify="right")
    table.add_column("Stress", justify="right")
    table.add_column("Location")
    for job in jobs:
        marker = " (current)" if job.id == current_job_id else ""
        table.add_row(
            job.id,
            f"{job.name}{marker}",
            str(job.hourly_pay),
            str(job.hours_per_week),
            str(job.energy_cost),
            str(job.stress_delta),
            job.location_id,
        )
    console.print(table)


def render_location_options(
    console: Console,
    locations: list[LocationDefinition],
    current_location_id: str | None,
) -> None:
    table = Table(title="Move Location")
    table.add_column("Id")
    table.add_column("Name")
    table.add_column("Modifiers")
    table.add_column("Notes")
    for location in locations:
        marker = " (current)" if location.id == current_location_id else ""
        modifier_text = ", ".join(f"{key} {value:+d}" for key, value in location.modifiers.items()) or "none"
        table.add_row(
            location.id,
            f"{location.name}{marker}",
            modifier_text,
            location.description,
        )
    console.print(table)


def render_event(console: Console, event: EventDefinition) -> None:
    body = event.description
    if event.choices:
        lines = [body, ""]
        for index, choice in enumerate(event.choices, start=1):
            lines.append(f"{index}. {choice.label} - {choice.description}")
        body = "\n".join(lines)
    console.print(Panel(body, title=event.name, border_style="magenta"))


def render_final_summary(console: Console, state: GameState, score: FinalScoreSummary) -> None:
    render_summary(console, state)
    table = Table(title="Final Score")
    table.add_column("Part")
    table.add_column("Value", justify="right")
    for key, value in score.breakdown.items():
        table.add_row(key, f"{value:.1f}")
    table.add_row("final_score", f"{score.final_score:.1f}")
    table.add_row("outcome", score.outcome)
    console.print(table)
    if state.game_over_reason:
        console.print(Panel(state.game_over_reason, title="Run Ended", border_style="red"))
