# Classic Status Arcs Wave 2 Design

## Goal

Extend the explicit Classic status-arc layer with the second wave of named scars and opportunities so housing instability, burnout pressure, and promotion openings affect later months as recognizable run states instead of isolated event hits.

## Scope

This pass adds only:

- `lease_pressure`
- `burnout_risk`
- `promotion_window_open`

This pass also tightens the Classic UI so the center and right panels treat active arcs as first-class monthly context instead of mixing them back into generic pressure prose.

Out of scope:

- content-authored arc hooks on `EventDefinition` or `EventChoice`
- new arc families beyond the approved second wave
- Desktop work
- broad cosmetic theming

## Architecture

Keep the existing status-arc architecture intact:

- `StatusArcDefinition` stays content-authored in `data/status_arcs.json`
- `ActiveStatusArc` stays runtime-authored in state
- trigger mappings remain code-owned in `src/budgetwars/engine/status_arcs.py`
- modifiers and chained events remain the mechanical backbone

Each new arc stays unique per `arc_id`. Retriggers refresh or escalate the same active arc rather than creating duplicates.

## Arc Behaviors

### Lease Pressure

Purpose: turn housing squeeze into a remembered run condition.

Trigger set:

- `rent_increase` starts a mild version when rent shock hits an already fragile lane
- `lease_default_warning` starts or escalates the arc sharply
- `lease_enforcement_notice` refreshes or escalates it to the highest pressure state

Effects:

- raises the weight of later lease-default and enforcement pressure
- feeds blocked-door and recovery diagnosis
- slightly penalizes score while active
- makes housing downgrade or fallback recovery read as the cleanest resolution

Resolution:

- accept downgrade / fallback housing line
- stabilize the lease through payment without further missed obligations

### Burnout Risk

Purpose: make overwork and recovery a multi-month condition instead of a one-shot crash.

Trigger set:

- `overtime_attrition_warning` starts the arc
- `burnout_month` escalates it

Effects:

- raises the weight of later burnout follow-ups
- adds pressure to score while active
- improves recovery-route prioritization toward de-intensify / recovery focus
- makes promotion pushes less attractive while the scar is live

Resolution:

- rebalance workload
- stop forcing overtime / promotion-hunt pressure
- survive a cleaner month with restored energy

### Promotion Window Open

Purpose: turn advancement openings into a multi-month opportunity arc instead of a one-screen popup.

Trigger set:

- `promotion_window` starts the arc
- taking the aggressive branch choice refreshes or intensifies opportunity pressure
- taking the steadier branch choice extends it at lower severity
- pending branch decisions can keep the arc live when promotion momentum is real

Effects:

- raises the weight of future promotion windows and branch-adjacent opportunity events
- boosts score lightly while active
- sharpens diagnosis toward “convert the window now” instead of generic career advice

Resolution:

- convert the window into promotion progress / branch choice
- let the opportunity expire through neglect or rising stress

## UI Changes

This is a hierarchy pass, not a theme pass.

Center panel:

- surface the top active arc above driver notes
- make the active arc feel like the month’s remembered context
- reduce duplicate warning prose when an arc already explains the threat

Right panel:

- let the diagnosis area lead with top active arcs
- show best recovery / conversion guidance tied to arcs first
- demote generic pressure copy when a named scar or opportunity exists

## Testing

Add deterministic tests for:

- lease arc start/escalation and housing-pressure contrast
- burnout arc start/escalation and recovery-weight contrast
- promotion arc start/persistence and future opportunity contrast
- Classic UI surfacing of the new arcs in diagnosis/forecast

Regression gate:

- full `pytest -q -k "not desktop"`

Contrast gate:

- one deterministic weak-housing vs stable-housing comparison
- one deterministic overloaded vs stabilized worker comparison
- one deterministic promotion-ready vs flat-momentum comparison

## Success Criteria

The pass is successful only if:

- the new arcs persist across months and remain unique per `arc_id`
- later event pressure differs while the arc is active
- recovery or conversion guidance changes because of the active arc
- the Classic UI names the top arc directly instead of reconstructing the situation from raw stats
