# Classic Finish Pass Design

**Date:** 2026-04-13
**Branch:** `feature/classic-finish-pass-v1`
**Scope:** Classic mode only

## Goal

Finish the current Classic direction without restarting architecture. The remaining work is to make consequence systems stronger, make recovery outside hometown achievable, deepen long-term arc content, strengthen branch and wealth identity, simplify the main screen hierarchy, and then rebalance against deterministic contrast scenarios.

## Current Baseline

Classic already has:
- a split UI surface instead of a single overloaded `main_window.py`
- a real status-arc layer (`status_arcs.py`, `status_arcs.json`, `StatusArcDefinition`, `ActiveStatusArc`)
- all-careers branch structure and post-cap role-band support
- deterministic contrast tests for several major systems

The project no longer needs another architecture pass. It needs stronger content, stronger monthly consequence flow, and clearer emphasis on the main screen.

## Remaining Workstreams

The finish pass will run in this order:
1. `stress recovery v2`
2. `status-arc content v2`
3. `career futures v3 follow-through`
4. `wealth identity v2`
5. `classic ui hierarchy simplification`
6. `final contrast / balance truth pass`

This order is deliberate. Stress recovery feeds arc pressure and monthly survivability. Arc depth feeds career and wealth feel. UI cleanup should happen after the content it needs to surface is real.

## Workstream 1: Stress Recovery V2

### Problem

Outside `hometown_low_cost`, stress often feels like a one-way ratchet. Stable runs in `mid_size_city` and `high_opportunity_metro` do not recover often enough on normal difficulty, which makes those locations feel structurally hostile instead of demanding.

### Approach

Keep the current `stress` and `energy` resources. Do not add a new fatigue subsystem.

Resolve monthly stress as a balance between:
- `pressure load`
- `recovery capacity`

`pressure load` continues to come from focus strain, city pace, instability, debt pressure, low energy, and severe active arcs.

`recovery capacity` becomes explicit and is driven by:
- baseline config relief
- focus choice (`recovery_month` strong, `social_maintenance` moderate, `move_prep` slight)
- housing stability / recovery quality
- transport reliability
- support and social footing
- non-negative surplus / breathing room
- absence of severe arc pressure

### City Identity Rules

- `hometown_low_cost` remains the easiest place to recover
- `mid_size_city` becomes neutral enough that stable runs can cool down
- `high_opportunity_metro` stays hardest, but stable runs can still reduce stress when the player earns that outcome

### Hard Rules

- do not globally flatten city identity
- do not solve this by only buffing `recovery_month`
- stable metro runs on normal must be able to lower stress
- fragile metro runs must still spiral

## Workstream 2: Status-Arc Content V2

### Problem

The arc architecture is correct, but the content footprint is still too narrow. Arcs exist and are visible, but too many runs still feel like events happen and then evaporate.

### Approach

Keep the explicit status-arc layer and deepen content, not architecture.

For each of the existing arc families:
- add stronger triggers
- add stronger escalation behavior
- add more follow-up choices
- add more build-dependent resolution paths
- add more access consequences where appropriate

Target families:
- transport instability
- credit squeeze
- education slipping
- lease pressure
- burnout risk
- promotion window

### Hard Rules

- no new state-machine rewrite
- do not move all trigger hooks into content in this pass
- prefer fewer higher-impact arcs over more filler events

## Workstream 3: Career Futures V3 Follow-Through

### Problem

All careers now have branch structure and late-career support, but the futures still need more divergence. Promotion and branch identity are better than before, but still not strong enough relative to the rest of the shell.

### Approach

Deepen branch-specific futures rather than adding new career families.

For all current careers:
- strengthen recurring promotion forks
- write more durable state from role choices and failures
- deepen branch-specific event hooks
- improve post-cap divergence between stability, scope, and upside paths

### Hard Rules

- do not add more careers
- do not revert to linear promotion bars
- durable career identity must affect later event pools and score interpretation

## Workstream 4: Wealth Identity V2

### Problem

Wealth is functioning, but it is still not one of the strongest run-defining identities. Credit, careers, and scars currently read more clearly than wealth strategy.

### Approach

Keep the four wealth signatures and deepen their risk style.

Each strategy should have:
- clearer upside months
- clearer bad-month pain
- more visible recovery implications
- stronger interaction with status arcs and event pools
- clearer score interpretation

### Hard Rules

- do not add realism clutter like taxes or account-type simulation
- keep wealth mechanical identity broader and more visible, not more complicated

## Workstream 5: Classic UI Hierarchy Simplification

### Problem

The screen is structurally better but still reads too much like software. Too many framed zones and duplicated concepts make the screen feel heavier than the month deserves.

### Approach

Do a hierarchy pass after systems are stronger.

Primary goals:
- reduce duplicated diagnosis language
- make the center panel the dominant commit zone
- make the left panel more identity-first
- make the right panel more purely diagnostic
- trim the top status area
- reduce main-screen visual clutter and repeated framed subzones

### Hard Rules

- do not widen into Desktop
- do not do a pure theme pass
- do not add explanation to compensate for weak systems

## Workstream 6: Final Contrast / Balance Truth Pass

### Problem

After the system passes, the game still needs a truth pass against deterministic fixtures so that the new structure produces real contrast instead of implied contrast.

### Approach

Use deterministic fixtures and compare:
- event pool
- arc presence and severity
- blocked doors
- promotion offers / role bands
- recovery route availability
- stress movement
- score movement

Target archetypes include:
- stable at-home saver
- debt-heavy renter
- transport-fragile worker
- school-heavy climber
- weak-credit fragile build
- strong-credit stable build

### Hard Rules

- if deterministic contrast does not show meaningful differences, the phase is not complete
- do not treat text-only diagnosis differences as sufficient

## Testing Strategy

Each workstream must follow TDD and end with:
- targeted tests for the new behavior
- the relevant deterministic contrast check
- a brief summary of what changed and what remains deferred

Regression baseline for this worktree at start:
- `..\\..\\.venv\\Scripts\\python.exe -m pytest -q -k "not desktop"`
- result: `270 passed, 2 skipped, 7 deselected`

## Non-Goals

- no Classic architecture restart
- no Desktop work
- no giant finance simulator
- no broad schema churn unless the new behavior is already proven

## Success Criteria

The finish pass is complete when:
- stress is recoverable outside hometown for stable runs
- status arcs feel like lasting run conditions, not labels
- career branches produce more visibly different futures
- wealth strategies feel like distinct risk styles
- the main screen feels less like a dashboard and more like a turn board
- deterministic contrast tests prove the differences
