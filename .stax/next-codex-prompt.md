STAX Sidecar rejected or held this task because proof is incomplete.

Do exactly one cleanup pass:
Candidate proof surface for tests_passed: Run tools/validate_data.py through stax:collect in the target repo. Suggested command: tools/validate_data.py. This is candidate-only, so treat it as a provisional hint until approved.

Address these proof gaps:
- Command evidence failed: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q -k not status_bar_trims_primary_score_category_bars_from_top_band exited 1.
- Command evidence failed: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q exited 1.
- Proof strength: Reject (0) - Failed command evidence: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q -k not status_bar_trims_primary_score_category_bars_from_top_band exited 1.
- Proof-strength reject: Failed command evidence: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q -k not status_bar_trims_primary_score_category_bars_from_top_band exited 1.
- Proof-strength reject: Failed command evidence: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q exited 1.

Do not broaden scope. Do not claim tests passed without local command evidence. Update .stax/codex-report.md, then stop.
Risk to avoid: Proof-strength blocker: Failed command evidence: /Users/deanguedo/Documents/GitHub/studentbudgetwars/.venv/bin/python -m pytest -q -k not status_bar_trims_primary_score_category_bars_from_top_band exited 1.
