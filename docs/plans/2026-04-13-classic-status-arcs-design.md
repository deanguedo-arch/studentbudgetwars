# Classic Status Arcs Design

**Date:** 2026-04-13

**Goal**

Add a thin explicit status-arc layer to Classic mode so multi-month consequences become named, legible run conditions without replacing the current event, modifier, or chained-event machinery.

**Why This Exists**

Classic already supports immediate event effects, multi-month modifiers, event choices, chained follow-up events, build-dependent event weighting, and recovery logic. Those mechanics work, but the run still feels too short-memory because the game has no first-class named scar concept. The UI compensates by inferring conditions from raw numbers, blocked doors, and recovery hints, which pushes too much interpretation into the Classic presentation layer.

Status arcs fix that by giving the engine and UI a shared runtime surface for named multi-month conditions such as `Transport Unstable` and `Credit Squeeze`.

## Scope

**V1 proof slice**

- Add status-arc content definitions and runtime state.
- Add lifecycle helpers for starting, refreshing, resolving, and ticking arcs.
- Prove the model with exactly three arc families:
  - `transport_unstable`
  - `credit_squeeze`
  - `education_slipping`
- Surface the top active arcs directly in Classic UI.

**Deferred**

- Event-schema authoring hooks such as `start_status_arc_id`.
- Full migration of trigger routing into content.
- More than one active arc entry per `arc_id`.
- Arc families beyond the first six discussed.

## Architecture

### Existing systems remain authoritative

- **Modifiers** remain the source of ongoing numerical effects.
- **Chained events** remain the source of scheduled follow-ups.
- **Event weighting and severity logic** remain in the existing event engine.

### New layer

- `StatusArcDefinition` lives in content and defines what a player-facing arc is.
- `ActiveStatusArc` lives in runtime state and tracks which arcs currently shape the run.
- `status_arcs.py` owns v1 lifecycle helpers and the proof-arc routing table.

This keeps the new layer additive. Status arcs name the scar, while modifiers and events still do the mechanical work.

## Data Model

### Content model

`StatusArcDefinition` should stay thin and mostly player-facing:

- `id`
- `name`
- `family`
- `summary`
- `default_duration_months`
- `ui_priority`
- `tone`
- `linked_modifier_ids`
- `followup_event_ids`
- `blocked_door_hints`
- `resolution_hint`

These hint fields are presentation only. They must never become authoritative logic.

### Runtime model

`ActiveStatusArc` should remain small:

- `arc_id`
- `source_event_id`
- `remaining_months`
- `severity`
- `started_month`
- `followup_pending`
- `note`

Severity is a bounded integer from `1` to `3`.

### State rules

- One active arc per `arc_id` in v1.
- Retriggering an active arc refreshes or escalates the existing entry.
- Duplicate active entries for the same arc are not allowed.

## Lifecycle

### Start

`start_status_arc(...)`

- Creates the arc if absent.
- Refreshes the existing arc if present.
- Applies or verifies linked modifier state as needed.

### Refresh

`refresh_status_arc(...)`

- Extends duration.
- Can increase severity with a hard cap of `3`.
- Can update the player-facing note.

### Resolve

`resolve_status_arc(...)`

- Removes the active arc.
- Clears any arc-owned lingering state.
- Must not leave stale runtime state or stale UI-visible scars.

### Tick

`tick_status_arcs(...)`

- Runs once per month.
- Decrements remaining duration.
- Auto-resolves expired arcs.
- Can schedule follow-up events if the arc and current build state justify them.

## Integration Rules

### Event engine

For v1, arc trigger mappings stay in code inside `status_arcs.py`.

That routing table maps only the proof slice:

- transport events to `transport_unstable`
- credit pressure events and resolution choices to `credit_squeeze`
- academic decline events and survival choices to `education_slipping`

No new arc hook fields are added to `EventDefinition` or `EventChoice` in v1.

### Access and recovery

Arc presence becomes another input into:

- event weighting
- transport and housing access checks where relevant
- recovery route prioritization
- light score pressure or interpretation

Arcs do not replace these systems. They provide named context to them.

### UI

Classic UI should stop inferring the top scars entirely from raw numbers once arcs exist.

The UI should read active arcs directly and surface:

- top `1-3` active arcs
- severity
- months remaining
- one best resolution line

The diagnosis panel should become simpler because it can point to named ongoing conditions instead of reconstructing them from scattered signals.

## Proof Arcs

### Transport Unstable

Represents an ongoing transport fragility condition after repairs, breakdown shocks, or stopgap commute choices.

Expected impact:

- raises transport-related follow-up pressure
- can narrow work reliability and recovery
- can expose downgrade or workaround choices

### Credit Squeeze

Represents an ongoing credit-pressure state after review penalties, missed-obligation shocks, or tightening access.

Expected impact:

- narrows financing doors
- makes credit-pressure follow-ups more likely
- makes rebuild or refinance choices matter more

### Education Slipping

Represents a sustained academic decline rather than a single bad month.

Expected impact:

- increases education-risk follow-ups
- interacts with intensity and survival decisions
- exposes de-intensify or pause-to-survive choices

## Error Handling and Validation

- Status arc ids referenced in code must exist in content.
- Linked modifier ids and follow-up event ids in arc content must validate against loaded content.
- Severity must stay within `1..3`.
- Duplicate active arcs for the same `arc_id` must collapse into refresh behavior.

## Testing Strategy

### Phase A

- content loading and validation for `status_arcs.json`
- runtime model smoke coverage

### Phase B

- lifecycle tests for start, refresh, resolve, and tick
- uniqueness-by-`arc_id` test
- severity cap test

### Phase C

- deterministic tests proving the three proof arcs start under expected triggers
- tests proving resolution and refresh paths
- contrast tests proving these arcs affect later behavior, not just immediate stats

### Phase D

- Classic UI tests asserting active arcs are surfaced directly
- diagnosis output tests showing the UI consumes arc state rather than reconstructing scars indirectly

## Migration Path

If the proof slice works, a later v2 can move arc lifecycle hooks into event content and gradually reduce the code-owned routing table. That migration should only happen after the semantics of start, refresh, and resolve are stable in play.
