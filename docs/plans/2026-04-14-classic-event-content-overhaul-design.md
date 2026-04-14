# Classic Event Content Overhaul Design

**Goal:** Make positive and stabilizing Classic events semantically coherent, materially consequential, and visibly tied to run health, while deepening branch futures, medium-term scars, wealth identity, remaining UI clarity issues, and restoring monthly cash-flow visibility.

## Problem Statement

Classic now has the right architecture, but the remaining weakness is content truth.

The current issues are:
- some recovery or stabilization outcomes carry signs that do not match their fiction
- many positive outcomes are too small to matter in score, arc pressure, or future progress
- career structure is ahead of career content, so different branches still do not always create clearly different futures
- medium-term scars exist, but still need stronger escalation, stronger resolution, and more build-specific consequences
- wealth participates in the system, but still lags career and credit as a run identity
- `main_window.py` still owns too much non-UI assembly logic
- the UI is smart but still too dashboard-like
- monthly cash flow is not surfaced prominently enough anymore

## Constraints

- Classic mode only
- no Desktop work
- no architecture restart
- keep explicit status arcs, all-careers progression, and current scoring model shape
- prefer content and consequence depth over new system invention
- execute in deterministic, test-first slices even if the master plan is broad

## Core Design Decisions

### 1. Rewrite the positive/stabilizing event taxonomy, not the whole engine

The next pass should not add another new system. It should rewrite how the content uses the current systems.

Positive and stabilizing outcomes will be treated as four content categories:
- `acute_recovery`: immediate body-state repair; strong stress relief, strong energy recovery, short-term cost acceptable
- `structural_stabilization`: improves future survivability; softens arcs, improves access, or restores housing/credit/education/career footing
- `stability_conversion`: converts a clean month into durable upside; smaller body effect, stronger long-run effect
- `tradeoff_recovery`: still net-stabilizing, but the cost lands on money, output, or momentum rather than obviously anti-recovery body signs

This is a taxonomy rewrite, not a new runtime subsystem.

### 2. Positive outcomes must be consequential

Recovery or stabilization should stop feeling like `-1 stress, +1 energy` filler.

The rule will be:
- acute stabilizers should create visibly meaningful stress/energy movement
- structural stabilizers should materially affect arc severity, blocked doors, access, standing, momentum, or modifiers
- when a choice is framed as protective or stabilizing, its net effect must feel stabilizing in the dimensions the player actually experiences

### 3. Career content must catch up to career structure

The branch scaffolding is now real. The remaining work is content divergence.

A branch is only successful when it changes:
- likely event pools
- promotion offer shapes
- risk/reward profile
- blocked doors and recovery routes
- late-game identity and score interpretation

This pass should deepen branch-specific content and not mistake branch count for branch quality.

### 4. Medium-term scars stay the backbone of remembered play

The current arc layer is correct. The missing work is more bite.

The six core arc families remain:
- transport instability
- credit squeeze
- education slipping
- lease pressure
- burnout risk
- promotion windows

The pass should deepen them through stronger triggers, stronger escalations, stronger resolution outcomes, and more branch/build-dependent interactions.

### 5. Wealth must become a stronger run identity

Wealth should stop feeling like a side allocation system and become a real answer to pressure.

That means:
- better pressure interactions
- clearer opportunity windows
- stronger downside signatures
- stronger end-of-run identity effects

### 6. Cash-flow truth should be visible at a glance

The screen should show both:
- persistent monthly `Cash Flow` in the top bar
- projected turn consequence as `Expected Swing` in the center panel

That avoids duplication while restoring a critical health number.

### 7. UI work should continue to remove interpretation clutter

The final UI work should continue the current direction:
- left side: identity first
- center: the move this month
- right side: diagnosis only

Also:
- move more presentation assembly out of `main_window.py`
- keep reducing repeated information
- keep reducing scrollbars and equal-weight panels

## Success Criteria

This overhaul is successful when:
- positive recovery and stabilization choices make intuitive sense on their face
- those outcomes create meaningful score and future-state movement
- branches produce clearly different futures in play, not just in data
- status arcs feel sharper and more memorable
- wealth creates more memorable pressure and recovery identities
- `main_window.py` loses more non-UI assembly logic
- monthly cash flow is visible again without reintroducing clutter

## Non-Goals

- no Desktop changes
- no new major subsystem replacing status arcs, modifiers, or chained events
- no broad cosmetic theme rewrite disconnected from gameplay meaning
- no one-shot all-event rebalance without phase-level tests
