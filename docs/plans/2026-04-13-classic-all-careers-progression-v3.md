# Classic All-Careers Progression V3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild Classic career progression across all eight careers so advancement slows down, branches exist everywhere, promotion choices create durable role identities, and late-career play continues after nominal tier cap.

**Architecture:** Keep the current career/event architecture, but deepen it with universal three-branch coverage, higher tier thresholds, tag-driven role-state effects, recurring promotion fork events, and post-cap role identity hooks. Persistent tags remain the first implementation of durable role state, and the career engine becomes responsible for translating those tags into long-term pay, volatility, stress, and blocker differences.

**Tech Stack:** Python 3.12, Pydantic models, JSON content files, Tkinter, pytest

---

### Task 1: Add coverage tests for all-careers parity targets

**Files:**
- Modify: `tests/test_content_loading.py`
- Create: `tests/test_career_progression_v3.py`

**Step 1: Write the failing test**

Add tests that assert:

- all eight careers exist
- every career has at least three branches
- every career still has five tiers
- tracks that previously had no branches now expose three branches

Add parity tests that will later verify:

- post-cap role-state divergence
- all-career branch count

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py tests/test_career_progression_v3.py -k "all_careers or progression_v3"`
Expected: FAIL because branchless careers still have no branches and the new parity tests have no implementation support.

**Step 3: Write minimal implementation**

No production code yet. Only add the failing tests.

**Step 4: Run test to verify it fails correctly**

Run the same command and confirm the failure is due to missing branch parity rather than a test typo.

**Step 5: Commit**

```bash
git add tests/test_content_loading.py tests/test_career_progression_v3.py
git commit -m "test: add all-careers progression parity coverage"
```

### Task 2: Expand `careers.json` to three branches for all eight careers and raise promotion targets

**Files:**
- Modify: `data/careers.json`
- Test: `tests/test_content_loading.py`
- Test: `tests/test_career_progression_v3.py`

**Step 1: Write the failing test**

Add exact assertions for the new branch ids on:

- `delivery_gig`
- `trades_apprenticeship`
- `healthcare_support`
- `sales`
- `degree_gated_professional`

Add exact assertions that promotion targets were materially increased for all careers.

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_content_loading.py tests/test_career_progression_v3.py -k "career_branch or promotion_target or all_careers"`
Expected: FAIL because the new branches and target thresholds are not present yet.

**Step 3: Write minimal implementation**

Update `data/careers.json` to:

- add three branches to each previously branchless career
- preserve existing branched careers, but normalize all tracks to three branches
- raise tier `promotion_target` values across every track

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS.

**Step 5: Commit**

```bash
git add data/careers.json tests/test_content_loading.py tests/test_career_progression_v3.py
git commit -m "feat: add all-careers branch structure and slower promotion targets"
```

### Task 3: Add durable career role-state support through tags and engine hooks

**Files:**
- Modify: `src/budgetwars/engine/careers.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Test: `tests/test_career_progression_v3.py`

**Step 1: Write the failing test**

Add tests showing that durable career tags can change:

- income
- stress or energy drift
- promotion blockers
- score interpretation

Use two same-track/same-tier runs that differ only by persistent career tag.

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_career_progression_v3.py -k "role_state or durable_tag or post_cap"`
Expected: FAIL because career tags do not yet alter long-term engine behavior strongly enough.

**Step 3: Write minimal implementation**

Implement shared helpers in `careers.py` that read persistent tags and branch ids to adjust:

- income multipliers
- variance
- stress / energy drift
- promotion momentum
- blocker rules

