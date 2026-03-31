# Weekly Loop

## Current Implemented Loop

1. Show the current week, player resources, debt pressure, and recent message log.
2. Let the player choose one menu action:
   `work`, `rest`, `buy item`, `switch job`, or `save and quit`.
3. If the player buys an item or switches job, apply it immediately and return to the menu for that same week.
4. When the player resolves the week with `work` or `rest`, apply all active temporary weekly effects first.
5. Apply mandatory weekly expenses automatically.
6. Prompt decisions for each optional weekly expense and apply pay or skip outcomes.
7. Optional expense outcomes may also create temporary carryover effects for next week.
8. Apply the chosen weekly action:
   `work` gives job income but costs energy and adds some stress.
   `rest` restores energy and reduces stress.
9. Working can also add a job-specific carryover modifier (for example fatigue or routine effects).
10. Apply current location modifiers once for the week.
11. Roll one random life event and resolve one event choice.
12. Events and event choices can add temporary carryover effects.
13. Apply debt interest and any overdraft handling.
14. Decrement temporary-effect durations and expire them cleanly.
15. Advance the week, autosave, and check for end-of-term success or failure.

The optional-expense layer is intentionally a core pressure system now:
paying helps keep stress/energy stable, while skipping preserves cash but compounds future risk.
Temporary effects make some choices echo into the next week without introducing a heavy status engine.

## Current Failure Conditions

- Stress reaches the configured maximum.
- Energy stays at or below the low-energy threshold for too many consecutive weeks.
- Debt reaches the configured game-over threshold.
- The player has to lean on debt for essentials too many times.

## Planned But Not Yet Implemented

- More weekly actions such as studying or paying down debt.
- Deeper location-driven decisions beyond static weekly modifiers.
- Richer consequences from inventory and recurring lifestyle choices.
- More nuanced budgeting choices than the current one-step weekly action model.
