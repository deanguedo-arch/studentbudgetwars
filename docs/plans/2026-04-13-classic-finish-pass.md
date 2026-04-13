# Classic Finish Pass Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Finish the remaining Classic-mode work by making stress recovery achievable outside hometown, deepening status-arc consequence content, strengthening career and wealth divergence, simplifying the Classic UI hierarchy, and proving the final result through deterministic contrast tests.

**Architecture:** Keep the current Classic architecture and extend it additively. Stress recovery becomes a pressure-vs-recovery calculation in month resolution, status arcs stay as the named multi-month scar layer, career and wealth systems get deeper content and durable consequences, and the UI hierarchy pass only happens after the stronger systems are in place.

**Tech Stack:** Python, pytest, Tkinter Classic UI, JSON content files

---

### Task 1: Stress Recovery V2 Failing Tests

**Files:**
- Modify: `tests/test_month_resolution.py`
- Reference: `src/budgetwars/engine/month_resolution.py`
- Reference: `src/budgetwars/engine/status_arcs.py`

**Step 1: Write the failing tests**

Add deterministic tests for:
- stable `mid_size_city` + `recovery_month` lowers stress
- stable `high_opportunity_metro` + `recovery_month` lowers stress
- stable ordinary metro month does not auto-ratchet stress upward
- fragile metro build still rises
- severe arcs reduce recovery capacity
- pressure trend messaging reflects easing / stable / rising

```python
def test_high_opportunity_metro_recovery_month_can_lower_stress(content_bundle):
    state = make_stable_state(city_id="high_opportunity_metro", focus="recovery_month", stress=48)
    resolved = resolve_month(state, content_bundle)
    assert resolved.player.stress < 48
```

**Step 2: Run test to verify it fails**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_month_resolution.py -q`
Expected: FAIL on one or more new metro recovery assertions.

**Step 3: Commit the failing test state only if you need a checkpoint**

```bash
git add tests/test_month_resolution.py
git commit -m "test: define stress recovery v2 expectations"
```

### Task 2: Stress Recovery V2 Implementation

**Files:**
- Modify: `src/budgetwars/engine/month_resolution.py`
- Maybe modify: `src/budgetwars/engine/status_arcs.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Implement explicit recovery-capacity calculation**

Add helpers similar to:

```python
def _stress_recovery_capacity(state, focus_def, housing_snapshot, transport_snapshot) -> int:
    ...

def _stress_pressure_burden(state, city_def, pressure_map) -> int:
    ...
```

Required inputs:
- focus bonuses (`recovery_month`, `social_maintenance`, `move_prep`)
- housing stability / recovery quality
- transport reliability
- support / social footing
- non-negative surplus breathing room
- severe active arc penalties
- city recovery / pressure bias

**Step 2: Replace one-way monthly stress handling with balanced resolution**

Keep city identity intact:
- hometown easiest
- mid-size recoverable when stable
- metro hardest but recoverable when earned

**Step 3: Re-run targeted tests**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_month_resolution.py -q`
Expected: PASS

**Step 4: Run broader regression**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`
Expected: PASS

**Step 5: Commit**

```bash
git add src/budgetwars/engine/month_resolution.py src/budgetwars/engine/status_arcs.py tests/test_month_resolution.py
git commit -m "feat: rebalance classic stress recovery"
```

### Task 3: Status-Arc Content V2 Failing Tests

**Files:**
- Modify: `tests/test_status_arcs.py`
- Modify: `tests/test_consequence_depth.py`
- Reference: `data/events.json`
- Reference: `data/status_arcs.json`
- Reference: `src/budgetwars/engine/status_arcs.py`
- Reference: `src/budgetwars/engine/events.py`

**Step 1: Write failing tests for stronger arc behavior**

Cover:
- stronger trigger coverage for existing arc families
- escalation after repeated hits
- follow-up choice availability while arc active
- access consequences while arc active
- build-dependent contrast in arc severity or resolution options

```python
def test_transport_unstable_escalates_after_repeated_transport_hits(content_bundle):
    state = make_transport_fragile_state()
    trigger_arc(state, "transport_unstable", severity=1)
    trigger_arc(state, "transport_unstable", severity=1)
    assert active_arc(state, "transport_unstable").severity >= 2
```

