# T1 · process.md for the Team Lead model, version 4
Status: ready-for-agent
Type: task
Blocked by: none
Repo: /home/chieule/workspace/squad (branch from main c1be501 unless the briefing names a base)
Spec: ../spec.md (B-ids) · Design: ../design.md (decision numbers) · Technical AC: `$SCOPE_DIR/evidence/qa-w-tech-ac.md` (AC ids)

## Files this task touches (and no others)
`templates/squad/process.md`, `skills/squad-process-update/history/process-v4.md` (new), `skills/squad-process-update/changelog.md`, `agents/manager.md` (**only** the `stays within N bytes` bullet in the Writing-rule block: delete it), `bin/processlint.py` (**only** the size check), `tests/test_processlint.py` and `tests/test_process_writing.py` (**only** what pins the size or budget), `tests/test_pod_rules_process.py` (new).

## Do
1. Run `python3 .scratch/tl-manages-team/process-edits.py` from the repo root: it applies the agreed edits (design decisions 1-9, 10) to the template in place and prints size and lint. Then tighten the new and the neighbouring wording. Delete the script in your last commit.
2. **No byte budget (decision 11, PO ruling E2: "Remove the budget completely").** Remove, and nothing else:
   - `bin/processlint.py`: the `size` check, the `budget` parameter of `lint()` and `_problems()`, the `WHOLE_FILE` marker and the "line 0 = whole file" docstring words if nothing else uses them (grep first). Every other check stays; the CLI exit codes stay.
   - `agents/manager.md`: the bullet `The file stays within N bytes. ...` in the Writing-rule block. Keep the other bullets byte for byte.
   - `tests/test_process_writing.py`: the `{N}` placeholder and the budget line in `RULE`, `manager_budget()` and `test_budget_is_one_figure_everywhere`; `RULE` must still equal the Manager's block exactly.
   - `tests/test_processlint.py`: `SizeTest` and `test_size_exception_matches_the_whole_file_marker`; the `budget=` arguments in the remaining tests.
   - Do not touch `docs/adr/0006-process-writing-rule.md` (T6 does). `process.md` itself has no size text.
3. **Version 4:** line 3 `process-version: 4`; `history/process-v4.md` is a byte copy of the template; one `## v4` block in `changelog.md` (format of v3; one item per changed section with `sections:`, `change: rule`, `why`, old and new as `snapshot`, as v2 did). `tests/test_process_history.py` and `tests/test_squadprocess*.py` stay green.
4. No heading added, renamed or removed (`tests/test_process_citations.py` pins 19). S row and S column of the Sizes tables stay byte for byte.
5. New test file `tests/test_pod_rules_process.py` pins, by reading the template: M roles include Team Lead and the duty row "Plan, order, assignment" is `Tech Lead | Team Lead | Team Lead`; the pod-contact and Team-Lead-to-Manager bullets; the `iterations/<n>.summary.md` Files row; the cap bullet's goal-share clause; a `FINAL:` rule covering the Team Lead; the no-relay bullet; the `Down` and Handover clauses; and S text unchanged (S row, "Tech Lead | Team Lead | Team Lead" only in M and L columns).

## Technical AC
AC-1.1 to AC-1.6, AC-2 (every duty the Manager loses names a new owner in `process.md`), AC-8 ordering.
- `python3 bin/processlint.py templates/squad/process.md` exits 0; there is no size limit (a `lint(text)` call with no budget argument works).
- Grep, and list the commands and results in `dev-evidence.md`: `Tech Lead in S and M`, `Plan owner`, `health check`, `Manager never pushes`, `steps in`, `queues the rest`, `Manager spawns`. No line contradicts the new model.
- `squad-process plan --json --squad-dir <copy of .claude/squads/plugin>` runs on a **copy** and reports no error.

## Business AC
B1, B3, B6, B11 (process.md part), B12, B14 (version, snapshot, changelog, lint; its byte-budget words are void by the PO's E2 ruling).

## Out of scope
Any agent file other than the one deleted bullet; settings; bin scripts other than the size check.
