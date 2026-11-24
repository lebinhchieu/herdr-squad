# 02 Goal-status line names the goals and has no bare type word
sha: c137955
## Behaviour
With rows in `goals.md` and no open ticket, the Team Lead nudge (5 and 15 min) asks the Manager one line per open (not `blocked`) goal, naming its id: `goal <id> done` or `goal <id> blocked: <reason>`, with each id filled in (e.g. `goal G1 done` or `goal G1 blocked: <reason>`). The word `STATUS` is gone from the Team Lead text. Blocked goals stay only in the "Manager's" sentence. Ticket-open, blocked-only and no-goals texts are unchanged.

SQ-10 and targeted run (from `tests/`): `python3 -m unittest test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions test_squad_start test_squad_log_message test_squadtask` -> Ran 217 tests, OK (hits of `grep -rl "squad-watchdog\|team_lead_nudge" tests/`: watchdog, start, log_message, squadtask, plus the three SQ-10 files).

## Checks
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squad_watchdog TeamLeadTest.test_goal_status_is_asked_of_the_team_lead_when_no_ticket_is_open (G1, G3 named with id, no STATUS, G2 absent from ask) | PASS on c137955 (## QA whitebox) | live, PASS on c137955 (## QA blackbox) |
| AC2 | TeamLeadTest.test_goal_status_is_not_asked_while_a_ticket_is_open_and_without_goals | PASS on c137955 (## QA whitebox) | live, PASS on c137955 (## QA blackbox) |
| AC3 | the two tests above (STATUS absent in ask, ticket-open, blocked-only, no-goals) | PASS on c137955 (## QA whitebox) | - |
| AC4 | 217-test run in Behaviour | PASS on c137955 (## QA whitebox) | - |
| AC5 | git diff b779afd --stat: bin/squad-watchdog, tests only; plugin.json untouched; docstrings updated | PASS on c137955 (## QA whitebox) | - |
| AC6 | - (QA blackbox live check) | - | live, PASS on c137955 (## QA blackbox) |

## Review
AC trace:
AC1 | TeamLeadTest.test_goal_status_is_asked_... | cd tests; python3 -m unittest test_squad_watchdog
AC2 | TeamLeadTest.test_goal_status_is_not_asked_... | same
AC3 | both tests | same
AC4 | 217 tests | see Behaviour
AC5 | git diff --stat b779afd | git diff --stat
AC6 | QA blackbox | squad-watchdog tick on scratch home
See `## Checks`.

## QA whitebox

### QA whitebox, ticket 02

#### Technical AC review (before HANDIN)
Ticket AC3-AC6 accepted. Base b779afd; code read: `bin/squad-watchdog` `team_lead_nudge_text` (l.320-338, the ask at l.332-335), module docstring "Who is told" (l.30-32), `TeamLeadTest` in tests/test_squad_watchdog.py.
Additions that bind the HANDIN sha (checked at HANDIN, no new test file, no matrix):
- AC3a Both texts (5-minute and 15-minute) of the AC1 test: with two non-blocked open goals and one `blocked` goal, the ask names every non-blocked id as `goal <id> done` and `goal <id> blocked: <reason>`; the ids come from `mine` (no hard-coded id).
- AC3b The blocked goal's id does not appear in any `goal <id> done|blocked:` ask form; it stays only in the "Manager's" sentence (assert that sentence still present).
- AC3c `assertNotIn("STATUS", text)` on the Team Lead text in every Team Lead test of that class: ask case (5 and 15 min), ticket-open case, blocked-only case, no-goals.md case.
- AC3d No-goals.md and ticket-open texts are unchanged from b779afd (AC2): same wording, no `goal <id>` form. Manager `nudge_text` untouched.
- AC5a Diff outside `team_lead_nudge_text`, its docstring, the module docstring "Who is told" if it quotes the line, tests and the ticket/evidence files is a finding. `.claude-plugin/plugin.json` stays 0.10.3; `skills/squad-process-update/changelog.md` untouched unless the 01 row quotes `STATUS` (then fix it; run `grep -rn 'STATUS' skills/squad-process-update/changelog.md docs/adr/0028*`).
- AC7a New printed text ASCII only (test_utf8_helpers / test_windows_safe).
- AC4a Quote the three SQ-10 runs and the `grep -rl` hit list with the result of each hit file.

#### Question to the Team Lead (not a gate)
The ticket title says "no bare type word", the AC only bans `STATUS`. The same sentence still ends "or `ASK` the Manager" (unchanged by AC2). I read AC1/AC2 as binding and will not FAIL on `ASK`; tell me if you want `ASK` reworded too.

#### Verdict on c137955: PASS
Ran on a clean clone of c137955 (real checkout): the 7 test files of the HANDIN, 217 OK. Diff vs b779afd: bin/squad-watchdog (team_lead_nudge_text + both docstrings), tests/test_squad_watchdog.py, ticket, evidence only. plugin.json 0.10.3, no `0.10.2` in .claude-plugin/. Non-ASCII in bin: only the old `…` at l.151. Live render (5 min, goals 1 in progress, 2 blocked, no ticket): asks `goal 1 done` / `goal 1 blocked: <reason>`, goal 2 only in the Manager's sentence, no `STATUS`.
AC3a-d, AC4a, AC5a, AC7a met; test loops every sent text (5 and 15 min). Team Lead FINAL 02: `ASK` stays.
Follow-ups (not a FAIL): the ask sentence is long (form given twice, generic and filled in); the `goal <id> ...` line has no task id (MSG-2), by AC1's design.

## QA blackbox

### 02 QA blackbox: behaviour check of c137955

Method: live. Scratch scope home laid out like a repo (`repo/.claude/squads/plugin/scopes/demo` + `repo/.scratch/demo/issues/01-demo.md`), roster demo-mgr + demo-tl, `--herdr-json` fixture with both idle. Command: `bin/squad-watchdog tick --home ... --manager demo-mgr --team-lead demo-tl --herdr-json ... --now` from the Developer worktree at c137955, at 10:00 / 10:06 / 10:16 UTC. `send` fails ("agent_not_found", demo names are not real herdr agents); `watchdog.log` text is what is judged. Goals: 1 and 3 `in progress`, 2 `blocked`.

| AC | Mode | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 / AC6 | live | ticket `Status: passed`, goals 1,3 in progress, 2 blocked | 5 and 15 min nudges to demo-tl: "No ticket is open: send the Manager one line per open goal, naming its id, as `goal <id> done` or `goal <id> blocked: <reason>`, here `goal 1 done` or `goal 1 blocked: <reason>`; `goal 3 done` or `goal 3 blocked: <reason>`: a goal is done when all its tickets passed, else blocked with the reason." Each open id filled in, blocked goal 2 not filled in. `grep -c STATUS watchdog.log` = 0. | PASS |
| AC2 | live | ticket `Status: building`, same goals | "Waiting: 01 building", open goals named, no "send the Manager" ask, no `STATUS` | PASS |
| AC2 | live | all three goals `blocked`, no open ticket | "Waiting: none open", blocked goals named as "the Manager's, not yours to solve" with reasons, no ask, no `STATUS` | PASS |
| AC2 | live | Team Lead missing from fixture, goal 1 open | `route: 5 min idle -> demo-mgr (team lead absent)`; Manager wording ("Check each goal and solve it ...") unchanged; no `STATUS` | PASS |
| AC2 | live | goal `done` | `all goals done; watchdog stops` | PASS |
| AC2 | live | nudge text | "The Manager updates goals.md; you never edit it." still present | PASS |

Not mine (QA whitebox): AC3-AC5 tests, SQ-10 runs, version, docstring.

#### Follow-ups (not AC breaks)
1. Wording is a little redundant: "as `goal <id> done` ..., here `goal 1 done` ...; `goal 3 done` ...". It reads fine and meets AC1.
