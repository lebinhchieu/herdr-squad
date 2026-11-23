# Evidence: 03 watchdog cold-cache pass

## Review

### Review

AC trace (all in `tests/test_squad_watchdog.py`, class `ColdCacheTest`, run `cd tests && python3 -m unittest test_squad_watchdog`):
- AC1 | test_a_failure_in_the_pass_is_logged_and_the_idle_events_still_run; kill switch in test_the_state_file_survives_garbage... | unittest
- AC2 | test_idle_means_55_minutes_since_the_last_main_turn_and_a_subagent_turn_does_not_count | unittest
- AC3 | same test; test_a_goal_home_respawns_its_own_manager... (Manager over the floor, no open work) | unittest
- AC4 | test_notes_newer_than_the_prompt_respawn_lazy_with_a_clean_environment, test_a_failed_respawn_is_logged_and_not_retried | unittest
- AC5 | test_two_prompts_then_gave_up_and_a_new_turn_starts_a_new_spell | unittest
- AC6 | test_a_blocked_pane_a_background_shell_and_a_small_context_are_logged_once_and_get_no_message | unittest
- AC7 | test_nothing_open_tells_the_team_lead_once_and_prompts_no_one_but_a_manager_is_respawned | unittest
- AC8 | test_the_state_file_survives_garbage_and_an_env_override_and_the_kill_switch_apply | unittest
- AC9 | same test; docstring "Cold cache" paragraph in bin/squad-watchdog | unittest, read
- AC10 | test_a_goal_home_respawns_its_own_manager_with_goal_dir_and_no_scope_dir; the other tests drive a scope home | unittest
- AC11 | grep -rl squad-watchdog tests/ hits and the SQ-10 three files | unittest
- AC12 | fake send, fake respawn, recorded herdr json in every test | unittest

Checks table: `evidence/03/checks.md`.

### Behaviour

Deviations from the notes, for the checkers: (1) a blocked pane or a background shell is logged only once the agent's last main turn is old enough (the transcript is read for them too); logging at once for every blocked pane broke the existing test that expects one log line. (2) Second prompt reads the transcript again for its ctx, since C4 stores no ctx. (3) A failed respawn sets `gave_up_ts`.

