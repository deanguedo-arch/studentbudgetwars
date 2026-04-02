# Active Handoff

## Current State
- Baseline branch: `main`
- Current `main` includes:
  - the monthly after-grad life-sim rebuild
  - consequence-depth systems
  - texture/visibility pass
  - explicit wealth strategy control
  - chained housing/transport/social events
  - `Why This Month Changed` month-driver summary
- Latest known merged `main` commit during this chat: `2b41a5f`
- Validation status: `tools/validate_data.py` passes
- Test status: `39 passed`
- Active roadmap source of truth: `docs/surgical-rebuild-roadmap.md`

## What The Game Is Now
- Title: `After Grad: The First 10 Years`
- Core loop:
  - `1 turn = 1 month`
  - `120 turns = 10 years`
  - start at age 18
  - goal is to reach age 28 in the strongest life position possible
- Main persistent systems:
  - career
  - education
  - housing
  - transport
  - budget stance
  - wealth strategy
- Main pressure stats:
  - cash
  - savings
  - high-interest savings
  - index fund
  - aggressive growth fund
  - debt
  - stress
  - energy
  - life satisfaction
  - family support
  - social stability

## Project Direction
- The framework is no longer the main problem.
- The next pass is not another skeleton rebuild.
- The project goal is now:
  - make the player feel they built or damaged a real decade of adulthood
- Optimize toward:
  - stronger long-term branching
  - realistic time scales
  - delayed payoff
  - stronger opportunity cost
  - bigger upside
  - more believable adulthood milestones
  - more tangible human consequences

## What Landed Recently
- Consequence-depth pass:
  - career switching friction
  - promotion blockers and momentum
  - housing stability and move penalties
  - transport reliability and switch friction
  - education re-entry friction
  - broad wealth/investing layer
  - market regimes
- Texture/visibility pass:
  - separate `wealth_strategy` from `budget_stance`
  - `data/wealth_strategies.json`
  - chained roommate events
  - chained vehicle events
  - parent bailout / parent boundary events
  - sales hot/cold streak events
  - modifier-gated follow-up events
  - `Why This Month Changed` summary in UI

## Most Important Files
- Engine:
  - `src/budgetwars/engine/game_loop.py`
  - `src/budgetwars/engine/month_resolution.py`
  - `src/budgetwars/engine/careers.py`
  - `src/budgetwars/engine/education.py`
  - `src/budgetwars/engine/housing.py`
  - `src/budgetwars/engine/transport.py`
  - `src/budgetwars/engine/events.py`
  - `src/budgetwars/engine/wealth.py`
  - `src/budgetwars/engine/simulation.py`
  - `src/budgetwars/engine/scoring.py`
- Models/loaders:
  - `src/budgetwars/models/core.py`
  - `src/budgetwars/models/content.py`
  - `src/budgetwars/models/state.py`
  - `src/budgetwars/loaders/content_loader.py`
  - `src/budgetwars/loaders/validators.py`
- UI:
  - `src/budgetwars/ui/main_window.py`
  - `src/budgetwars/ui/panes/menu_bar.py`
- Data:
  - `data/config.json`
  - `data/careers.json`
  - `data/education.json`
  - `data/housing.json`
  - `data/transport.json`
  - `data/focus_actions.json`
  - `data/events.json`
  - `data/wealth_strategies.json`
  - `data/presets.json`
  - `data/balance/*.json`

## Current Balance Read
- The game is mechanically working, but balance is not centered yet.
- Deterministic sim snapshot from this chat:
  - `normal + cautious`:
    - survival rate `100%`
    - average final score `76.91`
    - average ending stress `65.39`
    - average ending debt `0`
  - `normal + ambitious`:
    - survival rate `2.9%`
    - average final score `21.38`
    - average ending stress `98.01`
    - most deaths are `burnout_collapse`
- Takeaway:
  - safe play is too safe
  - aggressive play is too punishing
  - stress is the main balance problem
  - the game currently risks making `recovery_month` feel mandatory

## Main Weak Spots
- careers are still too compressed and top out too fast
- school is too short and too gamey
- `Study Push` still risks feeling like fake time compression
- housing is still more pressure than full adulthood progression
- transport still leans more gate/penalty than full life arc
- investing still needs to feel more explicit and player-driven
- social and family context are still too abstract
- event texture is improving, but still not deep enough
- the game is better at punishing instability than rewarding meaningful adulthood wins

## Active Rebuild Priorities
- Priority 1:
  - fix education realism
  - remove fake school acceleration
  - lengthen major program durations
- Priority 2:
  - rebalance stress around medium-risk play
  - reduce push harshness
  - reduce `Recovery Month` dominance
  - create more viable stabilization paths
- Priority 3:
  - expand careers from short ladders into real branches
- Priority 4:
  - add housing progression including ownership
- Priority 5:
  - turn investing into a true strategy layer
- Priority 6:
  - deepen transport lifecycle and event chains
- Priority 7:
  - deepen family, roommate, and social context
- Priority 8:
  - improve causal UI messaging and milestone punch

## Immediate Next Implementation Pass
- Start with Phase 1 and Phase 2 from `docs/surgical-rebuild-roadmap.md`.
- First concrete targets:
  - remove or sharply reduce direct school-time acceleration from focus actions
  - lengthen major program durations in `data/education.json`
  - recenter stress so medium-risk play is viable and `Recovery Month` is not pseudo-mandatory

## Immediate Success Targets
- School should feel like staying on track versus falling behind, not sprinting a degree.
- `normal + cautious` survival should move down from trivial safety into a more earned range.
- `normal + ambitious` survival should move up from near-doomed into risky but recoverable territory.
- `Recovery Month` should be useful, not something the player feels forced to take constantly.
- The decade should begin to feel larger, slower, and more believable.

## Whole-Project Acceptance Test
1. School feels like a long commitment, not a sprintable meter.
2. Careers feel like different lives, not just different pay ladders.
3. Housing includes real adulthood progression, including ownership.
4. Transport shapes opportunity and can become a trap.
5. Investing is a real strategy layer, not a passive side effect.
6. Family/social context affects recovery and collapse in believable ways.
7. Medium-risk play is viable.
8. Early decisions clearly shape the mid-game and late-game.
9. The player feels both pressure and aspiration.
10. The decade feels built, not just simulated.

## Notes For The Next Chat
- Treat current `main` as the only baseline.
- Do not reopen old branch history.
- Use `docs/surgical-rebuild-roadmap.md` as the active roadmap source of truth.
- Do not mistake the current need for another framework pass.
- Fix realism breaks before adding broad new content.
- Use simulation evidence before tuning by intuition.
- Keep early passes surgical and measurable.
