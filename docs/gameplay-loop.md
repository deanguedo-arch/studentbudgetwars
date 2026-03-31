# Weekly Loop

## Current Implemented Loop

1. Show a compact tactical dashboard with status, location/job context, week outlook, and recent activity.
2. Let the player choose one menu action:
   `work`, `rest`, `move location`, `switch job`, `buy item`, or `save and quit`.
3. If the player moves location, switches job, or buys an item, apply it immediately and return to the menu for that same week.
4. When the player resolves the week with `work` or `rest`, apply all active temporary weekly effects first.
5. Apply mandatory weekly expenses automatically.
6. Prompt decisions for each optional weekly expense and apply pay or skip outcomes.
7. Optional expense outcomes may also create temporary carryover effects for next week.
8. Apply the chosen weekly action:
   `work` gives job income but costs energy and adds some stress.
   `rest` restores energy and reduces stress.
9. Working can also add a job-specific carryover modifier (for example fatigue or routine effects).
10. Apply current location modifiers once for the week.
11. If working away from the job's home location, apply extra offsite strain penalties.
12. Roll one random life event and resolve one event choice.
13. Events and event choices can add temporary carryover effects.
14. Apply debt interest and any overdraft handling.
15. Compress routine bookkeeping log lines into compact weekly summaries.
16. Decrement temporary-effect durations and expire them cleanly.
17. Advance the week, autosave, and check for end-of-term success or failure.

The optional-expense layer is intentionally a core pressure system now:
paying helps keep stress/energy stable, while skipping preserves cash but compounds future risk.
Temporary effects make some choices echo into the next week without introducing a heavy status engine.
Location is now a central tactical lever because it can reduce pressure, shape weekly modifiers, and interact with work-week strain.

## Current Failure Conditions

- Stress reaches the configured maximum.
- Energy stays at or below the low-energy threshold for too many consecutive weeks.
- Debt reaches the configured game-over threshold.
- The player has to lean on debt for essentials too many times.

## Planned But Not Yet Implemented

- More weekly actions such as studying or paying down debt.
- Deeper location-driven decisions beyond static weekly modifiers and offsite work penalties.
- Richer consequences from inventory and recurring lifestyle choices.
- More nuanced budgeting choices than the current one-step weekly action model.
