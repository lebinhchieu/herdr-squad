# Evidence 06: parked questions

## Behaviour
Real run of `squad-inbox park|unpark|resolve` in a scratch folder (`SQUAD_INBOX_NOW` fixed):

```
parked Q1
parked Q2
Q2 unparked
Q1 resolved
squad-inbox: Q1 is already resolved
exit=2
---
## Q1
Status: resolved
Parked: 2026-11-04T10:00:00Z
Is the API versioned?
Blocks: ticket 7
From: E3 #2
Resolved: 2026-11-04T10:00:00Z yes, v1

## Q2
Status: unparked
Parked: 2026-11-04T10:00:00Z
Unparked: 2026-11-04T10:00:00Z
Which port?
```
- Readers count only `Status: parked` as parked; `unparked` and `resolved` are not parked.
- Park writes `## Q<n>` blocks; `unpark` sets `Status: unparked` and adds `Unparked:`; `resolve` adds `Resolved: <time> <answer>`; a repeat is refused with exit 2 and the file is unchanged.
- `escalations.md` and `inbox.jsonl` are byte-identical before and after (test_golden_and_inbox_untouched).
- Board side (AC1-AC6 page): reader function `parse_open_questions(text, path) -> (entries, warnings)` in `bin/squadinbox.py`; a broken block gives `open-questions.md unreadable: <path> (<heading>)` and the rest stay.
- Rule text: ITER-4 (park commands, never wait), START-18 (read `open-questions.md`), START-19 (`tickets:` line), `templates/scope/scope.md` (optional `tickets:` line), changelog v11. Only the Manager's composed rules change.

## Tests run
test_squadinbox_park (new, 6), test_squadinbox, _answer, _win, _body_crlf, test_po_inbox_contract, test_inbox_guide_cmd, test_instructions, test_rules_wording, test_sizes, test_small_files_equivalence, test_squad_manager_guard, test_windows_safe, test_old_language_inventory, test_processlint, test_process_writing, test_rules_contract, test_squadrules, test_squadcompose, test_team_duties, test_dev_rules_size, test_templates, test_squadscaffold, test_squad_start, test_crlf_squad_files, test_board_fixtures, test_promotion_0_6_0: all OK.

## QA blackbox

### QA blackbox, ticket 06 at 5b60ed2: PASS on what exists
Method: `bin`+`templates` from 5b60ed2, fixture copy (from a248f21), `squad-inbox` run by hand with `SQUAD_ROLE=manager` (and `SQUAD_DIR`/`SCOPE_DIR`/`GOAL_DIR` set like a real Manager). The page does not exist yet and ticket 05 (Needs you data) is not built, so the display parts of AC1-AC6 cannot be seen. I checked what the commands write and refuse.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| T06.AC1 | Scope `questions` with 3 open items (E1, E3, E4); `park --text ... --from E3 --blocks "ticket 05"` | "parked Q1"; `open-questions.md` has `## Q1`, `Status: parked`, `Parked: <time>`, text, `Blocks:`, `From:`. `squad-inbox list --open` still lists the 3 items (parking is not an answer; the page must subtract the parked ones: count 2 and "Parked (1)" cannot be seen yet) | PASS for the command; display at T05/T12 |
| T06.AC2 | `unpark Q1` | "Q1 unparked"; `Status: unparked`, `Unparked:` time added; again: "already unparked", exit 2 | PASS for the command; count 3 at T12 |
| T06.AC3 | `park` then `resolve Q2 --answer "go with (a)"` | `Status: resolved`, `Resolved: <time> go with (a)` | PASS for the command; row leaves Parked at T12 |
| T06.AC4 | `--level goal` (goal env set), `--level squad` (SQUAD_DIR set) | Goal question written to `goals/alpha/open-questions.md`; squad one to `<squad>/open-questions.md`; `--level goal` on a lone scope: "needs $GOAL_DIR", exit 2. Which question shows under which choice is a page part | PASS for where it is written; display at T12 |
| T06.AC5 | Fixture `broken-parked` (bad status, bad time, garbage entry) | `park` adds a new entry and leaves the broken text; `unpark Q1` on the broken entry: "no readable question Q1 in open-questions.md", exit 2, no crash. The page text "open-questions.md unreadable: <path>" cannot be seen yet | PASS for the commands; page text at T12 |
| T06.AC6 | Not testable: copy control is a page part | - | open (T12) |

Errors: unknown Q9: refused exit 2; empty `--text`: refused exit 2. Note: I used `--level squad` once with `--home <scope>` and it wrote into the scope's file; with the real env vars it is right (the help says `--home` is the Manager's home folder).
Not tested: the Manager rule text (ITER-4/START-18/START-19), `tickets:` line, process changelog: not a user-visible behaviour of the board; QA whitebox owns them.
Scratch left in /tmp (qb06.*, board-fixture-*); no server was started.

## QA whitebox

### QA whitebox 06: parked questions. sha 5b60ed2. Verdict: FAIL (first return)
Checked in a `git clone` at 5b60ed2. Ran the 24 test files of TA6/TA7/TA9/TA10 (park, inbox x5, instructions, dev_rules_size, process_writing, processlint, rules_*, squadrules, squadcompose, team_duties, sizes, templates, squadscaffold, squad_start, crlf_squad_files, windows_safe, no_bare_bash, old_language_inventory): 394 tests OK (one `test_no_pyc` failure was my own `__pycache__` leftover; passes in a clean tree).
Live probes (scratch folder, real CLI): CRLF file with 3 blocks (one broken) rewritten LF, no block lost, broken block text kept, next number = max+1 (Q6 after Q5, gap kept); 8 parallel `park` processes gave Q1..Q8, no duplicate, file parses; errors (empty text, `Status:` text, bad `--from`, unknown Q, repeat resolve, `--level goal` without `$GOAL_DIR`) exit 2, one line, file unchanged; `escalations.md`/`inbox.jsonl` untouched. Composed rules of the 10 roles x team x goal, before (6756f93) vs after: only `manager` changes (+338 B); the other roles are identical (TA8).
Accepted deviations (ADR 0016 supersedes ADR 0005 and bans card duplicates): rule text in ITER-4/START-18/START-19 and changelog v11 instead of a `manager.md` edit and a version bump; `test_dev_rules_size` Manager ceilings raised by the size of the new rule only.

#### Finding
- **F1 `Status: unparked` is outside the agreed format (TA1, T06 Rules).** The ticket Rules line and `tasks/decision-parked-questions.md` line 8 say `Status: parked | resolved`. The code writes and reads a third value `unparked` (`bin/squadinbox.py` OQ_STATUSES, `oq_edit`), plus an `Unparked:` line. It is a sensible way to build AC2, but it changes the contract that the reader tickets (05 Needs you count, 07, page 12) are built on, and nobody agreed it. Pass: edit the Rules line of `tasks/issues/06-parked-questions.md` and line 8 of the decision file to `parked | unparked | resolved` plus `Unparked:`, and state in `evidence.md` that readers count only `Status: parked` as parked. Doc-only; no code change needed. (Both files ride your branch, SAFE-4/FILE-11.)

#### Recheck sha 5b60ed2 (doc-only fix): PASS
F1 closed: ticket 06 Rules (line 12) and `tasks/decision-parked-questions.md` (line 8) now read `Status: parked | unparked | resolved`; `evidence.md` (line 28) states readers count only `Status: parked` as parked. No code change; sha unchanged, earlier checks stand.