Tests run (all OK): test_squad_watchdog (113), test_squadtask (15), test_squad_log_message (24), test_squad_start (49), test_squad_spawn (116); SQ-10: test_windows_safe (14), test_utf8_helpers (14), test_instructions (16). No full suite (DECISION 0).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_watchdog.ColdCacheTest.test_a_failure_in_the_pass_is_logged_and_the_idle_events_still_run`, `test_the_state_file_survives...` (kill switch); 113 tests in test_squad_watchdog.py green, old expectations unedited: OK | read tick() hook + 113 tests, OK | idle nudges unchanged, live tick: pass |
| AC2 | `test_idle_means_55_minutes_since_the_last_main_turn_and_a_subagent_turn_does_not_count`: OK | read last_turn, 54/56 min test, OK | 54 vs 56 min, subagent turn: pass |
| AC3 | same test (prompt text, log line, once); goal test (Manager needs no work): OK | prompt/respawn tests, OK | one prompt, Manager/TL prompted: pass |
| AC4 | `test_notes_newer_than_the_prompt_respawn_lazy_with_a_clean_environment`, `test_a_failed_respawn_is_logged_and_not_retried`: OK | argv/env/timeout test, OK | lazy respawn, polluted env: pass |
| AC5 | `test_two_prompts_then_gave_up_and_a_new_turn_starts_a_new_spell`: OK | 2 prompts + 1 give-up test, OK | 2 prompts then give-up: pass |
| AC6 | `test_a_blocked_pane_a_background_shell_and_a_small_context_are_logged_once_and_get_no_message`: OK | blocked/bg/small tests, OK | blocked/bg/small/50k once each: pass |
| AC7 | `test_nothing_open_tells_the_team_lead_once_and_prompts_no_one_but_a_manager_is_respawned`: OK | nothing-open test, OK | TL told once: pass |
| AC8 | `test_the_state_file_survives_garbage_and_an_env_override_and_the_kill_switch_apply` (corrupt file): OK | garbage state test, OK | garbage state recovers: pass |
| AC9 | same test (COLD_CTX override, bad value, docstring read by eye): OK | env override test, OK | override, bad value, COLD=0: pass |
| AC10 | `test_a_goal_home_respawns_its_own_manager_with_goal_dir_and_no_scope_dir` + scope-home tests above: OK | goal-home test, OK | goal home: pass |
| AC11 | grep -rl squad-watchdog tests/ (5 files) + test_windows_safe, test_utf8_helpers, test_instructions: all OK | 158 + grep hits OK | 114 OK on merged copy: pass |
| AC12 | every test passes fake send/respawn and a recorded herdr json; no real herdr or squad-respawn run: OK | fakes only, OK | scratch squad, fake herdr: pass |

## QA whitebox

### QA whitebox 03 — sha bb06a32 — FAIL (F1, Manager ruling FINAL)

Checked in a throwaway detached worktree of bb06a32. All tests use fake send/respawn/herdr json; nothing real was run.

#### Checks (my column)
| AC | Check | Result |
|---|---|---|
| AC1 | read `tick()` hook: runs only when `snap["ok"]`, try/except logs `cold-cache: pass failed`, kill switch `SQUAD_WATCHDOG_COLD=0`; `decide()`/state file untouched (diff); `test_squad_watchdog` 113 OK, old tests unedited | OK |
| AC2 | read `last_turn` (side==False rows of `read_session`, ctx from the reader); test 54 vs 56 min + newer subagent row | OK |
| AC3-4 | tests: prompt text/log literal, notes newer than prompt, argv exactly `squad-respawn <name> --lazy`, env without SQUAD_ROLE/NAME, one of SCOPE_DIR/GOAL_DIR, timeout 120 | OK |
| AC5 | test: 2 prompts, 1 give-up line, no respawn, new turn = new spell | OK |
| AC6-7 | tests: blocked, bg, small context once each, no message; nothing-open tells Team Lead once, Manager prompted | OK |
| AC8-10 | garbage state file, env override (+bad value), goal home test | OK |
| AC11 | `test_windows_safe` 14, `test_utf8_helpers` 14, `test_instructions` 16 OK; `grep -rl squad-watchdog tests/` hits all run: test_squad_log_message 24, test_squad_spawn 116, test_squad_start 49, test_squadtask 15 OK | OK |
| REV-4/5b | `last_turn()` on live transcripts, read-only (python3 -I, no herdr): the 8 live roster sessions give age 0-6 min and ctx 59k-134k (busy case); two finished sessions give age 132 min ctx 67k, equal to their file mtime (idle case). `ts` is timezone-aware. | OK |

#### Findings
**F1 (FAIL, Manager FINAL ruling: breaks spec story 18, "at most two prompts per idle spell"): a pass with several lazy respawns can look stale to `squad-spawn`'s `ensure` and start a second watchdog.**
- bin/squad-watchdog `tick()` writes `st["beat"]` only at the end of the tick (after `cold_cache_pass`); `cold_cache_pass` runs `respawn_fn` once per ready agent, up to 120 s each, in sequence.
- Each lazy respawn runs `squad-spawn` for a non-manager role, which ends with `squad-watchdog ensure --home <home>` (bin/squad-spawn:597-605). `ensure` -> `squad-start.watchdog_alive`: stale when `now - beat >= 3 * 60 s`.
- The beat is ~60 s old when the pass starts, so once one pass has spent about 120 s in respawns (e.g. 6-8 roles of one pod all at 55 min, ~15-20 s per respawn) `ensure` sees a stale beat and starts a second watchdog for the home: double prompts, double respawn attempts.
- Not an AC break and no test covers it. What would pass: write the beat (`write_state`) before each respawn, or run the cold pass after the beat write, or cap the respawns per pass; plus one test (fake respawn that advances time, assert `watchdog_alive`).

#### Follow-ups (not FAIL)
- Blocked/bg lines appear only after the 55-min age check (dev's deviation 1): fine, and it matches the spirit of the AC.

#### Verdict
FAIL 03 on bb06a32: F1 only. Everything else passes (see table). Re-hand-in: I recheck only bin/squad-watchdog and the new test (LC-3b).

### Re-check — sha 5937b61 — PASS (LC-3b: changed files only)
Throwaway detached worktree of 5937b61 (removed after).
- Diff vs bb06a32: bin/squad-watchdog (+6/-2) and tests/test_squad_watchdog.py (+20) only. `tick()` passes a `beat` callback (sets st["beat"]/st["pid"], `write_state`) that `cold_cache_pass` calls before each `squad-respawn --lazy`. Default `beat=lambda: None` keeps old callers working.
- F1 fixed: new test `test_the_heartbeat_stays_fresh_while_several_agents_are_respawned_in_one_pass` (3 respawns x 100 s, `watchdog_alive` True each time). With bin/squad-watchdog reverted to bb06a32 the test FAILS (alive list not all True); with the fix it passes.
- `python3 -m unittest test_squad_watchdog test_windows_safe test_utf8_helpers test_instructions`: 158 OK. Other grep hits unchanged by the diff (not rerun, LC-3b).
#### Follow-ups (not FAIL)
- Blocked/bg lines appear only after the 55-min age check (dev deviation 1): fine.
#### Verdict
PASS 03 on 5937b61.

## QA blackbox

### QA blackbox: ticket 03 (watchdog cold-cache pass), sha 5937b61 (checked merged with 01, cd95bc1)

Method: `live`. The real `squad-watchdog tick --home <scratch> --now <UTC>` ran in a scratch squad under /tmp: a scope home and a goal home, my own fake herdr (agent list/get/rename/start/close, logging each call), fake transcripts under a temp `CLAUDE_CONFIG_DIR`, and notes mtimes set with `touch -d`. The real `squad-respawn` ran against the scratch squad. 03 alone has no `--lazy` in its `squad-respawn` (that arrives with 01), so I ran it in a scratch clone with 03 and 01 merged, as ticket 04 will do. No real herdr, no live names. Source code was not read. Scratch dirs removed.

| AC | What I did | What I saw | Result |
|---|---|---|---|
| AC2 idle 54 vs 56 min | dev with last main turn 54 min ago, QA 56 min ago, both ctx 120k, at 12:00 | only the QA was prompted at 12:00; the dev was prompted at 12:01 (55 min) | pass |
| AC2 subagent turn | QA main turn 56 min old, a subagent turn 2 min old | QA still prompted | pass |
| AC3 eligible | QA with an open ticket | exactly one `agent prompt qb COLD CACHE: qb, your prompt cache expires in about 5 minutes. Write roles/qb.notes.md now (NOTE-1) ...`; log `prompted qb (1/2, ctx 120k, idle 56 min)` | pass |
| AC3 Manager / Team Lead | both idle 58-60 min, ctx 120-130k, ticket open | both prompted, then lazily respawned | pass |
| AC4 notes check and respawn | notes mtime after the prompt; polluted env `SQUAD_ROLE=team-lead SQUAD_NAME=tl SCOPE_DIR=/nonexistent` | `respawned lazy` for mgr, tl and qb in the same pass: rename, `agent start`, old pane closed, no `agent prompt` to the new session, `roles/<name>.lazy` = the roster session id, event `{"rule":"respawn","lazy":true}`. No second watchdog tab started | pass |
| AC4 failure path | (run before 01 was merged: `squad-respawn` refused `--lazy`) | `respawn lazy failed mgr: Usage: ...` logged, `gave_up_ts` set, no retry on later passes | pass |
| AC5 two prompts then give up | notes never written; passes at +1, +3, +6, +9, +20 min | prompts at 12:00 and 12:03 only (120 s apart), `gave up: notes not written` once at 12:06, nothing after, no respawn | pass |
| AC6 blocked / background shell / small | QA `blocked`; dev with a `bg` token; tl with ctx 30k | one log line each (`unavoidable: blocked`, `unavoidable: background shell`, `skipped: small context`), nothing sent, no repeat on the next pass. `working` agents untouched, silently | pass |
| AC6 boundary | ctx exactly 50000 | skipped, not prompted | pass |
| AC7 nothing open | dev owning a passed ticket, ctx 120k | `nothing open d2 (told tl)`; the Team Lead got `d2 has nothing open and a 120k context; retire it (COST-13b)` once; d2 not prompted or respawned | pass |
| AC8 state file | garbage in `watchdog.cold.json` | pass runs, prompts normally, file rewritten as valid JSON | pass |
| AC9 tunables | `SQUAD_WATCHDOG_COLD_CTX=200000`; `=abc`; `SQUAD_WATCHDOG_COLD=0` | ctx 120k skipped; bad value falls back to 50k (prompted); switch off: no prompt, no `cold-cache` log | pass |
| AC10 goal home | goal home with its own Manager `gm`, scope agents elsewhere; polluted env `SCOPE_DIR=<a scope>`, `SQUAD_ROLE=team-lead` | only `gm` prompted, then respawned lazily; marker in the goal's `roles/`, none in the scope's | pass |
| AC1 existing idle nudges | long idle spell | the 5 and 15 minute nudges still sent as before, alongside the cold-cache lines | pass |
| AC11 tests | `python3 -m unittest test_squad_watchdog` on the merged copy | 114 OK | pass |

Verdict: PASS.

Follow-ups (not blocking):
- Ticket 03 relies on 01's `--lazy`; until the 04 Developer merges both, a watchdog running 03 alone logs `respawn lazy failed` and gives up for that spell. This is by design and safe.
- Heartbeat fix F1 (5937b61) verified: the three respawns in one pass started no extra watchdog tab.
