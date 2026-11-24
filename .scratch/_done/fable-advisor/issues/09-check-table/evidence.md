# Evidence: 09 One check table per ticket

## Behaviour
- `squad-evidence checks --template` prints a comment line, the header, the separator and an empty AC1 row; with a filled Dev cell it passes `checks`, empty it exits 1.
- `squad-evidence checks <file>`: exit 0 ok, 1 problems (`file:line: AC2: empty Dev cell`), 2 usage.
- `squad-evidence check <folder>` with a `## Checks` section also wants every QA cell filled (`-` allowed); no section: unchanged. `squad-evidence check` on the evidence of tickets 01, 02, 03 exits 0 (04, 05, 07 are not on this branch).
- Rules: EVID-9 (Developer), EVID-9b (QAs, `## Review` points at `## Checks`), EVID-9d (Manager, no QA), EVID-9c/9e (`tech-ac = dev and qa-black = yes`: Developer assembles, Manager accepts); lint exit 0.

## Review
The check table is `## Checks` (`$SCOPE_DIR/evidence/09/checks.md`). Developer rule bytes: sweep max 5358 B before, 5433 B after; LIMIT 5400 -> 5440 (Tech Lead ANSWER 09, ceiling 5480).

## Hand-off for the Manager
After merge and re-pin: remove SQ-2 from `process.local.md` and add the `process-log.md` row (WHO-6).

## QA whitebox

### 09 QA whitebox, sha 136f92f: PASS
Base is 27e6f61 (not on main with 04-06/10); diff checked against it. My column is filled in evidence/09/checks.md.
- T1-T3: test_squad_evidence 49 OK (empty Dev cell fails, full table passes, final blank QA cell fails, flow add --heading Checks then check). `squad-evidence check` on evidence of 04, 05, 07 rc 0.
- T4: lint rc 0, no "Chieu" in templates. T5: test_rules_wording (CheckTableRulesTest) OK; 94 OK with test_dev_rules_size, test_rules_contract, test_squadrules.
- T6: LIMIT is 5440, not 5400: Tech Lead ANSWER 09 (ceiling 5480, the Manager accepted). OK as ruled.
- T7: SQ-2 left for the Manager; hand-off line is in evidence.md.
- T9: nothing to check in code.
Follow-ups (not blocking, SQ-4):
1. `cells()` splits on every `|`, also `\|` and a pipe inside backticks: a command cell like `grep x f | wc -l` gives "row has 5 cells, want 4" (tested). Commands often have pipes; split on unescaped `|` and outside backticks.
2. AC2 "`## Review` points at the table" is only in EVID-9b (QAs, who do not write `## Review`); the Developer rule EVID-9 does not say it. Tech Lead ruled this (ANSWER 09, byte cap). The Developer's own evidence does it.

## QA blackbox

### QA blackbox 09 (sha 136f92f, dev-fable-w)
Run from the dev-w worktree's `bin/squad-evidence`, scratch files only. Table: `checks.md` (my column filled).

| AC | live/shot | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 one table, 3 role columns | live | `checks --template`; `checks` on a full table | header `AC / Dev / QA whitebox / QA blackbox`, rc 0 on full | pass |
| AC2 empty Dev fails; `## Review` points at table | live | `checks` on tables with empty Dev, `-` Dev; `check` on folders with/without `## Checks`, blank QA cell; `add --heading Checks` then `check` | empty Dev rc 1 with `file:line: ACn: empty Dev cell`; no `## Checks` rc 0; blank QA rc 1; `-` ok; embed keeps table, rc 0; the Dev's own `## Review` names the table | pass |
| AC3 SQ-2 removed + log | - | - | Not done here by design (ticket T7, Dev hand-off): the Manager removes SQ-2 from the overlay after merge and re-pin | follow-up (Manager) |
| AC4 tests: empty cell fails, full passes | live | same runs as AC2 | both behaviours seen by hand (Dev's tests are QA whitebox's) | pass |

Also: repeated row id rc 1; wrong header rc 1; missing file / no args rc 2; real Dev evidence of 09 `check` rc 0.

## Checks

<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `PYTHONPATH=tests python3 tests/test_squad_evidence.py` OK | `python3 bin/squad-evidence checks --template` prints the 4-column header; EVID-9/9b put each role in its own column; OK | `squad-evidence checks --template` prints the 4-column header (AC, Dev, QA whitebox, QA blackbox); `checks` on a full table rc 0 `ok`; OK |
| AC2 | `PYTHONPATH=tests python3 tests/test_squad_evidence.py` (full table passes, empty Dev cell fails) | `python3 bin/squad-evidence checks` on a table with an empty Dev cell: rc 1, `AC: empty Dev cell`; full table rc 0. `## Review` pointer is in EVID-9b (Tech Lead ANSWER 09 ruling); OK | `squad-evidence checks` on a table with empty Dev cell: rc 1 `empty.md:4: AC2: empty Dev cell`; `-` in Dev also rc 1; `squad-evidence check` on a folder whose `## Checks` has an empty Dev cell rc 1, a blank QA cell rc 1, `-` allowed, full rc 0; `add --heading Checks` then `check` rc 0; EVID-9b in the rules for the `## Review` pointer; OK |
| AC3 | `python3 bin/squad-process lint --plugin-root .`; SQ-2 stays for the Manager (T7) | `python3 bin/squad-process lint --plugin-root .` rc 0; SQ-2 stays for the Manager (T7); OK | NOT checkable here: SQ-2 stays in the overlay until the Manager removes it after merge and re-pin (ticket T7, Dev evidence hand-off). Follow-up for the Manager, not a Dev fail |
| T1-T3 | `PYTHONPATH=tests python3 tests/test_squad_evidence.py` (ChecksTableTest) | `cd tests && PYTHONPATH=. python3 test_squad_evidence.py` 49 OK; `squad-evidence check` on evidence of 04, 05, 07 (git show of their shas) rc 0 | `squad-evidence check` on a folder with no `## Checks` rc 0 (unchanged); repeated row id rc 1; wrong header rc 1; no file rc 2, no args rc 2; OK |
| T4 | `python3 bin/squad-process lint --plugin-root .` exit 0; `grep -rn Chieu templates/squad/process` empty | lint rc 0; `grep -rn Chieu templates/squad/process` empty; OK | - |
| T5 | `PYTHONPATH=tests python3 tests/test_rules_wording.py` (CheckTableRulesTest) | `PYTHONPATH=. python3 -m unittest test_rules_wording test_dev_rules_size test_rules_contract test_squadrules` 94 OK | - |
| T6 | `PYTHONPATH=tests python3 tests/test_dev_rules_size.py` | LIMIT 5440 (not 5400) per Tech Lead ANSWER 09, ceiling 5480; test_dev_rules_size OK | - |
