# Codex Rules For Future Passes

- Preserve the daily market loop. Do not drift back into a passive weekly life-manager spine.
- Keep market, travel, gigs, study, events, inventory, scoring, and UI in separate modules.
- Keep content JSON-driven.
- Validate new JSON content on load.
- Prefer typed models over ad hoc dictionaries.
- Keep randomness deterministic when a seed is supplied.
- Reuse the simulation tooling before large balance passes.
- Treat Tkinter UI code as rendering/input only; keep rule logic in `engine/`.
- Avoid giant UI rewrites unless the loop model changes.
- Do not add a database or web frontend.
- Expand the board with discipline: more opportunity, not more administrative chores.
