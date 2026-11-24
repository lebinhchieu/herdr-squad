# 01 Team Lead sends the Manager the goal status

## Behaviour
With rows in `goals.md`, the Team Lead nudge (5 and 15 min) now names every open goal (blocked ones in the existing "Manager's" sentence, the rest as "Open goals: ..."). When no ticket is open it also asks for one line to the Manager: each goal is done when all its tickets passed, else blocked with the reason; the Manager updates `goals.md`, the Team Lead never edits it. With an open ticket the goal-status ask is left out; no goals -> old wording.

SQ-10 and targeted run (from `tests/`): `python3 -m unittest test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squad_start test_squad_log_message test_squadtask` -> Ran 217 tests, OK.

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog TeamLeadTest.test_goal_status_is_asked_of_the_team_lead_when_no_ticket_is_open | PASS on 4ba9166 (## QA whitebox, re-check) | live nudge run, PASS (## QA blackbox) |
| AC2 | TeamLeadTest.test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals | PASS on 4ba9166 (## QA whitebox, re-check) | live, PASS |
| AC3 | same AC1 test (G2 blocked named as the Manager's) | PASS on 4ba9166 (## QA whitebox, re-check) | live, both goals blocked, PASS |
| AC4 | existing watchdog rows pass unchanged (85 OK) | PASS on 4ba9166 (## QA whitebox, re-check) | live, TL absent routes to Manager, PASS |
| AC5 | the two tests above | PASS on 4ba9166 (## QA whitebox, re-check) | - |
| AC6 | docstring "Who is told"; ADR 0028 Consequences line | PASS on 4ba9166 (## QA whitebox, re-check) | - |
| AC7 | the 217-test run above | PASS on 4ba9166 (## QA whitebox, re-check) | - |
| AC8 | plugin.json 0.10.3; changelog v22 | PASS on 4ba9166 (## QA whitebox, re-check) | - |
| AC9 | - (QA blackbox live check) | PASS on 4ba9166 (## QA whitebox, re-check) | live, PASS (AC1/AC9 row) |

## Review
AC trace:
AC1 | tests/test_squad_watchdog.py TeamLeadTest.test_goal_status_is_asked_... | cd tests; python3 -m unittest test_squad_watchdog
AC2 | TeamLeadTest.test_goal_status_is_not_asked_... | same
AC3 | AC1 test | same
AC4 | existing rows | same
AC5 | both tests | same
AC6 | grep -n "one-line" bin/squad-watchdog; grep -n "reports goal status" docs/adr/0028-*.md | grep -c .
AC7 | 217 tests | see Behaviour
AC8 | grep -rn '0\.10\.2' .claude-plugin/ (no hit) | grep
AC9 | QA blackbox
See `## Checks`.

## QA whitebox

### QA whitebox, ticket 01

#### Technical AC review (before HANDIN)
Ticket AC5-AC9 are accepted. The base is eade230; the code read is `bin/squad-watchdog` `team_lead_nudge_text` (l.319), `open_goals`/`goals_text` (l.176-184), the docstring "Who is told" (l.30), and `TeamLeadTest` (tests l.630).
Additions that bind this sha (checked at HANDIN):
- AC5a Each AC1 and AC2 test checks the 5-minute and the 15-minute text (the 15-minute one is the "last reminder" variant).
- AC5b AC1 test asserts: goal id, title, status named; "Manager" and a done-or-blocked ask present; the text does not tell the Team Lead to write `goals.md` (a `goals.md` mention is allowed only as the Manager's file: assertNotRegex for a verb + `goals.md` aimed at "you").
- AC5c AC2 test asserts: waiting tickets listed as before, open goals named, and NO goal-status ask while a ticket is open.
- AC5d One assertion (inside an existing or new test, no new matrix): a `blocked` goal with an `in progress` goal and no ticket: the blocked one stays named as the Manager's; the ask covers the in-progress one only.
- AC5e One assertion: `goals.md` absent (old ticket-based check): the Team Lead text has no goal sentence and equals today's wording. Manager `nudge_text` untouched (existing tests pass unchanged).
- AC6a The goal list comes from `goals_text`/`open_goals` (no second formatter; title clipping stays `clean(..., 60)`). The stale docstring of `team_lead_nudge_text` ("a blocked goal ... is only named") is updated with the module docstring.
- AC7a New printed text is ASCII (test_utf8_helpers/test_windows_safe). Quote the three runs and the `grep -rl` hit list with the result of each hit file (tests/test_squad_watchdog.py, test_squad_start.py, test_squad_log_message.py, test_squadtask.py match "nudge/squad-watchdog").
- AC8a Version: `.claude-plugin/plugin.json` 0.10.3; `grep -rn '0\.10\.2' .claude-plugin/` empty; a new top row in `skills/squad-process-update/changelog.md` (it lists versions: l.3 "Plugin 0.10.2"). Check `tests/test_instructions.py` for a version-vs-changelog assertion.
- No change to `decide`, `wake_events` or routing (`route`): diff outside `team_lead_nudge_text`, docstring, tests, ADR, version, changelog is a finding.

#### Verdict on ee996b0: FAIL (one return)
Ran: the 7 test files of the HANDIN on a clean checkout of ee996b0: 217 OK (test_windows_safe git cases need a real checkout; run there: 44 OK). Non-ASCII in bin: only the old `...` at l.151, none added. Version, changelog v22, ADR line, docstrings: OK. Diff stays inside the allowed files.

##### F1 Ask is sent when every open goal is already `blocked` (AC3, AC5d)
- `bin/squad-watchdog` team_lead_nudge_text: `if open_goals(snap) and not open_tickets:` uses all open goals, not `mine`.
- Live call, all tickets passed, goals = [1 A blocked]: text says "Blocked goals are the Manager's, not yours to solve: 1 A: blocked (why). No ticket is open: send the Manager one line ...: each goal is done when ... else blocked with the reason." Two orders in one message; today's text for this case has no ask (AC3 "as today"), and the Team Lead is told to report a goal the Manager already holds as blocked, at every nudge.
- Pass: gate the ask on `mine` (an open goal that is not `blocked`): `if mine and not open_tickets:`.
- Test missing (AC5d): the first new test has a blocked G2 but asserts nothing about it. Add: the G2 blocked line is present ("Manager's"), and a blocked-only goals.md gives no "send the Manager one line" in the text.

##### F2 AC5a: the AC2 test checks only the 5-minute text
- tests/test_squad_watchdog.py `test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals`: ticks 0 and 5, asserts `self.sent[0]` only. Tick 15 too and assert both texts have no ask (the 15-minute text is a separate head).

##### Follow-ups (not a FAIL)
- The text says "(`STATUS`)" with no task id; MSG-2 wants an id after the type. Consider "send the Manager one line" with no type, or the goal id.

#### Re-check 4ba9166: PASS
Changed files only: bin/squad-watchdog (ask gated on `mine`), tests/test_squad_watchdog.py (G2 blocked line asserted; AC2 test ticks 5 and 15; blocked-only case has no ask). The 7 test files on a clean checkout of 4ba9166: 217 OK.
Follow-up: "(`STATUS`)" without a task id (MSG-2).

## QA blackbox

### 01 QA blackbox: behaviour check of ee996b0

Method: live. Scratch scope home laid out like a repo (`repo/.claude/squads/plugin/scopes/demo` + `repo/.scratch/demo/issues/01-demo.md`), roster demo-mgr + demo-tl, a `--herdr-json` fixture with both idle (agent `name` field), `bin/squad-watchdog tick --home ... --manager demo-mgr --team-lead demo-tl --herdr-json ... --now` at 10:00 / 10:06 / 10:16 UTC. `send` fails ("agent_not_found", the demo names are not real herdr agents); the text is in `watchdog.log` and is what is judged. Dev branch worktree binary (ee996b0); base binary compared once.

| AC | Mode | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 / AC9 | live | ticket `Status: passed`, goals.md: 1 `in progress`, 2 `blocked` | 5 and 15 min nudges go to demo-tl (no route line). Text: "Waiting: none open ... Blocked goals are the Manager's ...: 2 Demo goal two: blocked (waiting on Chieu, inbox 7). Open goals: 1 Demo goal one: in progress. No ticket is open: send the Manager one line (`STATUS`): each goal is done when all its tickets passed, else blocked with the reason. The Manager updates goals.md; you never edit it." Goal id, title, status named; no instruction to edit goals.md. Base binary, same input: no "Open goals", no ask. | PASS |
| AC2 | live | ticket `Status: building`, same goals | "Waiting: 01 building" listed; "Open goals: 1 Demo goal one: in progress"; no "send the Manager one line" ask | PASS |
| AC3 | live | both goals `blocked` | blocked goals named in "Blocked goals are the Manager's" sentence with reason | PASS (see follow-up 1) |
| AC4 | live | demo-tl missing from fixture | `route: 5 min idle -> demo-mgr (team lead absent)`; Manager wording unchanged (base text) | PASS |
| AC4 | live | all goals `done` | `all goals done; watchdog stops` | PASS |

Not mine (QA whitebox): AC5-AC8 code, tests, ADR, version.

#### Follow-ups (not AC breaks)
1. With only `blocked` goals and no open ticket, the Team Lead is still asked for a goal-status line, though nothing is left to report.
2. The line is typed `STATUS` with no goal ids named; the Manager reads it from free text.

#### Re-check on 4ba9166 (diff ee996b0..4ba9166)
Same scratch home and fixture, live, 10:00/10:06/10:16 UTC:
- AC1/AC9 passed ticket + in-progress goal: nudge to demo-tl names "Open goals: 1 Demo goal one: in progress" and asks the Manager one `STATUS` line; no goals.md edit asked. PASS
- AC2 ticket building: "Waiting: 01 building", open goal named, no status ask. PASS
- AC3 only blocked goals, no open ticket: blocked goals named as the Manager's, no status ask any more (follow-up 1 fixed). PASS
- AC4 Team Lead absent: route to Manager, old wording; all goals done: `all goals done; watchdog stops`. PASS
Follow-up 2 (`STATUS` names no goal ids) stays open, not an AC break.
