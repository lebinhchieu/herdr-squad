# 02 Token Coach is spawned with a prompt; Manager waits for its message
Status: ready-for-agent
Type: task

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; QA whitebox runs the full suite once on the final sha. Commit this task file as the ticket at `.scratch/coachwait-closelocal/issues/NN-<slug>.md`, evidence at `.../NN-<slug>/evidence.md`. Base: main. Brief: `$SCOPE_DIR/scope.md`, plan `$SCOPE_DIR/iterations/1.md`.

Touched files: `templates/squad/process/iterations.md` ([ITER-6] and neighbours), `bin/squad-spawn` (warning only), tests (new or an existing rules/spawn test file; find via `tests/test_squad_spawn*.py`, `tests/test_retro_rules.py`). If the composed rules or goldens change, refresh them as the previous squad-close scope did (see `git show 6ebcfbd 03` for the pattern). Do not touch `bin/squad-close`.

## Root cause (PO saw the coach pane idle, no prompt)
[ITER-6] tells the Manager to run `squad-spawn token-coach <name> --scope <scope>` with no `--prompt`; `bin/squad-spawn` sends a first message only when `--prompt` is set (~L318), so the coach starts idle and never writes `iterations/<n>.coach.md`. The Manager then polled `ls | grep -i proposal` in the scope root (wrong place, wrong name) for ~9 min.

## Business AC
1. [ITER-6] (the spawn line) includes `--prompt` with: scope and folder, size, the exact output file (`iterations/<n>.coach.md`, or `coach/<goal>.coach.md` for a goal), "read `squad-usage`, `usage-events.jsonl`, earlier backlogs", "message the Manager (file + proposal count) when done".
2. A rule (in [ITER-6] or next to it) says the Manager, after spawning the coach, does other work or ends its turn and waits for the coach's message; it never loops, sleeps or polls for the file. It checks the coach's pane only via `herdr agent list`, and only if no message came after the usual health-check idle window.
3. `squad-spawn` prints one stderr warning, never failing, when a non-manager role is spawned without `--prompt` (an unbriefed agent sits idle). Spawn behaviour otherwise unchanged.
4. The rules lint (`squad-process lint`) passes; writing rules ([ITER-6] stays one rule, names who acts, when, limit).

## Technical AC (QA whitebox; agreed unless the Developer counters here)
T1. ITER-6 stays one rule (`squad-process lint` passes) and contains: `--prompt`, the output path (scope and goal forms), the usage inputs, "message the Manager". The wait/no-poll text (no loop, no sleep, no polling for the file; `herdr agent list` only after the idle window) is in ITER-6 or a new rule beside it with `roles: manager`; rule IDs cited elsewhere still resolve (`tests/test_process_citations.py`).
T2. ITER-7 (coach side) is consistent with the prompt: same file name and message content; no contradiction between the two rules.
T3. `bin/squad-spawn` warning: one stderr line, printed only when `--prompt` is empty and role != manager; exit code and stdout JSON unchanged; no early exit before the warning on dry-run paths the tests use. Tests (red first on old code): dev and token-coach without `--prompt` warn; manager without `--prompt` does not; any role with `--prompt` does not; stdout still valid JSON / exit 0.
T4. Rules tests assert the actual wording (the `--prompt` flag and path in the composed Manager rules), not just rule existence; goldens refreshed only where the composed text changed, and the refresh diff is reviewed (no unrelated golden churn).
T5. `bash -n bin/squad-spawn`; `git diff --stat main` lists only iterations.md, `bin/squad-spawn`, tests/goldens, ticket/evidence; `bin/squad-close` untouched.
T6. Real sample (REV-4/5b): the Developer shows one real `squad-spawn` stderr from a run without and with `--prompt` (stub herdr), including the idle/no-prompt case.

## Design notes
- ITER-6 (≤60-word lint limit): spawn line with `--prompt`. New ITER-6c: Manager waits, never polls; `herdr agent list` only after the 10-min idle window ([MSG-8a]). ITER-7 already matches the prompt (file name, message content); unchanged.
- `bin/squad-spawn`: one stderr warning when role != manager and no `--prompt`; before `--dry-run`, exit/stdout unchanged.
- Changelog v7: ITER-6c added, ITER-6 retargeted. One existing test passed `--prompt` to stay about settings. `process.md` (legacy v6) not touched. No goldens changed. Agreed T1-T6.
