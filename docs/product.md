# Product Overview

Student Budget Wars is a turn-based terminal game about making it through a school term without collapsing financially or mentally.

The player manages a student character across weekly turns. Each week creates tradeoffs between earning money, covering bills, maintaining health and energy, and reacting to unpredictable life events.

Core design goals:

- Easy to run locally
- Strong replayability through random events and different starting presets
- Data-driven content so balancing and writing can happen without rewriting core code
- Modular systems that can be extended independently

## Current Mechanics

- Start from a preset plus difficulty.
- Resolve the term one week at a time in the terminal.
- Choose to work, rest, buy an item, or switch jobs before ending the week.
- Pay mandatory recurring expenses and make explicit decisions on optional upkeep/lifestyle expenses.
- Optional expense decisions can now create short-lived carryover effects for upcoming weeks.
- Gain job income when working.
- Some jobs add small next-week carryover effects, creating stronger week-to-week identity.
- Apply location modifiers once each week.
- Resolve one random event with a choice-based outcome.
- Some events now create temporary consequences that persist into later weeks.
- Lose from stress collapse, low-energy streaks, debt spiral, or repeated essential shortfalls.

## Current Strategic Profiles

- Optional expenses now represent meaningful quality-of-life tradeoffs instead of filler costs.
- Jobs are tuned to distinct survival styles (sustainable, cashflow-heavy, high-strain, high-hourly/low-hours).
- Locations nudge weekly outcomes toward different pressure patterns.
- Presets are intended to feel like different opening problems, not cosmetic stat variants.
- Temporary weekly modifiers let decisions echo forward without adding heavy simulation complexity.

## Planned Mechanics

- More weekly actions and stronger tradeoffs.
- More meaningful use of locations and inventory.
- Better balance across presets, jobs, and event pressure.
- Broader content depth without changing the data-driven structure.
