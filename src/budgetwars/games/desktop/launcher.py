from __future__ import annotations

from pathlib import Path

from budgetwars.core import GameSession, StartupOptions

from .app import DesktopShellApp


def build_desktop_session(options: StartupOptions, *, root: Path | None = None) -> GameSession:
    session = GameSession.from_startup_options(options.with_mode("desktop"), root=root)
    session.ensure_started(default_player_name=options.player_name or "DesktopPlayer")
    return session


def run_desktop(options: StartupOptions, *, root: Path | None = None) -> None:
    session = build_desktop_session(options, root=root)
    DesktopShellApp(session, startup_options=options.with_mode("desktop")).run()
