from __future__ import annotations

import pytest

from budgetwars.games.classic.ui import choice_previews, diagnostics, setup_dialog, view_builders, view_models
from budgetwars.games.classic.ui.main_window import MainWindow


def test_phase0_module_smoke_imports_and_builds_main_window(controller_factory):
    assert hasattr(view_models, "BuildSnapshotVM")
    assert hasattr(view_builders, "_resolve_context")
    assert hasattr(choice_previews, "_career_preview")
    assert hasattr(diagnostics, "_build_crisis_warnings")
    assert hasattr(setup_dialog, "compute_setup_dialog_geometry")

    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()

    controller = controller_factory()

    class _SessionStub:
        def require_controller(self):
            return controller

        def autosave(self):
            return None

        def refresh_bundle(self):
            return controller.bundle

        def start_new_game(self, *_args, **_kwargs):
            return None

        def save_named(self, *_args, **_kwargs):
            return None

    try:
        window = MainWindow(root, _SessionStub())
        window.update_idletasks()
        assert window.life_panel is not None
        assert window.outlook_panel is not None
        assert window.finance_panel is not None
    finally:
        if "window" in locals():
            window.destroy()
        root.destroy()