**Step 2: Run targeted tests to verify failure**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_status_arcs.py tests/test_consequence_depth.py -q`
Expected: FAIL on escalation / follow-up / contrast expectations.

### Task 4: Status-Arc Content V2 Implementation

**Files:**
- Modify: `data/events.json`
- Modify: `data/status_arcs.json`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/events.py`
- Maybe modify: `src/budgetwars/engine/month_resolution.py`
- Test: `tests/test_status_arcs.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Deepen content for the six existing arc families**

Add:
- stronger triggers
- escalation rules
- more follow-up choices
- branch/build-dependent resolution options
- stronger access consequences where relevant

**Step 2: Keep hooks code-owned**

Do not add content-authored `start_status_arc_id` fields yet. Keep v1/v2 trigger routing in `status_arcs.py`.

**Step 3: Run targeted and regression tests**

Run:
- `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_status_arcs.py tests/test_consequence_depth.py -q`
- `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`

**Step 4: Commit**

```bash
git add data/events.json data/status_arcs.json src/budgetwars/engine/status_arcs.py src/budgetwars/engine/events.py src/budgetwars/engine/month_resolution.py tests/test_status_arcs.py tests/test_consequence_depth.py
git commit -m "feat: deepen classic status arc consequences"
```

### Task 5: Career Futures Follow-Through Failing Tests

**Files:**
- Modify: `tests/test_career_progression_v3.py`
- Modify: `tests/test_consequence_depth.py`
- Reference: `data/careers.json`
- Reference: `data/events.json`
- Reference: `src/budgetwars/engine/careers.py`
- Reference: `src/budgetwars/engine/events.py`
- Reference: `src/budgetwars/engine/scoring.py`

**Step 1: Write failing tests for future divergence**

Cover:
- recurring promotion forks produce different later pay / stress / event pools
- post-cap role bands diverge more clearly
- identical income runs with different role paths do not score the same
- at least one contrast check per career family group

```python
def test_sales_manager_track_and_specialist_track_diverge_after_promotion(content_bundle):
    manager = run_sales_path(choice="manager_track")
    specialist = run_sales_path(choice="specialist_track")
    assert manager.player.monthly_income != specialist.player.monthly_income or manager.player.stress != specialist.player.stress
```

**Step 2: Run targeted tests to verify failure**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_career_progression_v3.py tests/test_consequence_depth.py -q`
Expected: FAIL on divergence assertions.

### Task 6: Career Futures Follow-Through Implementation

**Files:**
- Modify: `data/careers.json`
- Modify: `data/events.json`
- Modify: `src/budgetwars/engine/careers.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Maybe modify: `src/budgetwars/engine/game_loop.py`
- Maybe modify: `src/budgetwars/models/state.py`
- Test: `tests/test_career_progression_v3.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Deepen durable role consequences**

Add stronger divergence in:
- recurring promotion forks
- post-cap role bands
- branch-specific failure / upside hooks
- durable tags written by role choices and career setbacks

**Step 2: Run targeted and regression tests**

Run:
- `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_career_progression_v3.py tests/test_consequence_depth.py -q`
- `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`

**Step 3: Commit**

```bash
git add data/careers.json data/events.json src/budgetwars/engine/careers.py src/budgetwars/engine/events.py src/budgetwars/engine/scoring.py src/budgetwars/engine/game_loop.py src/budgetwars/models/state.py tests/test_career_progression_v3.py tests/test_consequence_depth.py
git commit -m "feat: deepen classic career futures"
```

### Task 7: Wealth Identity V2 Failing Tests

**Files:**
- Modify: `tests/test_consequence_depth.py`
- Maybe create: `tests/test_wealth_identity.py`
- Reference: `src/budgetwars/engine/wealth.py`
- Reference: `src/budgetwars/engine/events.py`
- Reference: `src/budgetwars/engine/scoring.py`
- Reference: `data/wealth_strategies.json`
- Reference: `data/events.json`

**Step 1: Write failing tests for wealth contrast**

Cover:
- strong-month divergence between strategies
- bad-month / liquidation divergence
- different recovery implications under stress pressure
- different score movement for same-income runs with different strategies

**Step 2: Run targeted tests to verify failure**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_consequence_depth.py -q`
Expected: FAIL on new wealth-contrast assertions.

### Task 8: Wealth Identity V2 Implementation

**Files:**
- Modify: `src/budgetwars/engine/wealth.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Modify: `data/wealth_strategies.json`
- Modify: `data/events.json`
- Maybe modify: `data/status_arcs.json`
- Test: `tests/test_consequence_depth.py`
- Maybe test: `tests/test_wealth_identity.py`

**Step 1: Deepen the four wealth signatures**

Make `cushion_first`, `debt_crusher`, `steady_builder`, and `market_chaser` feel more different on:
- upside months
- weak months
- liquidation pain
- recovery paths
- score interpretation

**Step 2: Run targeted and regression tests**

Run:
- `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_consequence_depth.py -q`
- `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`

