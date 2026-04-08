# Classic Learn Drawer and Pressure Integration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Teach players how to change stats and understand pressure by adding a toggleable Learn drawer, explicit pressure/source breakdowns, and clearer situation-family feedback in Classic.

**Architecture:** Keep the existing Classic shell and engine boundaries. Add a small learn-topic content layer, then thread the same causal language through events, monthly recaps, pressure summaries, and the new Learn drawer so the UI explains the model the engine already uses.

**Tech Stack:** Python, Tkinter, Pydantic, JSON content loaders, pytest.

---

### Task 1: Add learn-topic content and model support

**Files:**
- Create: `data/learn_topics.json`
- Modify: `src/budgetwars/models/content.py`
- Modify: `src/budgetwars/loaders/content_loader.py`
- Modify: `src/budgetwars/loaders/validators.py`
- Modify: `src/budgetwars/core/content.py`
- Modify: `tests/test_content_loading.py`

**Step 1: Write the failing test**

Add a content-loading test that asserts the bundle exposes a learn-topic collection with required topics like `credit`, `stress`, `housing`, `transport`, `career`, and `education`.

```python
def test_learn_topics_load_with_required_sections(bundle):
    topic_ids = {topic.id for topic in bundle.learn_topics}
    assert {"credit", "stress", "housing", "transport", "career", "education"} <= topic_ids
```

**Step 2: Run test to verify it fails**

Run: `& .venv\Scripts\python.exe -m pytest tests/test_content_loading.py -q`

Expected: fail because `ContentBundle` does not yet expose `learn_topics`.

**Step 3: Write minimal implementation**

Add a `LearnTopicDefinition` model, include `learn_topics` on `ContentBundle`, load `data/learn_topics.json`, and validate that each topic includes:
- `id`
- `title`
- `what_it_is`
- `how_to_raise`
- `how_to_lower`
- `why_it_matters`

**Step 4: Run test to verify it passes**

Run: `& .venv\Scripts\python.exe -m pytest tests/test_content_loading.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add data/learn_topics.json src/budgetwars/models/content.py src/budgetwars/loaders/content_loader.py src/budgetwars/loaders/validators.py src/budgetwars/core/content.py tests/test_content_loading.py
git commit -m "feat: add learn topic content"
```

---

### Task 2: Make situations and pressure read as a connected model

**Files:**
- Modify: `src/budgetwars/models/content.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/game_loop.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Modify: `tests/test_consequence_depth.py`
- Modify: `tests/test_month_resolution.py`
- Modify: `tests/test_event_choices_and_win_states.py`

**Step 1: Write the failing test**

Add scenario tests that assert:
- career-specific events prefer career-related pressure when the player is in a vulnerable career lane
- housing and transport events surface their family/pressure label
- monthly recap includes a readable `pressure source` or `pressure family` line
- low credit can steer the event pool toward credit-pressure situations

Example:

```python
def test_month_recap_names_pressure_family(bundle, controller_factory):
    controller = controller_factory()
    controller.resolve_month()
    assert any("Pressure family:" in line for line in controller.state.recent_summary)
```

**Step 2: Run test to verify it fails**

Run: `& .venv\Scripts\python.exe -m pytest tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_event_choices_and_win_states.py -q`

Expected: fail because the new pressure-family language is not yet present everywhere.

**Step 3: Write minimal implementation**

Add explicit situation metadata to events:
- `family`
- `context_tags`
- `trigger_reason`
- `learn_hint`

Then add helper functions that derive:
- dominant pressure family
- top pressure sources
- stat-change explanation lines

Make those helpers feed:
- event log entries
- monthly recap lines
- the right-side pressure summary

**Step 4: Run test to verify it passes**

Run: `& .venv\Scripts\python.exe -m pytest tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_event_choices_and_win_states.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/budgetwars/models/content.py src/budgetwars/engine/events.py src/budgetwars/engine/game_loop.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/scoring.py tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_event_choices_and_win_states.py
git commit -m "feat: connect situations to pressure families"
```

---

### Task 3: Add the Learn drawer and menu toggle in Classic

**Files:**
- Create: `src/budgetwars/games/classic/ui/panes/learn_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/panes/menu_bar.py`
- Modify: `src/budgetwars/games/classic/ui/panes/__init__.py`
- Modify: `tests/games/classic/test_main_window.py`

**Step 1: Write the failing test**

Add UI tests that assert:
- the Info menu contains a `Learn` action
- the main window exposes a `show_learn()` handler
- the Learn panel renders the stat sections and pressure map entries

Example:

```python
def test_info_menu_exposes_learn_action():
    callbacks = {"help": lambda: None, "score": lambda: None, ...}
    menu = build_menu_bar(root, callbacks)
    assert "Learn" in menu.entrycget(3, "label")
