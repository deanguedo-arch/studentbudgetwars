# Classic Master Repair Roadmap

**Goal:** Turn Classic into a stateful consequence strategy game where player choices produce different months, different futures, and different recovery options.

## Current State

Classic already has:
- stronger player-facing UI structure
- consequence matrix loading and validation
- build-dependent event weighting
- event severity scaling
- initial career branch and promotion scaffolding
- initial credit and recovery logic

Classic still lacks:
- enough branch-specific situations
- enough wealth-specific situations
- enough late-run divergence
- enough promotion choice depth
- enough credit-as-access consequences

## Priority Order

1. `stateful-situations-v2`
2. `career-branches-v2`
3. `credit-access-pressure-v2`
4. `wealth-risk-signatures-v1`
5. `recovery-routes-v1`
6. `score-consequence-rework`
7. `victory-state-rework`

## Hard Gates

1. Events must become materially build-dependent before more explanation-heavy UI work.
2. At least two career families must support three materially different branches each.
3. Credit must open and close real housing, transport, refinance, and recovery doors.
4. Wealth must create distinct risk profiles instead of simple allocation math.
5. Recovery routes must be build-dependent, not generic forgiveness.
6. Score changes must reflect consequence management, not passive stat drift.

## Contrast Scenarios

Every major phase should be tested against these builds:
- stable at-home saver
- debt-heavy renter
- transport-fragile warehouse worker
- school-heavy climber
- weak-credit strained builder
- strong-credit stable builder

## This Pass

This pass starts `stateful-situations-v2` by:
- extending event content to target `career branch` and `wealth strategy`
- adding branch-specific situations for retail and warehouse lanes
- adding wealth-strategy situations so liquidity/risk posture changes the month
- increasing branch depth for retail and warehouse from two branches to three

## Deferred

Still deferred after this pass:
- repeated promotion choice nodes with stronger future divergence
- credit as a full door system
- deeper wealth downside/upside mechanics
- branch-aware recovery routes
- score and victory-state rework
