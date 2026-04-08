# Classic UI Hierarchy Refactor Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rework the Classic UI so each turn reads as a clear monthly strategy decision, with stronger hierarchy, shorter text, and more explicit score and pressure feedback.

**Architecture:** Keep the simulation engine as the source of truth and move presentation logic into `main_window.py` and the Classic pane classes. Replace raw line-list rendering with small structured view models for monthly threat, opportunity, score delta, build snapshot, and pressure summary. Preserve the existing theme and pane layout, but make each panel emphasize priority, grouping, and cause-and-effect instead of dense descriptive text.

**Tech Stack:** Python 3.11+, Tkinter, pytest, existing `budgetwars` engine and Classic UI modules.

---

### Task 1: Define the new UI data flow

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`

**Step 1: Write the failing test**

Add a unit test that asserts `MainWindow` can build structured presentation data for:
- build snapshot
- monthly forecast
- pressure summary
- score delta summary

The test should verify the data is not a single flat list of strings.

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_main_window.py -v`
Expected: FAIL because the structured builders do not exist yet.

**Step 3: Write minimal implementation**

Create small helper methods in `main_window.py` that return dictionaries or dataclasses for each panel instead of line lists.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_main_window.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_main_window.py
git commit -m "refactor: structure classic ui presentation data"
```

### Task 2: Rebuild the center panel as a monthly command center

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_outlook_panel.py`

**Step 1: Write the failing test**

Add tests that verify the center panel renders named sections in this order:
- Main Threat
- Best Opportunity
- Chosen Focus
- Expected Swing

Also verify that monthly preview text is shorter and does not depend on a raw long list.

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_outlook_panel.py -v`
Expected: FAIL because the panel still renders line lists.

**Step 3: Write minimal implementation**

Update the panel to accept a structured payload and render a small set of labeled blocks and short notes.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_outlook_panel.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_outlook_panel.py
git commit -m "feat: sharpen classic monthly outlook panel"
```

### Task 3: Separate build actions from monthly actions

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/actions_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_actions_panel.py`

**Step 1: Write the failing test**

Add tests that verify action buttons are grouped into:
- Build
- Policy
- This Month

Also verify `Resolve Month` remains the visually dominant action and `Focus` appears in the monthly group.

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_actions_panel.py -v`
Expected: FAIL because the panel still lays out actions in one flat grid.

**Step 3: Write minimal implementation**

Teach `ActionsPanel` to accept grouped actions or a simple grouping hint and render grouped sections with `Resolve Month` highlighted.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_actions_panel.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/actions_panel.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_actions_panel.py
git commit -m "feat: group classic actions by decision type"
```

### Task 4: Make score movement explicit

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/score_strip.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_score_strip.py`

**Step 1: Write the failing test**

Add tests that verify the score strip can display:
- projected score
- tier
- score delta from last month
- strongest category
- weakest category
- a short diagnosis line

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_score_strip.py -v`
Expected: FAIL because the strip only shows projected score, tier, and biggest risk.

**Step 3: Write minimal implementation**

Add state in `main_window.py` to compare current and previous snapshots, then pass the delta summary into the score strip.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_score_strip.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/score_strip.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_score_strip.py
git commit -m "feat: surface score deltas in classic ui"
```

### Task 5: Collapse text walls in the build and pressure panels

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_life_panel.py`
- Test: `tests/games/classic/test_finance_panel.py`

**Step 1: Write the failing test**

Add tests that verify:
- the build panel shows concise one-line summaries per system
- the pressure panel prioritizes cash flow, debt, stress, and active threats before secondary details

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_life_panel.py tests/games/classic/test_finance_panel.py -v`
Expected: FAIL because both panels still infer emphasis from long string lists.

**Step 3: Write minimal implementation**

Replace line-list parsing with small structured sections or compact record objects. Keep the same visual framing, but reduce textual volume and repeated labels.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_life_panel.py tests/games/classic/test_finance_panel.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/life_panel.py src/budgetwars/games/classic/ui/panes/finance_panel.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_life_panel.py tests/games/classic/test_finance_panel.py
git commit -m "feat: simplify classic build and pressure panels"
```

### Task 6: Make the setup dialog feel like a run picker

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_setup_dialog.py`

**Step 1: Write the failing test**

Add tests that verify the setup summary uses stronger forecast language such as:
- Your Start
- Your Pressure
- Your Best Edge

Also verify it includes a concise forecast line instead of a dossier-style block.

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_setup_dialog.py -v`
Expected: FAIL because the summary still uses the older briefing labels.

**Step 3: Write minimal implementation**

Update `build_setup_summary_lines()` and the dialog labels to emphasize identity, risk, and upside.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_setup_dialog.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_setup_dialog.py
git commit -m "feat: make classic setup feel like a run picker"
```

### Task 7: Sharpen monthly recap and resolve feedback

**Files:**
- Modify: `src/budgetwars/games/classic/ui/log_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_run_feedback.py`

**Step 1: Write the failing test**

Add tests that verify monthly feedback is structured around:
- Big Win
- Big Hit
- Score Change
- New Threat
- Next Best Move

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_run_feedback.py -v`
Expected: FAIL because feedback still reads like generic log output.

**Step 3: Write minimal implementation**

Adjust the monthly recap text generation to build a short structured summary, while leaving the detailed event log intact below it.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_run_feedback.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/log_panel.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_run_feedback.py
git commit -m "feat: tighten classic monthly feedback"
```

### Task 8: Verify the full Classic UI flow

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/panes/*.py`
- Test: `tests/games/classic/test_classic_ui_smoke.py`

**Step 1: Write the failing test**

Add a smoke test that opens the Classic window, renders a state, and verifies the major panels all receive the new structured content without errors.

**Step 2: Run test to verify it fails**

Run: `pytest tests/games/classic/test_classic_ui_smoke.py -v`
Expected: FAIL until all panel API changes are wired together.

**Step 3: Write minimal implementation**

Wire up the new structured builders and panel renderers end-to-end.

**Step 4: Run test to verify it passes**

Run: `pytest tests/games/classic/test_classic_ui_smoke.py -v`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/panes/*.py tests/games/classic/test_classic_ui_smoke.py
git commit -m "feat: complete classic ui hierarchy refactor"
```

### Task 9: Run the full test suite and fix regressions

**Files:**
- Modify: any Classic UI file implicated by test failures

**Step 1: Run the full suite**

Run: `pytest tests/`
Expected: All existing tests pass, with the known Tkinter headless caveat still isolated to `test_desktop_windowing.py` if the environment lacks a display.

**Step 2: Fix any regressions**

Only touch the files that are directly causing failures. Do not broaden scope.

**Step 3: Re-run the full suite**

Run: `pytest tests/`
Expected: PASS.

**Step 4: Commit**

```bash
git add .
git commit -m "test: verify classic ui hierarchy refactor"
```
