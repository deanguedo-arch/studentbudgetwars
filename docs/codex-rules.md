# Codex Rules For Future Passes

- Do not collapse core systems into one file.
- Keep state mutation separate from terminal rendering.
- Keep tunable content in `data/*.json`.
- Validate JSON content at load time.
- Prefer typed models over loose dictionaries.
- Avoid hardcoded content-specific player attributes.
- Keep randomness injectable or seedable for tests.
- Add features in focused modules with clear ownership.
- Keep carryover/temporary effects lightweight, typed, and validator-backed.
- Reuse the non-interactive simulation tooling for balance checks before large tuning passes.
- Do not add a database for v1.
- Do not add a web frontend for v1.
- Prefer small, safe extensions over speculative complexity.