```

**Step 2: Run test to verify it fails**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic/test_main_window.py -q`

Expected: fail because there is no Learn drawer yet.

**Step 3: Write minimal implementation**

Create a reusable Learn drawer that shows:
- what each stat means
- how to raise it
- how to lower it
- what usually affects it
- the top active pressure sources
- current situation-family labels

Wire it through:
- `Info > Learn`
- an optional `?` or `Learn` button if space permits

Keep it toggleable and non-intrusive. It should open as a dedicated help surface, not replace the main screen.

**Step 4: Run test to verify it passes**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic/test_main_window.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/learn_panel.py src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/panes/menu_bar.py src/budgetwars/games/classic/ui/panes/__init__.py tests/games/classic/test_main_window.py
git commit -m "feat: add classic learn drawer"
```

---

### Task 4: Surface “how to change this” guidance in the main Classic panels

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/score_strip.py`
- Modify: `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/event_popup.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `tests/games/classic/test_main_window.py`

**Step 1: Write the failing test**

Add tests that check for player-facing guidance in the summary models and rendered lines:
- credit shows next threshold and a short “how to improve” hint
- stress shows top contributors
- housing/transport lines mention what drives the stat up or down
- the monthly forecast names the active pressure family and what it means

**Step 2: Run test to verify it fails**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic/test_main_window.py -q`

Expected: fail because the new guidance strings are not yet present.

**Step 3: Write minimal implementation**

Add short causal lines, not long paragraphs:
- `Credit: what raises it / what lowers it`
- `Stress: current drivers`
- `Housing: how to stabilize`
- `Transport: what improves reliability`
- `Career: what improves momentum`
- `Education: what improves standing`

Keep the guidance compact and consistent with the Learn drawer so the game speaks one language everywhere.

**Step 4: Run test to verify it passes**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic/test_main_window.py -q`

Expected: pass.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/score_strip.py src/budgetwars/games/classic/ui/panes/finance_panel.py src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/panes/life_panel.py src/budgetwars/games/classic/ui/panes/event_popup.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_main_window.py
git commit -m "feat: surface stat guidance in classic ui"
```

---

### Task 5: Run the integration suite and tighten any rough edges

**Files:**
- Modify as needed based on failing tests from prior tasks
- Add: `tests/games/classic/test_learn_drawer.py` if the Learn panel needs dedicated coverage

**Step 1: Write the failing test**

Add one focused integration test for the full loop:
- open Learn
- verify it shows stat guidance and pressure sources
- verify a month recap reflects a pressure family or causal explanation after a resolve

**Step 2: Run test to verify it fails**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_content_loading.py -q`

Expected: fail until the last pieces are wired.

**Step 3: Write minimal implementation**

Fix whatever remains in the Learn drawer, content loader, or pressure summary wiring.

**Step 4: Run test to verify it passes**

Run: `& .venv\Scripts\python.exe -m pytest tests/games/classic tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_content_loading.py -q`

Expected: pass, with the existing `test_desktop_windowing.py` caveat still isolated if you run the full suite.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: teach stat changes and pressure in classic"
```

---

### Notes

- Keep Desktop mode untouched.
- Prefer short, concrete guidance over long explanatory text.
- The Learn drawer should teach the same causal model the engine already uses.
- The goal is not more content volume; the goal is clearer cause and effect.
