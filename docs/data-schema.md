# Data File Intent

## `config.json`

Global runtime settings:
- day/week/term length
- stat bounds
- survival thresholds
- weekly cost totals
- interest rates
- event odds
- study/rest values
- autosave name

## `districts.json`

District definitions for the city/campus map.

Each district includes:
- travel cost
- travel energy/stress impact
- local risk
- event tags
- commodity biases
- local services
- local gigs

## `commodities.json`

Tradable market goods.

Each commodity includes:
- id / name / description
- min/max price
- typical range
- volatility
- backpack size
- district biases
- rare-event tags

## `gigs.json`

District-based hustle opportunities.

Each gig includes:
- availability districts
- pay
- energy cost
- stress delta
- heat delta
- GPA gate
- required item ids

## `items.json`

Support items the player can carry and use.

Each item includes:
- price
- backpack size
- allowed districts
- use effects

Valid effect keys:
- `cash`
- `debt`
- `bank_balance`
- `energy`
- `stress`
- `heat`
- `gpa`
- `study_points`

## `services.json`

Local district services.

Current service kinds:
- `bank`
- `supply_shop`

## `events.json`

Board-level and daily events.

Each event includes:
- trigger: `weekly`, `daily`, or `any`
- weight
- duration in days
- event tags
- market multipliers
- optional district-specific market multipliers
- immediate stat effects
- log entry

## `presets.json`

Starting archetypes.

Each preset defines:
- starting cash / debt / bank balance
- starting energy / stress / heat / GPA
- starting backpack capacity
- starting district
- starting support items

## `data/balance/difficulty_modifiers.json`

Difficulty-level multipliers and bonuses:
- starting cash/debt shifts
- rent multiplier
- debt-interest multiplier
- price-spread multiplier
- study-requirement multiplier
- energy-recovery multiplier
- stress multiplier

## `data/balance/price_curves.json`

Global market-generation knobs:
- base randomness
- scarcity multiplier range
- flood multiplier range

## `data/balance/exam_weeks.json`

Academic checkpoint definitions by week:
- required study points
- GPA penalty / reward
- stress delta
