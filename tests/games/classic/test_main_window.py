from __future__ import annotations

import pytest

from budgetwars.engine.status_arcs import start_status_arc
from budgetwars.games.classic.ui.main_window import (
    ActionsPanel,
    ClassicSetupDialog,
    MainWindow,
    compute_setup_dialog_geometry,
    build_build_snapshot,
    build_learn_drawer,
    build_monthly_forecast,
    build_pressure_summary,
    build_score_delta_summary,
    _budget_preview,
    _career_preview,
    _career_branch_preview,
    _focus_preview,
    _housing_preview,
    _transport_preview,
    _wealth_preview,
    should_use_compact_layout,
)
from budgetwars.games.classic.ui.panes.life_panel import LifePanel
from budgetwars.games.classic.ui.panes.finance_panel import FinancePanel
from budgetwars.games.classic.ui.panes.outlook_panel import OutlookPanel
from budgetwars.games.classic.ui.panes.event_popup import preview_choice_detail
from budgetwars.games.classic.ui.panes.menu_bar import (
    build_menu_bar,
    configure_dark_combobox_style,
    configure_dark_menu_style,
)
from budgetwars.models import LiveScoreSnapshot


def test_build_snapshot_returns_structured_items(controller_factory):
    controller = controller_factory()

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert snapshot.player_name == controller.state.player.name
    assert snapshot.city_name
    assert [item.label for item in snapshot.items] == [
        "Career",
        "Education",
        "Housing",
        "Transport",
        "Wealth",
        "Focus",
    ]
    assert snapshot.items[0].value
    assert snapshot.items[0].detail is not None
    assert not isinstance(snapshot.items[0], str)


def test_build_snapshot_exposes_progress_signals(controller_factory):
    controller = controller_factory()

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert any(item.progress for item in snapshot.items)
    assert snapshot.items[0].progress is not None
    assert "Progress" in snapshot.items[0].progress


