
sha: 635fea1
## Review

| AC | Test or capture | How run |
|---|---|---|
| T3.2 CONTEXT terms Next step, Commands table, Squads pane; README line for `/squads`, `squad-tree` | `git diff main -- CONTEXT.md README.md` | read |
| T3.2b ADR 0026 line 3 is `Status: accepted (...)`; six facts named; ADR 0020 line 7 has "(amended by 0026)" | `git diff -- docs/adr` (4 changed lines) | read |
| T3.3 / SQ-10 | the three files below | `python3 tests/<file>.py` |

## Behaviour

Docs only. `tests/test_windows_safe.py` 14 OK, `tests/test_utf8_helpers.py` 14 OK, `tests/test_instructions.py` 16 OK, `tests/test_promotion_0_6_0.py` 3 OK, `tests/test_templates.py` 8 OK. No full suite.

## Review: QA whitebox

### QA whitebox, ticket 06, sha 5c1fddd (return 0)
Verdict: PASS. Clean clone at 5c1fddd, tests run by me. Diff e32f28e..5c1fddd read in full.

| AC | Check | Result |
|---|---|---|
| T3.2 | CONTEXT.md adds Squads pane, Next step, Commands table (match promote.md wording; Squads pane says "not a board" via _Avoid_ and states read-only, copy only) plus one Relationships line; README one row for `/squads` and `squad-tree [--squad NAME] [--json]` (JSON version 1) | ok |
| T3.2b | ADR 0026 line 3 is `Status: accepted (...)`, no draft text; Decision lists all six facts (needs you, stuck, tasks done, tasks total, agents working, last active); ADR 0020 line 7 has "(amended by 0026)", same as line 12; 0007 and every other 0020/0026 line unchanged (4 changed lines, 2 per file) | ok |
| T3.3 / SQ-10 | test_windows_safe 14, test_utf8_helpers 14, test_instructions 16 OK; also test_promotion_0_6_0 3, test_templates 8, test_old_language_inventory 2 OK | ok |
| PROMO-8 | edits match promote.md; nothing the scope did not decide; 05's sha bcd75a6 is an ancestor of 5c1fddd | ok |

#### Follow-ups (SQ-4)
1. `test_squadboard_list` T04_AC1 fails on main too in a fresh clone (see evidence/05/qa-w.md). Expect it in the full `--tz` run.

## Review: QA blackbox

### QA blackbox: 06 (sha 5c1fddd), docs only
Read `git diff e32f28e 5c1fddd` of the four doc files (docs are not code).
| Check | Saw | Result |
|---|---|---|
| T3.2 CONTEXT.md terms | Squads pane, Next step, Commands table added (+ one relation line); wording matches promote.md and the built pane (copy only, list only, squad-tree) | pass |
| T3.2 README | one row `/squads`, `bin/squad-tree`; says read-only, runs none, copy, JSON version 1, points to ADR 0026 | pass |
| T3.2b ADR 0026 line 3 | `Status: accepted (...)`, no "Draft text for" | pass |
| T3.2b six facts | needs you, stuck, tasks done, tasks total, agents working, last active | pass |
| T3.2b ADR 0020 line 7 | "no cross-squad view (amended by 0026)"; line 12 has the same pointer; only that one line changed | pass |
| No other change | ADR 0007 untouched in this diff; bin/squadcommands.py and bin/squad-tree exist as the docs say | pass |
Follow-up: the Next step example "Answer 1 question(s)" differs from the pane text ("Answer 2 questions in api"); harmless.

## Diff check 5c1fddd..635fea1: QA whitebox

### QA whitebox, ticket 06, sha 5c1fddd (return 0)
Verdict: PASS. Clean clone at 5c1fddd, tests run by me. Diff e32f28e..5c1fddd read in full.

| AC | Check | Result |
|---|---|---|
| T3.2 | CONTEXT.md adds Squads pane, Next step, Commands table (match promote.md wording; Squads pane says "not a board" via _Avoid_ and states read-only, copy only) plus one Relationships line; README one row for `/squads` and `squad-tree [--squad NAME] [--json]` (JSON version 1) | ok |
| T3.2b | ADR 0026 line 3 is `Status: accepted (...)`, no draft text; Decision lists all six facts (needs you, stuck, tasks done, tasks total, agents working, last active); ADR 0020 line 7 has "(amended by 0026)", same as line 12; 0007 and every other 0020/0026 line unchanged (4 changed lines, 2 per file) | ok |
| T3.3 / SQ-10 | test_windows_safe 14, test_utf8_helpers 14, test_instructions 16 OK; also test_promotion_0_6_0 3, test_templates 8, test_old_language_inventory 2 OK | ok |
| PROMO-8 | edits match promote.md; nothing the scope did not decide; 05's sha bcd75a6 is an ancestor of 5c1fddd | ok |

#### Follow-ups (SQ-4)
1. `test_squadboard_list` T04_AC1 fails on main too in a fresh clone (see evidence/05/qa-w.md). Expect it in the full `--tz` run.

#### Re-check, sha 635fea1 (diff 5c1fddd..635fea1)
Verdict: PASS. Only docs/adr/0026 line 15 changed (plus evidence.md). The new text is true: `hooks/hooks.json` at 635fea1 lists one module `./register.tsx`, which runs po-inbox and `./squads/register`. No other ADR line changed; no code or test file changed, so the earlier test results stand.
