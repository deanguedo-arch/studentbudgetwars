# Weekly Loop

## Current Implemented Loop

1. Show the current week, player resources, debt pressure, and recent message log.
2. Let the player choose one menu action:
   `work`, `rest`, `buy item`, or `save and quit`.
3. If the player buys an item, apply the item immediately and return to the menu for that same week.
4. When the player resolves the week with `work` or `rest`, apply recurring weekly expenses.
5. Apply the chosen weekly action:
   `work` gives job income but costs energy and adds some stress.
   `rest` restores energy and reduces stress.
6. Roll one random life event and resolve one event choice.
7. Apply debt interest and any overdraft handling.
8. Advance the week, autosave, and check for end-of-term success or failure.

## Current Failure Conditions

- Stress reaches the configured maximum.
- Energy stays at or below the low-energy threshold for too many consecutive weeks.
- Debt reaches the configured game-over threshold.
- The player has to lean on debt for essentials too many times.

## Planned But Not Yet Implemented

- More weekly actions such as studying, paying down debt, or changing jobs.
- Location-driven effects during the actual week loop.
- Richer consequences from inventory and recurring lifestyle choices.
- More nuanced budgeting choices than the current one-step weekly action model.