Update scoring so strong late-career role identity is rewarded and fragile high-income identity is penalized.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/careers.py src/budgetwars/engine/scoring.py tests/test_career_progression_v3.py
git commit -m "feat: add durable all-careers role-state effects"
```

### Task 4: Rebalance promotion progression and remove max-tier dead-end behavior

**Files:**
- Modify: `src/budgetwars/engine/careers.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/game_loop.py`
- Test: `tests/test_month_resolution.py`
- Test: `tests/test_career_progression_v3.py`

**Step 1: Write the failing test**

Add tests showing:

- routine good months do not hit top tier absurdly early
- promotion pacing differs by branch fit and build health
- max-tier careers can still enter late-career opportunity states rather than going flat

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_month_resolution.py tests/test_career_progression_v3.py -k "promotion_pacing or max_tier or late_career"`
Expected: FAIL because promotion is still too fast and capped careers still flatten out.

**Step 3: Write minimal implementation**

Reduce routine progress gain, rely more on blockers, and make max-tier careers continue to accumulate late-career role-state outcomes through events and tags instead of ending progression logic.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/engine/careers.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/game_loop.py tests/test_month_resolution.py tests/test_career_progression_v3.py
git commit -m "feat: rebalance promotion pacing and extend post-cap career play"
```

### Task 5: Add branch-specific and role-specific events for every career family

**Files:**
- Modify: `data/events.json`
- Modify: `src/budgetwars/engine/events.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_event_choices_and_win_states.py`

**Step 1: Write the failing test**

Add deterministic tests that verify event-pool divergence for:

- all three branches in each of the eight careers
- at least one late-career durable role-state split per career family

Add choice-event tests showing recurring promotion forks write lasting career tags.

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py -k "career_progression_v3 or promotion_fork or branch_specific"`
Expected: FAIL because not all careers yet have real branch-specific and role-specific event pools.

**Step 3: Write minimal implementation**

Expand `data/events.json` with:

- recurring promotion fork events for every career
- branch-specific upside and failure hooks for every branch
- post-cap role-state events keyed by persistent tags

Wire any needed weighting adjustments in `events.py`.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS.

**Step 5: Commit**

```bash
git add data/events.json src/budgetwars/engine/events.py tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py
git commit -m "feat: add all-careers branch and role-state event pools"
```

### Task 6: Surface deeper career identity in Classic UI summaries

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Modify: `src/budgetwars/games/classic/ui/diagnostics.py`
- Modify: `src/budgetwars/games/classic/ui/view_models.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write the failing test**

Add tests showing that Classic UI summaries now surface:

- branch identity
- durable late-career role identity
- promotion windows as long-term forks rather than generic progress bars

**Step 2: Run test to verify it fails**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "career_progression_v3 or role_identity or promotion_fork"`
Expected: FAIL because the UI does not yet summarize deeper role-state identity cleanly.

**Step 3: Write minimal implementation**

Extend summary builders to name current branch and durable role identity more explicitly. Keep the UI pass additive and avoid broader layout redesign here.

**Step 4: Run test to verify it passes**

Run the same command.
Expected: PASS.

**Step 5: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/diagnostics.py src/budgetwars/games/classic/ui/view_models.py tests/games/classic/test_main_window.py
git commit -m "feat: surface all-careers role identity in classic ui"
```

### Task 7: Full regression and deterministic contrast verification

**Files:**
- Test: `tests/`

**Step 1: Run targeted parity tests**

Run:

- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_career_progression_v3.py`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/test_consequence_depth.py tests/test_event_choices_and_win_states.py -k "career_progression_v3 or promotion_fork or branch_specific"`
- `..\..\.venv\Scripts\python.exe -m pytest -q tests/games/classic/test_main_window.py -k "career_progression_v3 or role_identity or promotion_fork"`

Expected: PASS.

**Step 2: Run the full non-desktop suite**

Run: `..\..\.venv\Scripts\python.exe -m pytest -q -k "not desktop"`
Expected: PASS.

**Step 3: Verify deterministic contrasts**

Verify at least these:

- same career, different branch -> different event pool
- same branch, different durable role tags -> different late-career event pool
- same money, different role quality -> different score
- promotion pacing does not cap absurdly early in ordinary good runs

**Step 4: Commit**

```bash
git add .
git commit -m "test: verify all-careers progression v3"
```