**Step 3: Commit**

```bash
git add src/budgetwars/engine/wealth.py src/budgetwars/engine/events.py src/budgetwars/engine/scoring.py data/wealth_strategies.json data/events.json data/status_arcs.json tests/test_consequence_depth.py tests/test_wealth_identity.py
git commit -m "feat: strengthen classic wealth identities"
```

### Task 9: Classic UI Hierarchy Simplification Failing Tests

**Files:**
- Modify: `tests/games/classic/test_main_window.py`
- Modify: `tests/games/classic/test_ui_surface_stabilization.py`
- Reference: `src/budgetwars/games/classic/ui/main_window.py`
- Reference: `src/budgetwars/games/classic/ui/view_models.py`
- Reference: `src/budgetwars/games/classic/ui/diagnostics.py`
- Reference: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Reference: `src/budgetwars/games/classic/ui/panes/score_strip.py`
- Reference: `src/budgetwars/games/classic/ui/panes/status_bar.py`
- Reference: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Reference: `src/budgetwars/games/classic/ui/panes/finance_panel.py`

**Step 1: Write failing UI assertions**

Cover:
- center panel shows a single dominant monthly context block
- duplicate diagnosis strings are reduced
- right panel prefers diagnostic summary over repeated stats
- left panel surfaces stronger build identity before detail density

**Step 2: Run targeted tests to verify failure**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/games/classic/test_main_window.py tests/games/classic/test_ui_surface_stabilization.py -q`
Expected: FAIL on new hierarchy expectations.

### Task 10: Classic UI Hierarchy Simplification Implementation

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/view_models.py`
- Modify: `src/budgetwars/games/classic/ui/diagnostics.py`
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/score_strip.py`
- Modify: `src/budgetwars/games/classic/ui/panes/status_bar.py`
- Modify: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- Test: `tests/games/classic/test_main_window.py`
- Test: `tests/games/classic/test_ui_surface_stabilization.py`

**Step 1: Simplify the main-screen hierarchy**

Keep the changes structural, not purely cosmetic:
- stronger center-panel dominance
- less duplication
- identity-first left panel
- diagnostic-first right panel
- trimmed top strip

**Step 2: Run targeted UI tests and regression**

Run:
- `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/games/classic/test_main_window.py tests/games/classic/test_ui_surface_stabilization.py -q`
- `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`

**Step 3: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/view_models.py src/budgetwars/games/classic/ui/diagnostics.py src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/panes/score_strip.py src/budgetwars/games/classic/ui/panes/status_bar.py src/budgetwars/games/classic/ui/panes/life_panel.py src/budgetwars/games/classic/ui/panes/finance_panel.py tests/games/classic/test_main_window.py tests/games/classic/test_ui_surface_stabilization.py
git commit -m "feat: simplify classic ui hierarchy"
```

### Task 11: Final Contrast / Balance Truth Tests

**Files:**
- Modify: `tests/test_consequence_depth.py`
- Maybe modify: `tests/test_month_resolution.py`
- Maybe modify: `tests/test_status_arcs.py`
- Maybe modify: `tests/test_career_progression_v3.py`
- Maybe create fixture helpers in: `tests/conftest.py`

**Step 1: Add or reuse deterministic archetype fixtures**

Cover:
- stable at-home saver
- debt-heavy renter
- transport-fragile worker
- school-heavy climber
- weak-credit fragile build
- strong-credit stable build

**Step 2: Write final truth-pass assertions**

Compare at least:
- event pool
- arc presence / severity
- blocked doors
- promotion offers / role bands
- recovery route availability
- stress movement
- score movement

**Step 3: Run targeted truth-pass tests to verify meaningful contrast**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest tests/test_consequence_depth.py -q`
Expected: PASS only when differences are real.

### Task 12: Full Regression, Manual Preview, and Branch Summary

**Files:**
- No planned production-code changes in this task
- Optional notes update: `docs/plans/2026-04-13-classic-finish-pass.md`

**Step 1: Run full regression**

Run: `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`
Expected: PASS

**Step 2: Run deterministic spot checks called out by the new tests**

Examples:
- metro recovery scenario
- severe lease / burnout arc scenario
- divergent career role-band scenario
- divergent wealth strategy scenario

**Step 3: Manual Classic preview check**

Run: `./live_preview_classic.bat`
Inspect:
- non-hometown recovery is achievable on stable runs
- active arcs feel consequential
- center panel is visually dominant
- right panel is more diagnostic and less repetitive

**Step 4: Commit any final cleanup**

```bash
git add -A
git commit -m "test: lock in classic finish pass contrast"
```
