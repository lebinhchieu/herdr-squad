# 02 evidence

## Behaviour
Rule text only; no UI. New rule `ITER-19 Routine gates` (roles: manager) holds the 5-row gate table, the `[info] <scope> closed|started; say undo` `read` notice, the non-blocking full-suite ask (`--blocks ""`), and "with `away` set nothing here changes ([ITER-17])".

Changed to match: `ITER-11`, `ITER-5` (check-in item), `CLOSE-1`, `CLOSE-3b`, `GOAL-1`, `GOAL-6b`, `SUITE-1`, `SUITE-1b`, `SUITE-2d`, `SUITE-3`, `SUITE-3b`, repo `CLAUDE.md` "Running tests". `ITER-17` has no hunk. `grep -rn "PO confirms the close\|PO said yes\|and the PO's yes" templates agents CLAUDE.md` finds nothing left. `agents/` had no hit.

Not changed: `ITER-4` (already allows `--blocks ""`). Version not bumped (rides 05); changelog bullets added under a new `## v29` heading, no version line (05 writes it).

Tests (SQUAD_* unset, targeted): `bin/squad-process lint` exit 0; `test_rules_wording` (31, incl. the new `RoutineGatesTest`), `test_instructions`, `test_rules_contract`, `test_processlint`, `test_windows_safe`, `test_utf8_helpers`, `test_small_files_equivalence`, `test_sizes`: OK.
Known failing on base: `test_dev_rules_size::test_every_team_set_fits_the_limit` (5692 B > 5580 on 5c0d5cd; with this change 5689 B, no growth).

## Checks

<!-- Dev column filled; QA columns are theirs. -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 gate list, lint 0 | `python3 bin/squad-process lint` exit 0; `tests/test_rules_wording.py::RoutineGatesTest` | `python3 bin/squad-process lint` exit 0; ITER-19 has the 5 gate rows; `cd tests; python3 -m unittest test_rules_wording test_rules_contract test_processlint test_instructions` OK | `squad-process lint` exit 0 at e2b05c8; ITER-19 table has the 5 gate rows; test_rules_wording 31 ok |
| AC1b suite ask non-blocking | same test (`non-blocking`, `--blocks ""`); `grep -n "non-blocking" CLAUDE.md templates/squad/process/suites.md` | ITER-19 `--blocks ""`, nothing waits, `[warn] full suite: not answered`; `grep -n non-blocking CLAUDE.md templates/squad/process/suites.md` | ITER-19 says `--blocks ""`, nothing waits, check-in/merge item carries `[warn] full suite: not answered`; CLAUDE.md lines 46/48 and SUITE-1/1b/2d say non-blocking; test_rules_contract 18 ok |
| AC2 away unchanged | `git diff HEAD~2 -U0` shows no hunk inside ITER-17; test asserts `nothing here changes ([ITER-17])` | `git diff 5c0d5cd e2b05c8 -U0 -- templates/squad/process/iterations.md`: no hunk inside ITER-17 | `git diff -U0` hunks vs ITER-17 line: untouched. qa-b.md row AC2 |
| AC3 read item, `[info]`, undo | `grep -n "say undo" templates/squad/process/iterations.md` | `grep -n "say undo" templates/squad/process/iterations.md`; ITER-19 names `--kind read` | ITER-19 line 2 of the list: `squad-inbox add --kind read`, `[info] <scope> closed; say undo` |
| AC4 changelog, no bump | `git diff HEAD~2 -- skills/squad-process-update/changelog.md`; no `plugin.json` change (bump rides 05) | `git diff 5c0d5cd e2b05c8 --stat` touches no version file; `grep -n "^## v29" skills/squad-process-update/changelog.md` | changelog v29 bullets present; no plugin.json change in `git diff --stat`; bump rides 05 |

## QA whitebox

### QA whitebox 02, sha e2b05c8 (base 5c0d5cd)

Verdict: PASS. Method: detached worktree at e2b05c8, SQUAD_* unset, PYTHONDONTWRITEBYTECODE=1.

#### Checked
- `squad-process lint` exit 0.
- test_rules_wording (31), test_rules_contract (18), test_processlint (31), test_instructions (16), test_windows_safe (14), test_utf8_helpers (14): all OK.
- No hunk inside ITER-17 (T02-2). ITER-19 holds the 5-row table, `[info] <scope> closed; say undo`, `--kind read`, `--blocks ""`, away line (T02-1, T02-3).
- Old wording ("The PO confirms the close at a check-in") gone from closing.md; grep for other stale "PO's yes" wording finds none in the suite rules.
- Changelog under v29, no version file touched (T02-4).

#### Known failing on base (not FAIL)
- test_dev_rules_size::test_every_team_set_fits_the_limit: 5692 B on 5c0d5cd, 5689 B now (a 3 B drop).
- test_templates::TemplateLayersTest::test_designer_may_write_only_ui_design_files: red on base, `Edit(//tmp/**)` extra allow. Not touched here.

#### Follow-ups (not blocking)
- suites.md SUITE-1b (line ~16): the words "on the final sha" were dropped from "A full run, once, on the final sha". SUITE-2d and SUITE-5b keep it. Restore it when 05's integrator touches the file.
- changelog v29 heading is also created by 06 at 6bab9f1; the planned text conflict (plan-tech.md line 32) is for the last integrator.

## QA blackbox

### QA blackbox, task 02: standing yes for routine gates (sha e2b05c8)

Rule-text task, no screen. I read the rules as the squad sees them: `squad-process lint`, `squad-process rule ITER-19`, `squad-process compose <role>` to /tmp, and the text diff against main.

| AC | live | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 | live | `python3 bin/squad-process lint`; `squad-process rule ITER-19` | exit 0; the table has exactly the 5 gates of the ticket (close passed scope with 0 findings routine, start next planned scope routine, full `--tz` suite ask non-blocking, merge/push/deploy always asks, team/plan/scope change always asks) | pass |
| AC1b | live | read ITER-19 bullets and the CLAUDE.md "Running tests" diff, SUITE-1/1b/2d/3/3b diff | ask is an `answer` item with `--blocks ""`; "Nothing waits on it: tasks go on and the scope may pass and close"; "A check-in or merge item carries `[warn] full suite: not answered`"; CLAUDE.md ask line and the `--tz` runner line both say non-blocking and that the merge item names a missing answer; suite rules say the same | pass |
| AC2 | live | `git diff -U0` hunks of iterations.md vs ITER-17 position | hunks at lines 45, 99, 150; ITER-17 is at 134, untouched; ITER-19 says "With `away` set nothing here changes ([ITER-17])" | pass |
| AC3 | live | read ITER-19 | `squad-inbox add --kind read` (not `answer`), verdict line `[info] <scope> closed; say undo` / `started; say undo`; undo steps given | pass |
| AC4 | live | read changelog diff, diff stat | v29 entry with why and Deploy lines; no version file touched; bump rides 05 (Manager decision) | pass |
| Reach | live | composed manager, tech-lead, qa-whitebox rules | ITER-19 only in the manager's; the suite lines (non-blocking wording) reach manager and tech-lead; no stale "only after the PO's yes" for the full suite left in templates/CLAUDE.md | pass |

#### Follow-ups (not FAILs)
- Tickets 02 and 06 both add a `## v29` heading to the changelog; at integration the two entries must be merged under one heading (05 then writes the version line).
- `test_dev_rules_size::test_every_team_set_fits_the_limit` fails on base (known, 5692 B); this change shrinks it by 3 B.
