# Classic Stateful Situations V2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Classic months diverge more sharply by letting event content target career branches and wealth posture directly.

**Architecture:** Extend `EventDefinition` and event validation with branch and wealth gating, then drive the behavior from `data/events.json` instead of adding more ad hoc branching logic in `events.py`. Keep the engine changes narrow and prove the difference with contrast tests.

**Tech Stack:** Python, Pydantic models, JSON content files, pytest

---

### Task 1: Extend event content schema

**Files:**
- Modify: `src/budgetwars/models/content.py`
- Modify: `src/budgetwars/loaders/validators.py`
- Test: `tests/test_content_loading.py`

**Step 1: Write the failing test**

Add tests that invalid branch ids and wealth strategy ids in events fail validation.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_loading.py -q`

**Step 3: Write minimal implementation**

Add `eligible_branch_ids` and `eligible_wealth_strategy_ids` to `EventDefinition`, then validate those ids against loaded content.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_loading.py -q`

**Step 5: Commit**

Commit message: `feat: add branch and wealth event gating`

### Task 2: Make event eligibility respect branch and wealth gating

**Files:**
- Modify: `src/budgetwars/engine/events.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Write the failing test**

Add contrast tests showing management vs sales branches and cushion-first vs market-chaser runs expose different event ids.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_consequence_depth.py -q`

**Step 3: Write minimal implementation**

Update `_event_is_eligible(...)` to filter on branch and wealth strategy. Keep `event_family(...)` aligned with the new branch-specific event ids so pressure tagging remains coherent.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_consequence_depth.py -q`

**Step 5: Commit**

Commit message: `feat: respect branch and wealth event gating`

### Task 3: Deepen starter career branches and situations

**Files:**
- Modify: `data/careers.json`
- Modify: `data/events.json`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_content_loading.py`

**Step 1: Write the failing test**

Require retail and warehouse to expose three branches each. Require branch-specific and wealth-specific situations to appear in eligible event pools.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_consequence_depth.py -q`

**Step 3: Write minimal implementation**

Add:
- `retail_clienteling_track`
- `warehouse_equipment_track`
- branch-specific events for retail management, retail sales, retail clienteling, warehouse ops, warehouse dispatch, and warehouse equipment
- wealth-strategy events for cushion/steady and market-chaser lanes

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_loading.py tests/test_consequence_depth.py -q`

**Step 5: Commit**

Commit message: `feat: deepen branch and wealth situations`

### Task 4: Regression verification

**Files:**
- Test: `tests/`

**Step 1: Run the full non-desktop suite**

Run: `python -m pytest tests/ -q -k "not desktop_windowing"`

**Step 2: Verify expected result**

Expected: full green or only pre-existing skips/deselections.

**Step 3: Manual verification**

Run at least two short contrast starts:
- retail management vs retail sales
- cushion-first vs market-chaser during weak/correction market

Expected:
- different situation pools
- different monthly choices
- clearer run identity
