from __future__ import annotations

from pathlib import Path

from budgetwars.core import GameSession, StartupOptions

from .ui import BudgetWarsTkApp


def build_classic_session(options: StartupOptions, *, root: Path | None = None) -> GameSession:
    return GameSession.from_startup_options(options.with_mode("classic"), root=root)


def run_classic(options: StartupOptions, *, root: Path | None = None) -> None:
    session = build_classic_session(options, root=root)
    BudgetWarsTkApp(session, startup_options=options.with_mode("classic")).run()
