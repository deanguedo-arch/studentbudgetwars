# Classic Event Content Overhaul Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make Classic's stabilizing events coherent and consequential, deepen branch-driven futures and medium-term scars, strengthen wealth identity, restore monthly cash-flow visibility, reduce `main_window.py` risk, and finish the remaining UI hierarchy work.

**Architecture:** Keep the explicit status-arc layer, all-careers progression framework, and current scoring model shape. Do not add another new subsystem. Execute this as a content-and-presentation overhaul built on existing arcs, modifiers, event choices, promotion scaffolding, and Classic UI panes. Use TDD and deterministic contrast fixtures for every slice.

**Tech Stack:** Python 3.12, Tkinter Classic UI, Pydantic content models, pytest, JSON content files.

---

## Ground Rules

- Classic mode only
- Do not touch Desktop
- Do not restart architecture
- Do not do the whole event catalog in one undifferentiated code pass
- Use TDD for every task
- Keep changes phase-scoped with frequent commits
- Preserve deterministic archetype fixtures:
  - stable at-home saver
  - debt-heavy renter
  - transport-fragile worker
  - school-heavy climber
  - weak-credit fragile build
  - strong-credit stable build

## Event Taxonomy Rules To Enforce

### Positive/Stabilizing Taxonomy

Use these categories when rewriting content:
- `acute_recovery`
  - large `stress` reduction
  - large `energy` increase
  - may reduce cash, pay, or progress
  - should not read as body-state punishment
- `structural_stabilization`
  - moderate body relief
  - plus material arc softening, access improvement, standing recovery, or future stability
- `stability_conversion`
  - converts a clean month into future advantage
  - lower immediate body movement acceptable
  - must create lasting upside or access
- `tradeoff_recovery`
  - still net-stabilizing overall
  - costs land on cash, output, or momentum rather than obvious anti-recovery body signs

### Recovery Sign Rules

For events/choices labeled with words like:
- `recovery`
- `relief`
- `stabilize`
- `protect`
- `buffer`
- `pause`
- `rebalance`
- `de-intensify`
- `recover`
- `rest`

The positive branch must not carry obviously incoherent body-state signs unless the wording explicitly says the choice is not actually recovering.

Default sign expectations:
- `stress`: should move down for positive recovery branches
- `energy`: should move up for positive recovery branches
- `life_satisfaction`: usually flat or up unless the fiction clearly implies sacrifice
- `cash` / `promotion_progress` / `education_progress`: valid places to pay the cost

### Consequence Magnitude Rules

Do not use token outcomes for important stabilizers.

General target ranges:
- acute recovery: `stress -4 to -8`, `energy +3 to +6`
- structural stabilization: `stress -2 to -5`, `energy +1 to +4`, plus a real future effect
- stability conversion: `stress -1 to -3` or `energy +1 to +2`, plus a real future effect
- tradeoff recovery: net-stabilizing, with meaningful non-body cost

### Long-Term Consequence Rules

If a choice is framed as structural stabilization, it should also affect at least one of:
- active arc severity/duration
- housing/transport access
- credit trajectory
- education standing/momentum
- career momentum or role-band posture
- monthly cost profile via modifier
- blocked doors / recovery route availability

---

### Task 1: Build Recovery-Semantics Test Harness

**Files:**
- Create: `tests/test_event_semantics.py`
- Reference: `data/events.json`
- Reference: `tests/test_status_arcs.py`
- Reference: `tests/test_event_choices_and_win_states.py`

**Step 1: Write failing tests**

Add tests that collect event choices and events with positive/stabilizing labels or descriptions and assert:
- positive recovery branches are not carrying obviously anti-recovery signs
- acute recovery outcomes move `stress` and `energy` meaningfully
- structural stabilizers must either soften a status arc materially or produce a meaningful non-body future effect

Also add explicit audit tests for known high-value events, including at minimum:
- `burnout_month -> take_real_recovery`
- `overtime_attrition_warning -> rebalance_workload`
- `exam_probation_hearing -> cut_hours_and_recover_standing`
- `lease_enforcement_notice -> pay_to_hold_lease`
- `reserve_deployment_window -> spend_buffer_now`
- `credit_limit_review -> tighten_up`
- `refinance_window -> refinance_now`
- `protect_shift_reliability`
- `protect_recovery_blocks`
- `protect_care_continuity`

**Step 2: Run tests to verify they fail**

Run:
```bash
pytest tests/test_event_semantics.py -q
```

Expected: failures showing sign inconsistencies or low-impact outcomes.

**Step 3: Commit scaffold only after failures are real**

Do not implement yet.

---

### Task 2: Rewrite Acute Recovery And Structural Stabilization Outcomes

