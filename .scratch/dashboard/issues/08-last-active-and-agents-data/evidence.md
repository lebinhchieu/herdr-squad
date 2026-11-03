
sha: 3440711
## Behaviour
No page yet (tickets 05 and 12 draw it). Checked on the ticket 02 fixture with the tests below.
- New readers: `/api/active` (`bin/squadboard_active.py`) and `/api/agents` (`bin/squadboard_agents.py`, plus `banner(sel)` for ticket 05). Found by ROUTE discovery.
- `--herdr-json FILE` added to `bin/squadboard.py` (3 lines: flag, `server.herdr_json`, `sel["herdr_json"]`).
- AC1 (working owner: transcript mtime, `approx`; retired owner: no transcript time), AC2, AC3 (`partial: ["transcript"]`), AC4 (goal = newest scope or goal Manager), AC5 (59:59 not quiet, 60:00 quiet; 90 min gives `quiet_s` 5400; 30 min none), AC6 (5 live rows, 1 retired, other squad hidden), AC7 (herdr down, bad JSON, missing file, empty PATH: `status unknown`, roles listed).
- `tests/test_squadboard_active.py` (8) and `tests/test_squadboard_agents.py` (8) pass. Also run: `test_squadboard_server`, `test_board_fixtures` (44 pass), `test_windows_safe`, `test_no_bare_bash`, `test_old_language_inventory`.
- Real CLI note: `herdr agent list` has no `--json` flag (it prints JSON already); the reader calls `herdr agent list`.

## QA whitebox

### QA whitebox 08: last active and agents data. sha e933167. Verdict: FAIL (first return)
Checked in a `git clone` at e933167. Ran test_squadboard_active, test_squadboard_agents, test_squadboard_server, test_board_fixtures, test_windows_safe, test_no_bare_bash, test_old_language_inventory: 60 tests OK. No write calls in the two new modules (TC.2); the board tree was byte- and mtime-identical after a live run (read-only check, REV-5b).
OK: pure `parse_herdr`, herdr called by name with a 5 s timeout and no shell, missing/garbage/down all give `unknown:["herdr"]` with roles listed, roster filter (other squad hidden), row field set asserted, banner `[]` vs `None`, quiet boundary 3599/3600, transcript only `stat`ed, roster/transcript helpers reused. `herdr agent list` has no `--json` flag (verified live): calling it without the flag is right; TA2's wording is superseded.

#### Findings
- **F1 `bin/squadboard_agents.py:33-45` (`STATUSES`, `parse_herdr`), TA1/TA4, REV-4 (real samples incl. the idle case).** Live run on this machine: `herdr agent list` returns `agent_status` `done` for 3 of 9 agents (`board-dev-ui-4`, `board-dev-agents-5`, `board-dev-park-6`; also `idle`, `working`). The reader maps any status outside `working|idle|blocked` to `unknown`, so `/api/agents` showed those 3 live agents as `unknown` while herdr answered fine. That is the same word AC7 uses for "herdr not running", so the page would say status unknown for agents herdr knows. The recorded fixture has no `done` sample, so the test (`test_T08_TA1`, asserts the set is exactly working/idle/blocked) never saw it. Pass: map `done` to `idle` (it is a turn finished, waiting for input) or keep it as `done` and tell tickets 10/12; add a `done` agent to a recorded sample (copied from the live list, name changed) and assert the row status for it; a status herdr adds later still gives `unknown`.

Live result (for the record): 7 live rows, 6 retired, banner `[]`; scope `last active` source transcript, approx true.

#### Recheck sha 3440711: PASS
Changed file only (LC-3b): bin/squadboard_agents.py (+ test). test_squadboard_agents, test_squadboard_active, test_squadboard_server, test_old_language_inventory, test_windows_safe: 51 OK. Live run: agents herdr lists as `done` now show `idle`; no live agent shows `unknown`. A new status word still gives `unknown`; test `test_T08_TA4_done_status_is_idle_new_word_unknown` covers both.

## QA blackbox

### QA blackbox, ticket 08 at e933167: PASS on what exists
Method: `bin`+`templates`+`tests` from e933167; fresh fixture copy (`board_fixtures.py --now`); board with `--herdr-json` on ports 18731/18741/18742; routes found by trying `/api/agents` and `/api/active` (query `squad=fix&scope=checkout` or `goal=alpha`). No page yet, so I read the JSON. For transcript tests the board got `CLAUDE_CONFIG_DIR=<fixture claude-config>`.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| T08.AC1 | Task 02: last message 15 h old, owner `fix-dev-02` working. Without and with the fixture transcripts | Without transcripts: source messages, 15 h. With: source transcript, `approx: true`, ~10 s old. Done tasks 07/08: source messages (message age) | PASS (data); wording "3 min ago, approx" at T12 |
| T08.AC2 | Scopes with no message, commit or transcript (search, parked, alpha-api at start) | `ts: null`, `partial: [messages, transcript]`; tasks 01 (todo) and 09 (done) have no entry | PASS (data); text "no activity recorded" at T12 |
| T08.AC3 | Scope checkout: fix-qab-checkout has no transcript file | Scope: source git, `partial: ["transcript"]` | PASS (data); text "partial: transcript missing" at T12 |
| T08.AC4 | Goal alpha: messages in alpha-api (100 min ago) and alpha-ui (40 min ago); then a goal-level message 5 min ago | Goal = 40 min (newest scope); after the goal message = 5 min | PASS |
| T08.AC5 | Task 02 in progress, live owner; newest message 90 / 30 / 60 / 61 min old | quiet_s 5400 (= 1 h 30) / none / 3600 / 3660 | PASS |
| T08.AC6 | Agents of checkout with `agents.json` | 5 live rows (manager, 2 dev, qa-whitebox working, qa-blackbox status unknown), role, task, status, last_activity; `retired_count: 1` with fix-dev-03 under `retired` | PASS (data); rows and "1 retired" control at T12 |
| T08.AC7 | Board with `not-running.json` | `status: unknown`, `reason: herdr not running`, `unknown: ["herdr"]`; the 5 roles still listed with status unknown, retired 1 | PASS (data); banner text at T12 |

Watch at T12 (not a fail now): task 04 (stage "blocked", live owner idle) also carries `quiet_s` (5 h) when no transcript is read. AC5 says quiet is for an in-progress task; the page must not show "quiet" for a blocked task.
Note: an Agents row for fix-qab-checkout has no pane (status unknown): fine, it has no herdr entry.
Cleanup: boards stopped by PID; scratch left in /tmp (qb08.*, board-fixture-*).

#### Re-check at 3440711 (diff: agents module and its test)
Same fixture, a copy of `agents.json` with one agent `done` and one with an invented status word.
- `done` row shows `idle`; the invented word shows `unknown`; blocked and working unchanged; 5 live rows, `retired_count` 1. PASS (AC6)
- Herdr not running file: `status unknown`, reason "herdr not running", 5 roles still listed. PASS (AC7)
- Quiet data for task 02 unchanged (`quiet_s` set, source messages). AC1-AC5 untouched by the diff.
Boards stopped by PID.
