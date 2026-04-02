from __future__ import annotations

from pathlib import Path

import pytest

from budgetwars.core import GameSession, StartupOptions
from budgetwars.games.desktop.app import DesktopShellApp


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _build_app() -> DesktopShellApp:
    session = GameSession.from_startup_options(
        StartupOptions(mode="desktop", player_name="WindowTester"),
        root=PROJECT_ROOT,
    )
    return DesktopShellApp(session)


def _reset_app(app: DesktopShellApp) -> None:
    for app_id in list(app.open_windows):
        app.close_window(app_id)
    app.active_app = ""
    app.browser_page = "jobs"
    app.profile_tab = "info"
    app.mail_index = 0
    app.open_app("mail")


@pytest.fixture(scope="module")
def app() -> DesktopShellApp:
    desktop = _build_app()
    yield desktop
    desktop.root.destroy()


def _iter_widgets(root):
    for child in root.winfo_children():
        yield child
        yield from _iter_widgets(child)


def _compact_menu_labels(app: DesktopShellApp, app_id: str, menu_caption: str) -> list[str]:
    window = app.open_windows[app_id]
    for widget in _iter_widgets(window.host):
        if widget.winfo_class() == "Menubutton" and menu_caption in widget.cget("text"):
            menu_name = widget.cget("menu")
            menu = widget.nametowidget(menu_name)
            end = menu.index("end")
            if end is None:
                return []
            labels: list[str] = []
            for index in range(end + 1):
                if menu.type(index) != "separator":
                    labels.append(menu.entrycget(index, "label"))
            return labels
    return []


def test_open_app_reuses_existing_window_and_activates(app: DesktopShellApp):
    _reset_app(app)
    mail_window = app.open_windows["mail"].toplevel
    app.open_app("mail")
    assert app.open_windows["mail"].toplevel is mail_window
    assert app.active_app == "mail"


def test_focusing_background_window_updates_active_state(app: DesktopShellApp):
    _reset_app(app)
    app.open_app("profile")
    app.open_app("bank")
    app._focus_window("profile")
    assert app.active_app == "profile"
    assert app.open_windows["profile"].task_button.cget("bg") == "#3f86f4"
    assert app.open_windows["bank"].task_button.cget("bg") == "#2e69db"


def test_global_click_on_background_window_widget_activates_it(app: DesktopShellApp):
    _reset_app(app)
    app.open_app("profile")
    app.open_app("bank")
    profile_host = app.open_windows["profile"].host

    class _Event:
        pass

    event = _Event()
    event.widget = profile_host
    app._on_global_pointer_down(event)
    assert app.active_app == "profile"
    assert app.open_windows["profile"].task_button.cget("bg") == "#3f86f4"
    assert app.open_windows["bank"].task_button.cget("bg") == "#2e69db"


def test_compact_menus_share_same_action_set_as_toolbar_registry(app: DesktopShellApp):
    _reset_app(app)
    app.open_app("bank")
    bank = app.open_windows["bank"]
    bank.size = (700, 540)
    bank.normal_size = bank.size
    app._apply_window_geometry(bank)
    app.render_bank("bank")
    bank_compact = _compact_menu_labels(app, "bank", "Bank Menu")
    assert bank_compact == [action.label for action in app._bank_toolbar_actions()]

    app.open_app("mail")
    mail = app.open_windows["mail"]
    mail.size = (680, 560)
    mail.normal_size = mail.size
    app._apply_window_geometry(mail)
    app.render_mail("mail")
    mail_compact = _compact_menu_labels(app, "mail", "Mail Menu")
    assert mail_compact == [action.label for action in app._mail_toolbar_actions()]


def test_taskbar_minimize_and_restore_is_deterministic(app: DesktopShellApp):
    _reset_app(app)
    app.open_app("profile")
    app.toggle_task_window("profile")
    assert app.open_windows["profile"].minimized is True
    app.toggle_task_window("profile")
    assert app.open_windows["profile"].minimized is False
    assert app.active_app == "profile"


def test_tile_windows_stays_within_desktop_bounds(app: DesktopShellApp):
    _reset_app(app)
    app.open_app("profile")
    app.open_app("bank")
    app.open_app("browser")
    app.tile_open_windows()
    app.root.update_idletasks()

    origin_x, origin_y = app._desktop_origin()
    desktop_width, desktop_height = app._desktop_bounds()
    max_x = origin_x + desktop_width
    max_y = origin_y + desktop_height

    for window in app.open_windows.values():
        if window.minimized:
            continue
        left = window.toplevel.winfo_x()
        top = window.toplevel.winfo_y()
        right = left + window.toplevel.winfo_width()
        bottom = top + window.toplevel.winfo_height()
        assert left >= origin_x
        assert top >= origin_y
        assert right <= max_x
        assert bottom <= max_y