**Files:**
- Modify: `data/events.json`
- Modify: `tests/test_event_semantics.py`
- Modify: `tests/test_status_arcs.py`
- Modify: `tests/test_event_choices_and_win_states.py`

**Step 1: Rewrite high-value recovery choices in content**

Adjust immediate and choice effects so positive recovery branches have coherent and meaningful impact.

Focus first on:
- burnout recovery choices
- education recovery choices
- housing stabilization choices
- credit stabilization / refinance choices
- transport-protection choices
- branch-specific “protect” or “stabilize” outcomes

**Step 2: Ensure costs land on the right axis**

When a recovery branch needs a cost, prefer:
- `cash`
- `promotion_progress`
- `education_progress`
- `life_satisfaction`
- temporary income or output modifiers

Avoid body-state punishment on the clearly positive branch unless the wording explicitly says recovery is incomplete.

**Step 3: Run focused tests**

Run:
```bash
pytest tests/test_event_semantics.py tests/test_status_arcs.py tests/test_event_choices_and_win_states.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json tests/test_event_semantics.py tests/test_status_arcs.py tests/test_event_choices_and_win_states.py
git commit -m "feat: rewrite classic recovery event semantics"
```

---

### Task 3: Strengthen Structural Stabilizers In Engine And Arc Resolution

