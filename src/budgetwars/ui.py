from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import EventDefinition, FinalScoreSummary, GameState, ItemDefinition


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
            "1. Work week\n2. Rest week\n3. Buy item\n4. Save and quit",
            title="Actions",
            border_style="green",
        )
    )


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
