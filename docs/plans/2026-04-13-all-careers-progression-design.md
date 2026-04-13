# Classic All-Careers Progression Design

## Goal

Bring all eight Classic careers up to full progression parity so careers no longer max out too early, promotion choices create durable future differences, and late-career play remains structurally alive after nominal tier cap.

## Problems to Fix

- Promotion progress accumulates too quickly through routine monthly play.
- Tier thresholds are too low, so many careers reach the top too early.
- Max tier is a hard stop instead of the start of late-career identity play.
- Four careers still have no branch structure at all.
- Promotion events and career events mostly create short-term pressure, not durable role identity.
- Event coverage is uneven across careers, so some lanes still feel mostly generic.

## Scope

This pass covers all eight Classic careers:

- `retail_service`
- `warehouse_logistics`
- `delivery_gig`
- `office_admin`
- `trades_apprenticeship`
- `healthcare_support`
- `sales`
- `degree_gated_professional`

For every career, this pass adds:

- at least three real branches
- slower promotion pacing
- recurring promotion fork choices
- post-cap late-career role states
- branch-specific and role-specific long-term events
- durable role tags that change future income, volatility, stress, and event pools

Out of scope:

- Desktop
- broad Classic visual redesign
- replacing the status-arc system
- rewriting the entire event engine

## Recommended Architecture

Use one shared additive progression framework instead of eight separate implementations.

Keep:

- existing `CareerTrackDefinition`, `CareerBranchDefinition`, `CareerTierDefinition`
- existing branch selection flow
- event choices and persistent tags
- status arcs and event weighting

Add:

- richer branch coverage in `data/careers.json`
- higher promotion thresholds across all careers
- a shared tag-driven role-state layer that reads long-term promotion/event choices
- a late-career “role band” model implemented through durable tags plus shared income/stress/volatility adjustments in the career engine

The career engine remains authoritative for:

- monthly income
- monthly stress / energy drift from career identity
- promotion blockers and pacing
- post-cap role-state effects

The event layer remains authoritative for:

- when role forks appear
- what choices the player can make
- which durable tags are written
- how later opportunity/failure hooks differ by branch and role tag

## Career Matrix

Every career follows the same structural rule:

- `3 branches minimum`
- `2 recurring promotion fork windows minimum`
- `1 post-cap late-career layer`
- `1 opportunity hook and 1 failure hook minimum per branch`

### Existing branched careers to deepen

#### Retail / Service

- operations management
- sales performance
- clienteling / key accounts

Late-career role directions:

- crisis lead
- output surge
- sustainable ops
- territory closer
- client-book builder

#### Warehouse / Logistics

- floor operations
- dispatch coordination
- equipment specialist

Late-career role directions:

- foreman / output pressure
- escalation dispatch
- resilience dispatch
- specialist contract lane

#### Office / Admin

- operations desk
- people coordination
- compliance / controls

Late-career role directions:

- execution manager
- culture coordinator
- controls specialist

### Branchless careers that must gain branches

#### Delivery / Gig Work

- route grinder
- platform optimizer
- independent operator

#### Trades / Apprenticeship

- field crew
- precision specialist
- estimator / supervisor

#### Healthcare Support

- floor care
- technical support
- scheduling / coordination

#### Sales

- volume closer
- account manager
- enterprise / strategic seller

#### Degree-Gated Professional

- technical specialist
- client / stakeholder lead
- people / operations manager

## Promotion and Post-Cap Model

### Promotion pacing

Slow routine advancement materially by:

- reducing base monthly promotion gain
- reducing “healthy month” bonus stacking
- raising tier thresholds across every track
- tightening blockers around branch fit, energy, stress, reliability, and credential fit

### Promotion windows

Promotion windows stop being “extra progress” and become conversion points.

Each career family gets recurring event choices that write durable identity such as:

- manager vs specialist
- stable salary vs upside variance
- stretch scope vs consistency
- client-book growth vs operational control
- contract upside vs schedule stability

Those choices must alter:

- long-term income multiplier
- variance
- stress / energy load
- future event pool
- future blockers
- ending interpretation

### Post-cap late-career play

Reaching the last nominal tier no longer ends progression.

Instead, careers enter a late-career role-state game where role tags keep changing the run:

- stable incumbent
- stretched leader
- fragile high earner
- specialist with schedule control
- burnout-prone manager
- reputation-based closer
- compliance-bound operator

This late-career layer is not another raw tier ladder. It is a durable identity layer that keeps future months different.

## Runtime Model

Use durable tags as the first implementation of role state.

Do not add a heavy new role-state machine unless the tag model proves insufficient.

Implementation rule:

- event choices write persistent tags
- career engine reads persistent tags and current branch
- income, variance, stress, promotion pace, and blockers adjust from those tags
- event eligibility and weighting continue to read branch ids plus persistent tags

This keeps the implementation additive and uses the repo’s current strengths.

## Content Strategy

### Careers content

Update `data/careers.json` to:

- add missing branches
- raise `promotion_target` values for every track
- keep five-tier tracks but treat them as the opening/midgame ladder

### Events content

Expand `data/events.json` with:

- recurring fork events for all careers
- branch-specific opportunity events for all branches
- branch-specific pressure/failure events for all branches
- post-cap role-band events keyed by persistent tags

Every new event must either:

- write a durable role tag
- reinforce an existing role tag
- punish the weakness of a role tag
- reward the strength of a role tag

If it only changes stress and cash without future identity impact, it should not be added.

## Scoring and Endings

Scoring must reward:

- branch commitment
- durable role quality
- stable high-quality advancement
- surviving late-career pressure without collapse

Scoring must punish:

- fragile high-income identity
- unresolved role-specific failure pressure
- uncommitted or flat late-game career states

Endings should name not just the track, but the career shape the player built.

## UI Scope

No broad redesign in this pass.

Only enough Classic UI work to expose:

- current branch
- key persistent career identity tags in summary language
- late-career role identity in build and end-state interpretation
- promotion windows as real long-term forks, not generic progress boosts

## Testing Strategy

Required deterministic checks:

- advancement pacing does not hit cap absurdly early for each career
- each career exposes three branches
- promotion forks create different future states
- late-career role states alter future events and scoring
- post-cap runs in the same career diverge by role tags
- same-income runs with different role quality do not score the same

Minimum test coverage:

- branch unlock test per career
- branch event divergence test per career
- promotion fork test per career
- post-cap role-state divergence test per career family
- scoring divergence tests for durable role quality

## Success Criteria

This pass succeeds only if:

- all eight careers have real branches
- careers no longer top out too early in ordinary good runs
- promotion events create durable pay/risk identity
- post-cap careers still have real decisions and consequences
- events feel career-shaped instead of generic
- different branches and role paths in the same career lead to visibly different futures
