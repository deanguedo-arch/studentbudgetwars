## Repo Proof Surface Candidate

Repo: studentbudgetwars
Confidence: high
Status: candidate

## Detected Stack
- python

## Detected Proof Commands
- tools/import_costs_from_csv.py
- tools/validate_data.py

## Detected Risky Actions
- No risky live actions detected.

## Proposed Proof Rules
- tests_passed: require local_command_output, target_repo_cwd (package.json scripts)
- data_pipeline_ready: require schema_or_fixture_validation, quality_command_output (data script/path detection)
- repo_identity: require target_repo_cwd, matching_repo_path, matching_worktree_fingerprint (generic STAX sidecar rule)

## Unknowns
- No unknowns recorded.

## Decision Needed
Approve this proof surface, edit it, or keep it candidate-only.
