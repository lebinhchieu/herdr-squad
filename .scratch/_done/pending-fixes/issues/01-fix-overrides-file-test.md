# Fix the spawn test that fails on main: test_a_failed_agent_start_leaves_the_old_overrides_file
Duties: Developer builds and writes design notes and technical AC with QA whitebox; QA whitebox code check; QA blackbox behaviour check; hand in to both QAs
Files: bin/squad-spawn, tests/test_squad_spawn.py
Status: ready
After: none

Ticket path: .scratch/pending-fixes/issues/01-fix-overrides-file-test.md (the Developer commits this text there on its branch, FILE-11).
Touched files are an estimate (LC-9b); a change re-issues this file.
Status: needs-triage
Type: task
Source: tl-always E2 (a), Chieu asked for a fix ticket in the next scope (SQ-17).

plugin: 0.10.0 432b8ea8144f6b593e730aebea852e295ac3c945

## Problem
`tests/test_squad_spawn.py` SpawnDryRunTest `test_a_failed_agent_start_leaves_the_old_overrides_file` fails on main. It is listed as `Known failing on base` in 10 or more closed scopes (`grep -rl` over `scopes/_done/*/iterations/*.md`), so each scope re-checks and excuses it.

## AC (draft; the next scope's Tech Lead or Developer settles the technical AC)
- AC1 The test passes on the fix sha: `python3 -m unittest tests.test_squad_spawn` exits 0, with no new skips.
- AC2 The cause is named in `## Review`: a defect in `bin/squad-spawn` (fix the code) or a stale test (fix the test), never deleting the test.
- AC3 Targeted tests (`grep -rl 'overrides' tests/` hits) pass.

## Comments