def test_build_snapshot_surfaces_branch_identity(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    controller.state.player.career.tier_index = 2
    controller.state.player.career.branch_id = "warehouse_dispatch_track"

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert hasattr(snapshot, "identity_line")
    assert snapshot.identity_line is not None
    assert "Dispatch Coordination" in snapshot.identity_line
    assert "Warehouse / Logistics" in snapshot.identity_line


def test_build_snapshot_surfaces_persistent_commitments(controller_factory):
    controller = controller_factory()
    controller.state.player.persistent_tags = ["scope_push_lane", "dispatch_command_lane"]

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert hasattr(snapshot, "persistent_commitments")
    assert "Scope Push Lane" in snapshot.persistent_commitments
    assert "Dispatch Command Lane" in snapshot.persistent_commitments


def test_build_snapshot_surfaces_late_career_band(controller_factory):
    controller = controller_factory(opening_path_id="full_time_work")
    controller.state.player.career.track_id = "office_admin"
    controller.state.player.career.tier_index = 4
    controller.state.player.career.branch_id = "office_operations_track"
    controller.state.player.career.role_band_id = "stretch_scope_band"
    controller.state.player.career.post_cap_advancement_level = 2

    snapshot = build_build_snapshot(controller.state, controller.bundle)

    assert "Ops Scope Owner" in snapshot.identity_line
    assert "Late-career" in snapshot.items[0].progress


def test_monthly_forecast_exposes_named_sections(controller_factory):
    controller = controller_factory()

    forecast = build_monthly_forecast(controller.state, controller.bundle)

    assert forecast.monthly_focus
    assert forecast.main_threat
    assert forecast.best_opportunity
    assert forecast.chosen_focus
    assert forecast.expected_swing
    assert forecast.situation_family
    assert forecast.credit_status
    assert forecast.progress_label
    assert forecast.progress_detail
    assert 0.0 <= forecast.progress_fraction <= 1.0
    assert isinstance(forecast.driver_notes, list)


def test_monthly_forecast_surfaces_persistent_commitments(controller_factory):
    controller = controller_factory()
    controller.state.player.persistent_tags = ["consistency_lane"]

    forecast = build_monthly_forecast(controller.state, controller.bundle)

    assert hasattr(forecast, "persistent_commitments")
    assert "Consistency Lane" in forecast.persistent_commitments


def test_monthly_forecast_surfaces_top_active_status_arcs(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    start_status_arc(
        controller.bundle,
        controller.state,
        "credit_squeeze",
        source_event_id="collections_warning",
        duration_months=4,
        severity=2,
    )

    forecast = build_monthly_forecast(controller.state, controller.bundle)

    assert hasattr(forecast, "active_status_arcs")
    assert forecast.active_status_arcs
    assert forecast.active_status_arcs[0].name == "Credit Squeeze"
    assert forecast.active_status_arcs[0].severity == 2
    assert forecast.active_status_arcs[0].months_remaining == 4
    assert forecast.active_status_arcs[0].resolution_hint


def test_pressure_summary_surfaces_persistent_commitments(controller_factory):
    controller = controller_factory()
    controller.state.player.persistent_tags = ["dispatch_command_lane", "office_scope_lane"]

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert hasattr(summary, "persistent_commitments")
    assert "Dispatch Command Lane" in summary.persistent_commitments
    assert "Office Scope Lane" in summary.persistent_commitments


def test_pressure_summary_uses_active_status_arcs_for_diagnosis(controller_factory):
    controller = controller_factory(opening_path_id="college_university")
    controller.state.player.education.program_id = "full_time_university"
    controller.state.player.education.is_active = True
    start_status_arc(
        controller.bundle,
        controller.state,
        "education_slipping",
        source_event_id="overtime_exam_collision",
        duration_months=3,
        severity=2,
    )

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert hasattr(summary, "active_status_arcs")
    assert summary.active_status_arcs
    assert summary.active_status_arcs[0].name == "Education Slipping"
    assert "education slipping" in summary.run_killer.lower()
    assert "reduce intensity" in summary.fastest_fix.lower() or "protect" in summary.fastest_fix.lower()


def test_monthly_forecast_surfaces_recovery_route(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.stress = 81
    controller.state.player.social_stability = 82
    controller.state.player.family_support = 70
    controller.state.player.last_social_lifeline_year = 0

    forecast = build_monthly_forecast(controller.state, controller.bundle)

    assert hasattr(forecast, "recovery_route")
    assert forecast.recovery_route is not None
    assert "network" in forecast.recovery_route.lower()


def test_pressure_summary_prioritizes_key_metrics(controller_factory):
    controller = controller_factory()

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert summary.projected_score >= 0
    assert summary.score_tier
    assert summary.biggest_risk
    assert summary.credit_score >= 300
    assert summary.credit_tier
    assert summary.credit_progress_label
    assert summary.credit_progress_detail
    assert 0.0 <= summary.credit_progress_fraction <= 1.0
    assert [metric.label for metric in summary.primary_metrics][:3] == [
        "Cash",
        "Savings",
        "Debt",
    ]
    assert summary.progress_label
    assert summary.progress_detail
    assert 0.0 <= summary.progress_fraction <= 1.0
    assert summary.active_modifiers is not None
    assert summary.crisis_watch is not None


def test_pressure_summary_surfaces_blocked_doors(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 690
    controller.state.player.debt = 16500
    controller.state.player.monthly_surplus = -120

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert hasattr(summary, "blocked_doors")
    assert any("solo rental" in line.lower() for line in summary.blocked_doors)
    assert any("financed car" in line.lower() for line in summary.blocked_doors)


def test_pressure_summary_surfaces_consequence_signals(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.pending_events.append(controller.bundle.events[0])
    controller.state.pending_user_choice_event = controller.bundle.events[0]
    controller.state.pending_user_choice_event_id = controller.bundle.events[0].id
    controller.state.month_driver_notes = ["Housing squeeze is dominating this month."]

    summary = build_pressure_summary(controller.state, controller.bundle)

    assert summary.pressure_family
    assert "housing squeeze" in summary.month_driver.lower()
    assert summary.pending_fallout_count >= 1
    assert any("situation choice pending" in line.lower() for line in summary.pending_decisions)


def test_learn_drawer_surfaces_topics_and_pressure_sources(controller_factory):
    controller = controller_factory()

    vm = build_learn_drawer(controller.state, controller.bundle)

    assert vm.active_pressure_family
    assert vm.credit_line
    assert vm.stress_line
    assert vm.pressure_sources
    topic_ids = {topic.id for topic in vm.topics}
    assert {"credit", "stress", "housing", "transport", "career", "education"} <= topic_ids


def test_action_choice_previews_mention_likely_changes(controller_factory):
    controller = controller_factory()

    career = controller.bundle.careers[0]
    branch = controller.bundle.careers[0].branches[0]
    housing = controller.bundle.housing_options[0]
    transport = controller.bundle.transport_options[0]
    budget = controller.bundle.config.budget_stances[0]
    wealth = controller.bundle.wealth_strategies[0]
    focus = controller.bundle.focus_actions[0]

    assert "Likely changes:" in _career_preview(career)
    assert "Likely changes:" in _career_branch_preview(branch)
    assert "Likely changes:" in _housing_preview(housing)
    assert "Likely changes:" in _transport_preview(transport, transport.upfront_cost, transport.monthly_payment + transport.insurance_cost + transport.fuel_maintenance_cost)
    assert "Likely changes:" in _budget_preview(budget)
    assert "Likely changes:" in _wealth_preview(wealth)
    assert "Likely changes:" in _focus_preview(focus)


def test_education_intensity_options_include_preview_language(controller_factory):
    controller = controller_factory()
    window = object.__new__(MainWindow)
    window.session = type("Session", (), {"require_controller": lambda self=None: controller})()

    options = MainWindow._education_intensity_options(window)

    assert any("Likely changes:" in detail for _, _, detail in options)
    assert any(label == "Standard" for label, _, _ in options)


def test_event_choice_preview_language_reflects_stat_effects():
    detail = preview_choice_detail("Take the repair hit now", {"stress": -2, "cash": -150})

    assert "Likely changes:" in detail
    assert "stress -2" in detail
    assert "cash -150" in detail


def test_score_delta_summary_compares_current_and_previous_snapshots():
    previous = LiveScoreSnapshot(
        projected_score=45.0,
        score_tier="Silver",
        biggest_risk="Debt pressure is still the softest part of the run.",
        breakdown={
            "net_worth": 38.0,
            "monthly_surplus": 62.0,
            "debt_ratio": 41.0,
            "career_tier": 55.0,
            "credentials_education": 49.0,
            "housing_stability": 58.0,
            "life_satisfaction": 44.0,
            "stress_burnout": 36.0,
        },
    )
    current = LiveScoreSnapshot(
        projected_score=52.5,
        score_tier="Silver",
        biggest_risk="Debt pressure is still the softest part of the run.",
        breakdown={
            "net_worth": 42.0,
            "monthly_surplus": 66.0,
            "debt_ratio": 48.0,
            "career_tier": 57.0,
            "credentials_education": 50.0,
            "housing_stability": 60.0,
            "life_satisfaction": 47.0,
            "stress_burnout": 39.0,
        },
    )

    delta = build_score_delta_summary(previous, current)

    assert delta.previous_score == 45.0
    assert delta.current_score == 52.5
    assert delta.delta == 7.5
    assert delta.strongest_category
    assert delta.weakest_category
    assert delta.diagnosis


def test_run_feedback_lines_surface_recovery_without_repeating_blocked_doors(controller_factory):
    controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
    controller.state.player.credit_score = 690
    controller.state.player.debt = 16500
    controller.state.player.monthly_surplus = -120
    controller.state.player.stress = 81
    controller.state.player.social_stability = 82
    controller.state.player.family_support = 70
    controller.state.player.last_social_lifeline_year = 0

    window = object.__new__(MainWindow)
    window.session = type("Session", (), {"require_controller": lambda self=None: controller})()
    window._latest_snapshot = controller.live_score_snapshot()

    lines = MainWindow._run_feedback_lines(window)

    assert any("recovery route:" in line.lower() for line in lines)
    assert not any("blocked door:" in line.lower() for line in lines)


def test_run_feedback_lines_surface_month_driver_and_pending_fallout(controller_factory):
    controller = controller_factory()
    controller.state.month_driver_notes = ["Debt anxiety is rising and crowding out flexibility."]
    controller.state.pending_events.append(controller.bundle.events[0])
    controller.state.pending_user_choice_event = controller.bundle.events[0]
    controller.state.pending_user_choice_event_id = controller.bundle.events[0].id

    window = object.__new__(MainWindow)
    window.session = type("Session", (), {"require_controller": lambda self=None: controller})()
    window._latest_snapshot = controller.live_score_snapshot()

    lines = MainWindow._run_feedback_lines(window)

    assert any("month driver:" in line.lower() for line in lines)
    assert any("pending fallout:" in line.lower() for line in lines)
    assert any("situation choice pending:" in line.lower() for line in lines)


def test_dark_combobox_style_prefers_light_text():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.withdraw()
    try:
        style_name = configure_dark_combobox_style(root)
        style = ttk.Style(root)
        assert style.lookup(style_name, "foreground", ("readonly",)) == "#f0eadb"
        assert style.lookup(style_name, "fieldbackground", ("readonly",)) == "#243446"
    finally:
        root.destroy()


def test_dark_menu_style_uses_light_foreground():
    class FakeMenu:
        def __init__(self) -> None:
            self.options: dict[str, str | int | bool] = {}

        def configure(self, **kwargs):
            self.options.update(kwargs)

        def cget(self, key: str):
            return self.options[key]

    menu = FakeMenu()
    configure_dark_menu_style(menu)

    assert menu.cget("fg") == "#f0eadb"
    assert menu.cget("activeforeground") == "#f0eadb"
    assert menu.cget("bg") == "#0b1016"


def test_menu_bar_exposes_learn_action():
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        menu = build_menu_bar(
            root,
            {
                "new_game": lambda: None,
                "save": lambda: None,
                "exit": lambda: None,
                "career": lambda: None,
                "education": lambda: None,
                "housing": lambda: None,
                "transport": lambda: None,
                "budget": lambda: None,
                "wealth": lambda: None,
                "focus": lambda: None,
                "resolve": lambda: None,
                "text_size": lambda: None,
                "compact_layout": lambda: None,
                "score": lambda: None,
                "learn": lambda: None,
                "help": lambda: None,
            },
        )
        info_menu = root.nametowidget(menu.entrycget(3, "menu"))
        labels = [info_menu.entrycget(i, "label") for i in range(info_menu.index("end") + 1)]
        assert "Learn" in labels
    finally:
        root.destroy()


def test_build_menu_bar_includes_learn_entry(monkeypatch):
    created: list[object] = []

    class FakeMenu:
        def __init__(self, *_args, **_kwargs):
            self.entries: list[tuple[str, object, object | None]] = []
            self.options: dict[str, object] = {}
            created.append(self)

        def configure(self, **kwargs):
            self.options.update(kwargs)

        def add_command(self, *, label, command):
            self.entries.append(("command", label, command))

        def add_separator(self):
            self.entries.append(("separator", None, None))

        def add_cascade(self, *, label, menu):
            self.entries.append(("cascade", label, menu))

    monkeypatch.setattr("budgetwars.games.classic.ui.panes.menu_bar.tk.Menu", FakeMenu)

    callbacks = {
        "new_game": lambda: None,
        "save": lambda: None,
        "exit": lambda: None,
        "career": lambda: None,
        "education": lambda: None,
        "housing": lambda: None,
        "transport": lambda: None,
        "budget": lambda: None,
        "wealth": lambda: None,
        "focus": lambda: None,
        "resolve": lambda: None,
        "text_size": lambda: None,
        "compact_layout": lambda: None,
        "score": lambda: None,
        "learn": lambda: None,
        "help": lambda: None,
    }

    menu = build_menu_bar(object(), callbacks)

    info_menu = next(entry[2] for entry in menu.entries if entry[:2] == ("cascade", "Info"))
    view_menu = next(entry[2] for entry in menu.entries if entry[:2] == ("cascade", "View"))
    assert ("command", "Learn", callbacks["learn"]) in info_menu.entries
    assert ("command", "Toggle Compact Layout", callbacks["compact_layout"]) in view_menu.entries


def test_compact_layout_prefers_smaller_screens():
    assert should_use_compact_layout(1366, 768) is True
    assert should_use_compact_layout(1920, 1080) is False
    assert should_use_compact_layout(2560, 1440) is False


def test_setup_group_selection_updates_button_and_summary(monkeypatch):
    class FakeVar:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    class FakeButton:
        def __init__(self):
            self.config = {}

        def configure(self, **kwargs):
            self.config.update(kwargs)

    class FakeDialogResult:
        def __init__(self, result):
            self.result = result

    dialog = object.__new__(ClassicSetupDialog)
    dialog.master = object()
    dialog._groups_by_key = {
        "preset_id": type("Group", (), {
            "title": "Preset",
            "prompt": "Choose the background you are starting from:",
            "options": [
                ("Supported Student", "supported_student", "A balanced start."),
                ("Broke but Ambitious", "broke_but_ambitious", "A shakier start."),
            ],
        })(),
    }
    dialog._group_selection_vars = {"preset_id": FakeVar("Supported Student")}
    dialog._group_desc_vars = {"preset_id": FakeVar("A balanced start.")}
    dialog._group_buttons = {"preset_id": FakeButton()}
    dialog._value_maps = {
        "preset_id": {
            "Supported Student": ("Supported Student", "supported_student", "A balanced start."),
            "Broke but Ambitious": ("Broke but Ambitious", "broke_but_ambitious", "A shakier start."),
        }
    }
    refresh_calls = []
    dialog._refresh_summary = lambda: refresh_calls.append(True)

    monkeypatch.setattr(
        "budgetwars.games.classic.ui.main_window.SelectionDialog",
        lambda *args, **kwargs: FakeDialogResult("broke_but_ambitious"),
    )

    dialog.select_setup_group("preset_id")

    assert dialog._group_selection_vars["preset_id"].get() == "Broke but Ambitious"
    assert dialog._group_desc_vars["preset_id"].get() == "A shakier start."
    assert dialog._group_buttons["preset_id"].config["text"] == "Broke but Ambitious"
    assert refresh_calls == [True]


def test_actions_panel_layouts_stay_vertically_bounded():
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        groups = [
            ("Build", [
                ("Career", lambda: None),
                ("Education", lambda: None),
                ("Housing", lambda: None),
                ("Transport", lambda: None),
            ]),
            ("Policy", [
                ("Budget", lambda: None),
                ("Wealth", lambda: None),
            ]),
            ("This Month", [
                ("Focus", lambda: None),
                ("Resolve Month", lambda: None),
            ]),
        ]

        normal = ActionsPanel(root)
        normal.set_grouped_actions(groups)
        normal.update_idletasks()
        normal_height = normal.winfo_reqheight()

        compact = ActionsPanel(root)
        compact.set_grouped_actions(groups, compact=True)
        compact.update_idletasks()
        compact_height = compact.winfo_reqheight()

        assert normal_height <= 100
        assert compact_height <= 140
    finally:
        root.destroy()


def test_setup_dialog_geometry_is_clamped_to_parent_window():
    x, y, width, height = compute_setup_dialog_geometry(
        parent_x=100,
        parent_y=50,
        parent_width=1600,
        parent_height=900,
        screen_width=1920,
        screen_height=1080,
    )

    assert width <= 1600 - 48
    assert height <= 900 - 48
    assert x >= 100
    assert y >= 50


def test_compact_action_groups_keep_focus_and_resolve():
    window = object.__new__(MainWindow)
    window.session = type(
        "Session",
        (),
        {
            "require_controller": lambda self=None: type(
                "Controller",
                (),
                {
                    "available_win_states": lambda self=None: [],
                },
            )(),
        },
    )()

    groups = MainWindow._build_action_groups(window, compact=True)

    assert [name for name, _ in groups[-1][1]] == ["Focus", "Resolve Month"]


def test_toggle_compact_layout_flips_manual_override():
    window = object.__new__(MainWindow)
    window._compact_layout_auto = False
    window._compact_layout_override = None
    window.master = type("Master", (), {"winfo_width": lambda self=None: 2560, "winfo_height": lambda self=None: 1440})()
    refresh_calls = []
    window.refresh = lambda: refresh_calls.append(True)

    MainWindow.toggle_compact_layout(window)
    assert window._compact_layout_override is True

    MainWindow.toggle_compact_layout(window)
    assert window._compact_layout_override is False
    assert len(refresh_calls) == 2


def test_show_learn_toggles_drawer_and_renders_content(controller_factory):
    class FakeLearnDrawer:
        def __init__(self) -> None:
            self.exists = True
            self.rendered = None
            self.focused = False
            self.destroyed = False

        def render(self, drawer) -> None:
            self.rendered = drawer

        def focus_force(self) -> None:
            self.focused = True

        def winfo_exists(self) -> bool:
            return self.exists

        def destroy(self) -> None:
            self.destroyed = True
            self.exists = False

    window = object.__new__(MainWindow)
    controller = controller_factory()
    window.session = type("Session", (), {"require_controller": lambda self=None: controller})()
    window.master = object()
    window._learn_visible = False
    window._learn_drawer = None

    created: list[FakeLearnDrawer] = []

    def make_drawer(*_args, **_kwargs):
        drawer = FakeLearnDrawer()
        created.append(drawer)
        return drawer

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("budgetwars.games.classic.ui.main_window.LearnDrawer", make_drawer)
    try:
        MainWindow.show_learn(window)

        assert window._learn_visible is True
        assert created
        assert created[0].rendered is not None
        assert created[0].focused is True

        MainWindow.show_learn(window)

        assert window._learn_visible is False
        assert window._learn_drawer is None
        assert created[0].destroyed is True
    finally:
        monkeypatch.undo()


def test_life_panel_rerender_does_not_duplicate_build_subtitle(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory()
        panel = LifePanel(root)
        snapshot = build_build_snapshot(controller.state, controller.bundle)
        panel.render_snapshot(snapshot)
        panel.render_snapshot(snapshot)

        labels = [
            child.cget("text")
            for child in panel._scroll_frame.winfo_children()
            if isinstance(child, tk.Label)
        ]
        assert labels.count(snapshot.identity_line) == 1
    finally:
        root.destroy()


def test_finance_panel_compact_limits_commitment_chips_with_overflow_note(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory()
        controller.state.player.persistent_tags = [
            "scope_push_lane",
            "consistency_lane",
            "dispatch_command_lane",
            "office_scope_lane",
            "healthcare_continuity_lane",
            "trades_precision_schedule_lane",
        ]
        summary = build_pressure_summary(controller.state, controller.bundle)
        panel = FinancePanel(root)
        panel.render_summary(summary, compact=True)

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert "Committed Lanes" in texts
        assert "Scope Push Lane" in texts
        assert "Consistency Lane" in texts
        assert "Dispatch Command Lane" not in texts
        assert "+4 more" in texts
    finally:
        root.destroy()


def test_finance_panel_desktop_shows_more_commitment_chips_with_overflow_note(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory()
        controller.state.player.persistent_tags = [
            "scope_push_lane",
            "consistency_lane",
            "dispatch_command_lane",
            "office_scope_lane",
            "healthcare_continuity_lane",
            "trades_precision_schedule_lane",
        ]
        summary = build_pressure_summary(controller.state, controller.bundle)
        panel = FinancePanel(root)
        panel.render_summary(summary, compact=False)

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert "Committed Lanes" in texts
        assert "Scope Push Lane" in texts
        assert "Consistency Lane" in texts
        assert "Dispatch Command Lane" in texts
        assert "Office Scope Lane" in texts
        assert "Healthcare Continuity Lane" not in texts
        assert "+2 more" in texts
    finally:
        root.destroy()


def test_outlook_panel_renders_active_status_arcs(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory(opening_path_id="full_time_work")
        controller.state.player.transport.option_id = "beater_car"
        start_status_arc(
            controller.bundle,
            controller.state,
            "transport_unstable",
            source_event_id="car_repair",
            duration_months=3,
            severity=2,
        )
        panel = OutlookPanel(root, resolve_callback=lambda: None)
        panel.render_forecast(
            build_monthly_forecast(controller.state, controller.bundle),
            compact=False,
            show_resolve_button=False,
        )

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert any(text in {"Active Arcs", "ACTIVE ARC"} for text in texts)
        assert any("Transport Unstable" in text for text in texts)
    finally:
        root.destroy()


def test_phase_status_arc_outlook_panel_promotes_top_arc_as_hero_context(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory(opening_path_id="full_time_work")
        start_status_arc(
            controller.bundle,
            controller.state,
            "burnout_risk",
            source_event_id="overtime_attrition_warning",
            duration_months=3,
            severity=2,
        )
        panel = OutlookPanel(root, resolve_callback=lambda: None)
        panel.render_forecast(
            build_monthly_forecast(controller.state, controller.bundle),
            compact=False,
            show_resolve_button=False,
        )

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert "ACTIVE ARC" in texts
        assert any("Burnout Risk" in text for text in texts)
    finally:
        root.destroy()


def test_finance_panel_renders_active_status_arc_section(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
        start_status_arc(
            controller.bundle,
            controller.state,
            "credit_squeeze",
            source_event_id="collections_warning",
            duration_months=4,
            severity=2,
        )
        summary = build_pressure_summary(controller.state, controller.bundle)
        panel = FinancePanel(root)
        panel.render_summary(summary, compact=False)

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert "Active Arcs" in texts
        assert any("Credit Squeeze" in text for text in texts)
    finally:
        root.destroy()


def test_phase_status_arc_pressure_summary_prefers_arc_diagnosis_and_trims_generic_signals(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
        controller.state.player.housing.option_id = "solo_rental"
        controller.state.player.housing.housing_stability = 34
        controller.state.player.credit_score = 556
        controller.state.player.debt = 12200
        controller.state.player.monthly_surplus = -220
        start_status_arc(
            controller.bundle,
            controller.state,
            "lease_pressure",
            source_event_id="lease_default_warning",
            duration_months=4,
            severity=2,
        )
        summary = build_pressure_summary(controller.state, controller.bundle)
        panel = FinancePanel(root)
        panel.render_summary(summary, compact=False)

        def _all_label_texts(widget: tk.Widget) -> list[str]:
            texts: list[str] = []
            for child in widget.winfo_children():
                if isinstance(child, tk.Label):
                    texts.append(child.cget("text"))
                texts.extend(_all_label_texts(child))
            return texts

        texts = _all_label_texts(panel)
        assert summary.biggest_risk == "Lease Pressure"
        assert "Risk: Lease Pressure" in texts
        assert not any(text.startswith("Pressure family:") for text in texts)
    finally:
        root.destroy()


def test_phase8_default_layout_hides_primary_panel_scrollbars(controller_factory):
    import tkinter as tk

    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is unavailable in this environment")
    root.withdraw()
    try:
        root.geometry("1700x980")
        host = tk.Frame(root)
        host.pack(fill="both", expand=True)
        host.grid_columnconfigure(0, weight=1)
        host.grid_columnconfigure(1, weight=1)
        host.grid_columnconfigure(2, weight=1)
        host.grid_rowconfigure(0, weight=1)

        controller = controller_factory(opening_path_id="move_out_immediately", city_id="mid_size_city")
        controller.state.player.credit_score = 680
        controller.state.player.debt = 5200
        controller.state.player.monthly_surplus = 180
        controller.state.player.stress = 52
        controller.state.player.energy = 60

        life_panel = LifePanel(host)
        life_panel.grid(row=0, column=0, sticky="nsew")
        life_panel.render_snapshot(build_build_snapshot(controller.state, controller.bundle), compact=False)

        outlook_panel = OutlookPanel(host, resolve_callback=lambda: None)
        outlook_panel.grid(row=0, column=1, sticky="nsew")
        outlook_panel.render_forecast(
            build_monthly_forecast(controller.state, controller.bundle),
            compact=False,
            show_resolve_button=False,
        )

        finance_panel = FinancePanel(host)
        finance_panel.grid(row=0, column=2, sticky="nsew")
        finance_panel.render_summary(
            build_pressure_summary(controller.state, controller.bundle),
            compact=False,
        )

        root.update_idletasks()

        assert not life_panel._scrollbar.winfo_ismapped()
        assert not outlook_panel._scrollbar.winfo_ismapped()
        assert not finance_panel._scrollbar.winfo_ismapped()
    finally:
        root.destroy()