**Files:**
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Test: `tests/test_status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write failing tests**

Add tests showing that structural stabilizers should do more than tiny stat movement.

Examples:
- refinance should materially soften `credit_squeeze`
- reserve deployment should materially soften `lease_pressure`
- real recovery should materially soften `burnout_risk`
- education recovery should materially soften `education_slipping`

**Step 2: Implement minimal engine support**

Use current seams only:
- stronger `refresh_status_arc(...)` deltas on stabilizing branches
- stronger recovery-route effects where appropriate
- clearer scoring benefit from actually executing a stabilizing choice correctly

Do not add a new subsystem.

**Step 3: Run targeted tests**

Run:
```bash
pytest tests/test_status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/budgetwars/engine/status_arcs.py src/budgetwars/engine/events.py src/budgetwars/engine/month_resolution.py src/budgetwars/engine/scoring.py tests/test_status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: deepen classic stabilizer consequences"
```

---

### Task 4: Restore Monthly Cash-Flow Visibility

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/status_bar.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write failing UI tests**

Add tests asserting:
- the top bar shows numeric monthly `Cash Flow`
- the center panel still shows projected turn consequence as `Expected Swing`
- the two labels are not literal duplicates

**Step 2: Implement minimal UI change**

Restore a clear `Cash Flow` number in the status bar.

Keep the center panel’s turn consequence visible, optionally renamed to `Projected Cash Flow Swing` if needed for clarity.

**Step 3: Run tests**

Run:
```bash
pytest tests/games/classic/test_main_window.py -q -k "cash_flow or expected_swing or status_bar"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/status_bar.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_main_window.py
git commit -m "feat: restore classic cash-flow visibility"
```

---

### Task 5: Deepen Branch Futures For Retail, Warehouse, And Office

**Files:**
- Modify: `data/events.json`
- Modify: `data/careers.json`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/careers.py`
- Test: `tests/test_career_progression_v3.py`
- Test: `tests/test_event_choices_and_win_states.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Write failing contrast tests**

For each selected track, assert different branches produce:
- different top event pools
- different promotion-offer pools
- different late-career follow-up events
- different blocked-door or recovery-route patterns when pressured

Start with:
- `retail_service`
- `warehouse_logistics`
- `office_admin`

**Step 2: Add branch-specific content, not just weights**

For each branch, add:
- one stronger upside hook
- one stronger pressure hook
- one recurring promotion fork or late-career follow-up
- one structural stabilizer or failure route that only makes sense for that branch

**Step 3: Run tests**

Run:
```bash
pytest tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py -q -k "retail or warehouse or office"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json data/careers.json src/budgetwars/engine/events.py src/budgetwars/engine/careers.py tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py
git commit -m "feat: deepen retail warehouse office branch futures"
```

---

### Task 6: Deepen Branch Futures For Delivery, Trades, And Healthcare

**Files:**
- Modify: `data/events.json`
- Modify: `data/careers.json`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/careers.py`
- Test: `tests/test_career_progression_v3.py`
- Test: `tests/test_event_choices_and_win_states.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Write failing contrast tests**

Mirror Task 5 for:
- `delivery_gig`
- `trades_apprenticeship`
- `healthcare_support`

**Step 2: Implement branch-specific hooks**

Add stronger branch differentiation in:
- recurring month pressure
- recovery routes under pressure
- later promotion opportunities
- fatigue and reliability tradeoffs

**Step 3: Run tests**

Run:
```bash
pytest tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py -q -k "delivery or trades or healthcare"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json data/careers.json src/budgetwars/engine/events.py src/budgetwars/engine/careers.py tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py
git commit -m "feat: deepen delivery trades healthcare branch futures"
```

---

### Task 7: Deepen Branch Futures For Sales And Degree-Gated Professional

**Files:**
- Modify: `data/events.json`
- Modify: `data/careers.json`
- Modify: `src/budgetwars/engine/events.py`
- Modify: `src/budgetwars/engine/careers.py`
- Test: `tests/test_career_progression_v3.py`
- Test: `tests/test_event_choices_and_win_states.py`
- Test: `tests/test_consequence_depth.py`

**Step 1: Write failing contrast tests**

Focus on:
- volatility vs stability lanes
- specialist vs client/leadership lanes
- post-cap identity differences

**Step 2: Implement stronger branch futures**

Add content so these tracks diverge more clearly in:
- upside windows
- pressure windows
- blocked doors and access needs
- late-career identity events

**Step 3: Run tests**

Run:
```bash
pytest tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py -q -k "sales or professional"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json data/careers.json src/budgetwars/engine/events.py src/budgetwars/engine/careers.py tests/test_career_progression_v3.py tests/test_event_choices_and_win_states.py tests/test_consequence_depth.py
git commit -m "feat: deepen sales and professional branch futures"
```

---

### Task 8: Deepen Medium-Term Scar Content

**Files:**
- Modify: `data/events.json`
- Modify: `data/status_arcs.json`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Modify: `src/budgetwars/engine/month_resolution.py`
- Test: `tests/test_status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`

**Step 1: Write failing tests for stronger scars**

For each arc family, require more bite in at least one deterministic scenario:
- transport instability
- credit squeeze
- education slipping
- lease pressure
- burnout risk
- promotion window

Each scenario should check at least one of:
- stronger follow-up event weight
- stronger blocked door effect
- stronger recovery-route divergence
- stronger score movement

**Step 2: Implement content upgrades**

Add or rewrite arc-coupled events and choices so scars:
- escalate more clearly
- offer more asymmetric resolutions
- interact more with branch/build identity

**Step 3: Run tests**

Run:
```bash
pytest tests/test_status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py -q -k "arc or recovery"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json data/status_arcs.json src/budgetwars/engine/status_arcs.py src/budgetwars/engine/month_resolution.py tests/test_status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py
git commit -m "feat: deepen classic medium-term scars"
```

---

### Task 9: Deepen Wealth Identity Content

**Files:**
- Modify: `data/events.json`
- Modify: `src/budgetwars/engine/wealth.py`
- Modify: `src/budgetwars/engine/scoring.py`
- Modify: `src/budgetwars/engine/status_arcs.py`
- Test: `tests/test_consequence_depth.py`
- Test: `tests/test_month_resolution.py`
- Test: `tests/test_finish_pass_truth.py`

**Step 1: Write failing tests**

Require wealth to diverge more strongly in pressured runs:
- cushion-first under lease pressure
- debt-crusher under credit squeeze
- market-chaser under bad credit or weak liquidity
- steady-builder under clean compounding windows

Also add at least one truth test showing wealth strategy changes memorable run identity, not just return math.

**Step 2: Implement content and consequence upgrades**

Make wealth matter more through:
- stronger pressure-coupled windows
- stronger rescue windows
- stronger downside traps for misaligned strategy
- stronger score identity when the strategy fits the run shape

**Step 3: Run tests**

Run:
```bash
pytest tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_finish_pass_truth.py -q -k "wealth"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add data/events.json src/budgetwars/engine/wealth.py src/budgetwars/engine/scoring.py src/budgetwars/engine/status_arcs.py tests/test_consequence_depth.py tests/test_month_resolution.py tests/test_finish_pass_truth.py
git commit -m "feat: deepen classic wealth identity content"
```

---

### Task 10: Move More Non-UI Logic Out Of `main_window.py`

**Files:**
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Create: `src/budgetwars/games/classic/ui/dialogs.py`
- Create: `src/budgetwars/games/classic/ui/build_snapshot.py`
- Create: `src/budgetwars/games/classic/ui/monthly_forecast.py`
- Create: `src/budgetwars/games/classic/ui/pressure_summary.py`
- Create: `src/budgetwars/games/classic/ui/learn_drawer_builder.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write or adapt smoke tests**

Add tests that import new modules directly and verify:
- dialogs still construct
- snapshot builder still returns the same VM shape
- forecast builder still returns the same VM shape
- pressure summary builder still returns the same VM shape

**Step 2: Move code without behavior change**

Move remaining non-UI assembly out of `main_window.py`, including:
- dialog classes
- snapshot builders
- forecast builders
- pressure summary builders
- learn drawer builders

