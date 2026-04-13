# Classic Status Arcs Wave 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the Classic status-arc layer with lease pressure, burnout risk, and promotion-window opportunity arcs, then tighten the Classic UI to lean on active arcs more directly.

**Architecture:** Keep status arcs thin and additive. Use content definitions in `data/status_arcs.json`, keep trigger mappings code-owned in `src/budgetwars/engine/status_arcs.py`, and feed the new arcs into event weighting, access/recovery logic, light scoring, and direct Classic UI surfacing.

**Tech Stack:** Python 3.12, Pydantic models, JSON content files, Tkinter, pytest

---

### Task 1: Add second-wave status arc definitions

**Files:**
- Modify: `data/status_arcs.json`
- Test: `tests/test_content_loading.py`

**Step 1: Write the failing test**

Add tests that verify `status_arcs.json` now includes:

- `lease_pressure`
- `burnout_risk`
- `promotion_window_open`

Also assert each has follow-up events and resolution copy.

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py -k "status_arc and wave_2"`
Expected: FAIL because the new arc definitions do not exist yet.

**Step 3: Write minimal implementation**

Add the three arc definitions with:

- summaries
- priorities
- tones
- follow-up event ids
- blocked-door hints
- resolution hints

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py -k "status_arc and wave_2"`
Expected: PASS.

**Step 5: Commit**

```bash
git add data/status_arcs.json tests/test_content_loading.py
git commit -m "feat: define second wave classic status arcs"
```

### Task 2: Add lease pressure arc behavior

**Files:**
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/housing.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:

- `lease_default_warning` starts `lease_pressure`
- `lease_enforcement_notice` escalates the same arc instead of duplicating it
- the arc increases later lease pressure or blocked housing diagnosis
- the arc creates a real contrast against a stable housing build

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "lease_pressure or phase_status_arc_lease"`
Expected: FAIL because no lease arc behavior exists yet.

**Step 3: Write minimal implementation**

Use code-owned mappings in `status_arcs.py` and feed the active arc into event weighting, housing access/diagnosis, and light score pressure.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "lease_pressure or phase_status_arc_lease"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/status_arcs.py src/budgetwars/engine/events.py src/budgetwars/engine/housing.py src/budgetwars/engine/scoring.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: model lease pressure as a status arc"
```

### Task 3: Add burnout risk arc behavior

**Files:**
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:

- `overtime_attrition_warning` starts `burnout_risk`
- `burnout_month` escalates it
- recovery-oriented choices or a cleaner month can soften it
- the active arc changes later burnout pressure and diagnosis

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "burnout_risk or phase_status_arc_burnout"`
Expected: FAIL because no burnout arc behavior exists yet.

**Step 3: Write minimal implementation**

Wire code-owned mappings and feed the active arc into burnout pressure weighting, recovery routing, and light score pressure.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "burnout_risk or phase_status_arc_burnout"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/status_arcs.py src/budgetwars/engine/events.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/scoring.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: model burnout risk as a status arc"
```

### Task 4: Add promotion-window opportunity arc behavior

**Files:**
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Modify: `src/budgetwars/engine/game_loop.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_event_choices_and_win_states.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write the failing test**

Add deterministic tests showing:

- `promotion_window` starts `promotion_window_open`
- its choices extend or intensify the same opportunity arc
- a pending promotion branch decision can keep the arc relevant
- active opportunity arcs change later promotion pressure and score movement

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py tests/test_month_resolution.py -k "promotion_window_open or phase_status_arc_promotion"`
Expected: FAIL because no promotion arc behavior exists yet.

**Step 3: Write minimal implementation**

Use code-owned mappings and feed the active opportunity arc into event weighting, diagnosis, and light score upside.

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py tests/test_month_resolution.py -k "promotion_window_open or phase_status_arc_promotion"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/status_arcs.py src/budgetwars/engine/events.py src/budgetwars/engine/scoring.py src/budgetwars/engine/game_loop.py tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py tests/test_month_resolution.py
git commit -m "feat: model promotion windows as status arcs"
```

### Task 5: Tighten Classic arc-first hierarchy

**Files:**
- Modify: `src/budgetwars/games/classic/ui/diagnostics.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write the failing test**

Add tests showing:

- the center panel surfaces the top active arc before generic warnings
- the right-side diagnosis uses active arcs first when they exist
- duplicate generic diagnosis text is reduced when an active arc already explains the run pressure

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc and (outlook or diagnosis or hierarchy)"`
Expected: FAIL because the current UI still mixes active arcs with too much generic pressure prose.

**Step 3: Write minimal implementation**

Keep the existing layout, but make the center and right panels arc-first:

- top active arc becomes the hero context
- diagnosis derives from active arcs before raw pressure-family text
- duplicate warning lists are trimmed when an arc already explains the threat

**Step 4: Run test to verify it passes**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc and (outlook or diagnosis or hierarchy)"`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/diagnostics.py src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/panes/finance_panel.py tests/games/classic/test_main_window.py
git commit -m "feat: make classic ui arc-first"
```

### Task 6: Full regression and contrast verification

**Files:**
- Test: `tests/`

**Step 1: Run targeted proof tests**

Run:

- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py -k "wave_2"`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_month_resolution.py -k "phase_status_arc_lease or phase_status_arc_burnout or phase_status_arc_promotion"`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_event_choices_and_win_states.py -k "phase_status_arc_promotion or promotion_window"`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "status_arc and (outlook or diagnosis or hierarchy)"`

Expected: PASS.

**Step 2: Run the full non-desktop suite**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q -k "not desktop"`
Expected: PASS.

**Step 3: Verify deterministic contrasts**

Verify at least one deterministic contrast in each family:

- fragile renter vs stable at-home saver
- overloaded overtime worker vs stabilized worker
- promotion-ready worker vs flat-momentum worker

Expected differences:

- active arcs
- later event pressure
- blocked doors or recovery route lines
- score movement or promotion diagnosis

**Step 4: Commit**

```bash
git add .
git commit -m "test: verify second wave classic status arcs"
```
