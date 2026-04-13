# Classic Status Arcs V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a thin explicit status-arc layer to Classic mode so the run remembers multi-month scars and surfaces them directly in the UI.

**Architecture:** Keep modifiers and chained events as the mechanical backbone. Add `StatusArcDefinition` content, `ActiveStatusArc` runtime state, and a small `status_arcs.py` helper module that owns v1 trigger routing for `transport_unstable`, `credit_squeeze`, and `education_slipping`.

**Tech Stack:** Python 3.12, Pydantic models, JSON content files, Tkinter, pytest

---

### Task 1: Add status arc models and content loading

**Files:**
- Modify: `src/budgetwars/models/content.py`
- Modify: `src/budgetwars/models/state.py`
- Modify: `src/budgetwars/models/__init__.py`
- Modify: `src/budgetwars/core/content.py`
- Modify: `src/budgetwars/loaders/content_loader.py`
- Modify: `src/budgetwars/loaders/validators.py`
- Create: `data/status_arcs.json`
- Test: `tests/test_content_loading.py`

**Step 1: Write the failing test**

Add tests that:
- load `status_arcs.json` into the content bundle
- reject unknown linked modifier ids
- reject unknown follow-up event ids
- verify `GameState` can hold active status arcs

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py`
Expected: FAIL because status arc models and loader wiring do not exist.

**Step 3: Write minimal implementation**

Add:
- `StatusArcDefinition`
- `ActiveStatusArc`
- `status_arcs` on `ContentBundle`
- `active_status_arcs` on `GameState`
- loader and validator support
- a thin `data/status_arcs.json` with the first three arc definitions

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/models/content.py src/budgetwars/models/state.py src/budgetwars/models/__init__.py src/budgetwars/core/content.py src/budgetwars/loaders/content_loader.py src/budgetwars/loaders/validators.py data/status_arcs.json tests/test_content_loading.py
git commit -m "feat: add classic status arc models and content loading"
```

### Task 2: Add lifecycle helpers with unique-per-id behavior

**Files:**
- Create: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/__init__.py`
- Test: `tests/test_status_arcs.py`

**Step 1: Write the failing test**

Add tests for:
- starting a new arc
- refreshing an existing arc instead of duplicating it
- capping severity at `3`
- resolving an arc cleanly
- ticking an arc until it expires

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_status_arcs.py`
Expected: FAIL because the helper module does not exist.

**Step 3: Write minimal implementation**

Implement:
- `start_status_arc`
- `refresh_status_arc`
- `resolve_status_arc`
- `tick_status_arcs`

Keep logic small and additive. Use one active entry per `arc_id`.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_status_arcs.py`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/status_arcs.py src/budgetwars/engine/__init__.py tests/test_status_arcs.py
git commit -m "feat: add classic status arc lifecycle helpers"
```

### Task 3: Prove transport instability as an arc

**Files:**
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/transport.py`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:
- transport-breakdown trigger events start `transport_unstable`
- retriggers refresh or escalate the same arc instead of duplicating it
- the active arc changes later pressure or transport access behavior

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "transport_unstable or phase_status_arc_transport"`
Expected: FAIL because no transport arc exists.

**Step 3: Write minimal implementation**

Use a code-owned mapping table in `status_arcs.py` so qualifying transport events and choices start or refresh `transport_unstable`. Feed the active arc into transport fragility and follow-up pressure.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "transport_unstable or phase_status_arc_transport"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/events.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/transport.py src/budgetwars/engine/status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: model transport instability as a status arc"
```

### Task 4: Prove credit squeeze as an arc

**Files:**
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/housing.py`
- Modify: `src/budgetwars/engine/transport.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:
- credit-review style trigger events start `credit_squeeze`
- rebuild or refinance paths can soften or resolve it
- the active arc tightens later housing or transport doors
- the active arc adds light score pressure

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "credit_squeeze or phase_status_arc_credit"`
Expected: FAIL because no credit arc exists.

**Step 3: Write minimal implementation**

Wire code-owned event and choice mappings for `credit_squeeze`, then feed the active arc into access checks, recovery routing, and a small score-pressure adjustment.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "credit_squeeze or phase_status_arc_credit"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/events.py src/budgetwars/engine/housing.py src/budgetwars/engine/transport.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/scoring.py src/budgetwars/engine/status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: model credit squeeze as a status arc"
```

### Task 5: Prove education slipping as an arc

**Files:**
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/education.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:
- education warning or decline triggers start `education_slipping`
- de-intensify or pause survival choices can soften or resolve it
- the active arc changes later academic follow-up pressure

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "education_slipping or phase_status_arc_education"`
Expected: FAIL because no education arc exists.

**Step 3: Write minimal implementation**

Use the code-owned mapping table in `status_arcs.py` to start, refresh, and resolve `education_slipping`, then tie it into follow-up pressure and recovery options.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "education_slipping or phase_status_arc_education"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/events.py src/budgetwars/engine/education.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: model education slipping as a status arc"
```

### Task 6: Surface active arcs directly in Classic UI

**Files:**
- Modify: `src/budgetwars/games/classic/ui/view_models.py`
- Modify: `src/budgetwars/games/classic/ui/diagnostics.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write the failing test**

Add tests that verify Classic UI now surfaces top active arcs with:
- arc name
- severity
- months remaining
- best resolution line

Also assert the diagnosis panel uses active arcs directly instead of only reconstructing pressure from raw stats.

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc"`
Expected: FAIL because active arcs are not exposed in the view models or panes.

**Step 3: Write minimal implementation**

Add view-model support for the top active arcs and render them directly in the center and diagnosis surfaces. Keep the layout additive and avoid a full redesign in this task.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/view_models.py src/budgetwars/games/classic/ui/diagnostics.py src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/panes/life_panel.py tests/games/classic/test_main_window.py
git commit -m "feat: surface classic status arcs in ui"
```

### Task 7: Full regression and proof checks

**Files:**
- Test: `tests/`

**Step 1: Run targeted proof tests**

Run:
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_status_arcs.py`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "status_arc or transport_unstable or credit_squeeze or education_slipping"`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc"`

Expected: PASS.

**Step 2: Run the full non-desktop suite**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q -k "not desktop"`
Expected: PASS with only existing skips or deselections.

**Step 3: Contrast verification**

Verify one deterministic contrast scenario:
- fragile transport build vs stable transport build
- weak-credit build vs strong-credit build
- overloaded student build vs stabilized student build

Expected:
- different active arcs
- different blocked doors or recovery routes
- different event pressure in later months

**Step 4: Commit**

```bash
git add .
git commit -m "test: verify classic status arc proof slice"
```