`MainWindow` should keep wiring and view orchestration only.

**Step 3: Run UI tests**

Run:
```bash
pytest tests/games/classic/test_main_window.py -q
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/budgetwars/games/classic/ui/main_window.py src/budgetwars/games/classic/ui/dialogs.py src/budgetwars/games/classic/ui/build_snapshot.py src/budgetwars/games/classic/ui/monthly_forecast.py src/budgetwars/games/classic/ui/pressure_summary.py src/budgetwars/games/classic/ui/learn_drawer_builder.py tests/games/classic/test_main_window.py
git commit -m "refactor: move classic presentation logic out of main_window"
```

---

### Task 11: Final UI Hierarchy Pass

**Files:**
- Modify: `src/budgetwars/games/classic/ui/panes/status_bar.py`
- Modify: `src/budgetwars/games/classic/ui/panes/life_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/outlook_panel.py`
- Modify: `src/budgetwars/games/classic/ui/panes/finance_panel.py`
- Modify: `src/budgetwars/games/classic/ui/main_window.py`
- Test: `tests/games/classic/test_main_window.py`

**Step 1: Write failing tests for visual hierarchy rules**

Require at minimum:
- top area trimmed and not overloaded with redundant metrics
- center panel remains dominant and focused on the month’s move
- right panel stays diagnosis-only
- left panel remains identity-first
- fewer duplicated labels between center and right
- main screen still fits without primary scrollbars at default preview size

**Step 2: Implement hierarchy cleanup**

Keep this pass about emphasis, not ornament.

Target:
- fewer bordered boxes fighting for attention
- less repeated text
- cleaner top band
- more obvious commitment flow in the center

**Step 3: Run UI tests and do manual preview**

Run:
```bash
pytest tests/games/classic/test_main_window.py -q
```

Manual check:
```bash
.\live_preview_classic.bat
```

**Step 4: Commit**

```bash
git add src/budgetwars/games/classic/ui/panes/status_bar.py src/budgetwars/games/classic/ui/panes/life_panel.py src/budgetwars/games/classic/ui/panes/outlook_panel.py src/budgetwars/games/classic/ui/panes/finance_panel.py src/budgetwars/games/classic/ui/main_window.py tests/games/classic/test_main_window.py
git commit -m "feat: finish classic visual hierarchy pass"
```

---

### Task 12: Final Truth Pass

**Files:**
- Modify: `tests/test_finish_pass_truth.py`
- Modify: `tests/test_consequence_depth.py`
- Modify: `tests/test_career_progression_v3.py`
- Modify: `tests/test_month_resolution.py`
- Modify: `tests/games/classic/test_main_window.py`
- Reference: `docs/plans/2026-04-14-classic-event-content-overhaul-design.md`

**Step 1: Expand deterministic truth gates**

Require the finished game to prove, through tests, that:
- recovery/stabilization choices make sense and matter
- core scars have bite
- branch futures really diverge
- wealth identity is memorable
- blocked doors and recovery routes differ by build
- cash flow is visible again

**Step 2: Run focused final truth suite**

Run:
```bash
pytest tests/test_finish_pass_truth.py tests/test_consequence_depth.py tests/test_career_progression_v3.py tests/test_month_resolution.py tests/games/classic/test_main_window.py -q
```

Expected: PASS.

**Step 3: Run full non-desktop suite**

Run:
```bash
pytest -q -k "not desktop"
```

Expected: PASS.

**Step 4: Commit**

```bash
git add tests/test_finish_pass_truth.py tests/test_consequence_depth.py tests/test_career_progression_v3.py tests/test_month_resolution.py tests/games/classic/test_main_window.py
git commit -m "test: lock classic content overhaul truth gates"
```

---

## Verification Matrix

For every major phase, compare relevant archetypes on:
- top weighted events
- status-arc pressure
- blocked doors
- recovery route availability
- promotion offers
- projected score
- visible UI diagnosis

### Required deterministic archetypes
- stable at-home saver
- debt-heavy renter
- transport-fragile worker
- school-heavy climber
- weak-credit fragile build
- strong-credit stable build

### Required branch contrast groups
- retail branches
- warehouse branches
- office branches
- delivery branches
- trades branches
- healthcare branches
- sales branches
- degree-gated professional branches

---

## Planned Deliverables

By the end of this master plan, Classic should have:
- recovery/stabilization events that read coherently
- positive outcomes that actually matter
- stronger medium-term scars
- stronger branch-specific futures
- stronger wealth identity
- visible monthly cash flow again
- less logic inside `main_window.py`
- a cleaner final screen hierarchy
- deterministic truth tests that prove the rewrite worked
