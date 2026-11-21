# Evidence: 03 03 watchdog reads the bg token, cap, log reason

## Review

AC trace (Dev) | see `## Checks`
AC1 | tests/test_squadboard_agents.py::test_T03_1 | cd tests; python3 -m unittest test_squadboard_agents
AC2 | test_squad_watchdog.BgTest.test_decide_keeps_its_input... | python3 -m unittest test_squad_watchdog.BgTest
AC3 | BgTest.test_a_dev_with_a_token_holds... | same
AC4 | BgTest cap, working-pass and env tests | same
AC5 | BgTest.test_an_other_squads_token... | same
AC6 | BgTest.test_a_busy_roster_agent_holds_the_stop... | same
AC7 | BgTest cap and hold tests (exact lines) | same
AC8 | grep -rn SQUAD_WATCHDOG_BG_MAX bin/squad-watchdog README.md | shell
AC9 | SQ-10 and hit files | python3 -m unittest <file> in tests/
AC10 | diff touches two test files | git diff --stat 804c29c
AC11 | grep checks | shell

Branch squad/plugin/watchdog-shell/plugin-dev-watchdog-shell-2, commit 42ef899. `squad-evidence checks` exit 0.

### Behaviour
Run from `tests/` at 42ef899, all OK: test_squad_watchdog 78 (71 + 7 new BgTest), test_squadboard_agents 10 (9 + 1), test_squad_start 49, test_squad_log_message 25, test_squadtask 15, test_squadboard_inbox 12.
SQ-10: test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK.
Greps: `grep -rn "0\.9\.5" .claude-plugin/` empty; `grep -rln '0\.9\.5' tests/` empty; `SQUAD_WATCHDOG_BG_MAX` hits bin/squad-watchdog and README.md.
Not run: the full suite (Tech Lead's, after ASK).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `cd tests; python3 -m unittest test_squadboard_agents` 10 OK (test_T03_1; FIELDS and test_T08_TA1 unedited) | worktree 42ef899: `python3 -m unittest test_squadboard_agents` 10 OK; diff of parse_herdr read: bg only for non-empty string | n/a, unit test (whitebox) |
| AC2 | `python3 -m unittest test_squad_watchdog.BgTest.test_decide_keeps_its_input_and_loads_a_state_without_bg_keys` OK | re-check 3b1cd8e: probe tick with a fresh home and down.json exits 0 and logs `herdr does not answer`; `python3 -m unittest test_squad_watchdog test_squadboard_agents` 88 OK | n/a, unit test; live: 0.9.5 state file and herdr-down tick load, no crash: pass |
| AC3 | `BgTest.test_a_dev_with_a_token_holds_the_idle_spell_and_a_blocked_one_still_wakes` OK | `python3 -m unittest test_squad_watchdog` 78 OK; tick series on the live raw sample: no idle start while the token holds | live: held 0-75 no idle start; blocked agent stays blocked, WAKE at 10 min: pass |
| AC4 | `BgTest.test_the_cap_ends_the_hold_once_per_stretch...`, `test_a_working_pass_in_a_long_hold_resets_the_cap`, `test_the_cap_env_falls_back_to_60...` OK | tick series --now 10:00..11:07 on live raw sample: bg busy at 10:00, bg cap and idle start at 11:00, nudge 11:07; bg_max_s read: empty, abc, -5, nan, inf give 60, 0 gives off | live: cap at 60, reset by working pass (cap 51+60), absent token restarts, env values: pass |
| AC5 | `BgTest.test_an_other_squads_token_holds_the_sleep_until_the_cap_and_is_not_logged` OK | read of decide: `not machine_working and not busy`, busy covers every name in snap bg; test_an_other_squads_token run in the 78 | live: other squad token, sleep stub: none before cap, once at cap+5: pass |
| AC6 | `BgTest.test_a_busy_roster_agent_holds_the_stop_until_the_cap` OK | read of decide: working includes busy, stop branch uses working; test_a_busy_roster_agent_holds_the_stop in the 78 | live: all goals done + busy, no stop until cap: pass |
| AC7 | the exact log lines asserted in the cap test, `busy (bg shell)` in the hold test; test_squad_watchdog 78 OK | log lines of the live tick series match the ticket text exactly; one pair per stretch | live: exact `bg busy:` and `bg cap:` lines once per stretch, `busy (bg shell)` in idle end: pass |
| AC8 | `grep -rn SQUAD_WATCHDOG_BG_MAX bin/squad-watchdog README.md` hits both; README has the `hooks/herdr-bg` row | `grep -rn SQUAD_WATCHDOG_BG_MAX bin/squad-watchdog README.md` hits both; README hooks/herdr-bg row present | live: grep and README rows: pass |
| AC9 | windows_safe 14, utf8_helpers 14, instructions 16 OK; hit files: squad_start 49, log_message 25, squadboard_agents 10, squadtask 15, squad_watchdog 78, squadboard_inbox 12, all OK | `python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_squad_start test_squad_log_message test_squadtask test_squadboard_inbox` run in worktree | n/a, tests (whitebox) |
| AC10 | tests only in the two existing files; the two real rows are the fixture in test_T03_1 | `git diff --stat main 42ef899 -- tests/` shows only the two existing files | n/a (whitebox) |
| AC11 | `grep -rn 0.9.5 .claude-plugin/` empty; `grep -rln 0.9.5 tests/` empty; v19 at the top of changelog.md | `grep -rn 0.9.5 .claude-plugin/` empty; `grep -rln 0.9.5 tests/` empty; v19 first in changelog.md | live: plugin.json 0.9.6, no 0.9.5 in .claude-plugin, v19 on top: pass |

## QA whitebox

### QA whitebox 03: watchdog reads the bg token
Sha 42ef899 (based on main 804c29c). Verdict: FAIL, one finding. Checks table: `checks.md` (my column).

#### Finding 1 (breaks technical AC 2 and an existing behaviour)
`bin/squad-watchdog:413` (`tick`): `snap["busy"] = st["bg_busy"]`. When herdr does not answer, `decide` returns early (the `not snap["ok"]` branch, before `st["bg_busy"]` is set), so a state without `bg_busy` (a fresh home, or any 0.9.5 state file) makes `tick` raise `KeyError: 'bg_busy'`.
Reproduced: temp home with a roster, `echo '{"id":"x","error":{"code":"server_not_running"}}' > down.json`, `squad-watchdog tick --home H --manager s1-mgr --herdr-json down.json` -> traceback, rc 1, no log, no state. The same command on main (804c29c) exits 0 and logs `herdr does not answer (herdr not running); no idle check until it does`.
Why it matters: AC 2 says a state without `bg_since`/`bg_busy` loads; under `run` the exception is caught as `pass failed: KeyError` every pass, so the `down` line is never logged and no state is written until herdr answers. The existing herdr-down tests pass only because their state already holds `bg_busy` from an earlier ok tick.
What passes: `snap["busy"] = st.get("bg_busy") or []` (or set the keys before the early return), plus one test: `tick` with a recorded herdr-down file on an empty home logs the `down` line and does not raise (extend the existing herdr-down test to start from no state).

#### Checked and fine
- parse_herdr: `bg` only for a non-empty string; status unchanged; FIELDS and test_T08_TA1 unedited.
- decide: deepcopy keeps `st`; bg clock per name resets on working, blocked, gone, no token; no re-arm after the cap; `bg_max` 0 off; machine check and stop use busy; bg_cap logs once per stretch.
- `bg_max_s`: empty, abc, -5, nan, inf give 60; 0 is off.
- Live run (REV-5b): tick series on the real `herdr agent list` sample (evidence/03 raw file, team lead `done` with `bg: ⏵ 1 shell`): `bg busy` at 10:00, no idle start through 10:30, `bg cap` and `idle start` at 11:00, nudge at 11:07. Exact log text as in the ticket.
- Tests: watchdog 78, agents 10, windows_safe 14, utf8 14, instructions 16, squad_start, log_message, squadtask, squadboard_inbox OK. Version, changelog v19, README rows present.

#### Follow-ups (no return for these)
- The README row for `bin/squad-watchdog` is one very long line; the added text sits after `the log tail` with no full stop before it (the missing stop was there before).

#### Re-check on 3b1cd8e (diff 42ef899..3b1cd8e: bin/squad-watchdog line 413, one test)
Verdict: PASS. Finding 1 fixed: `snap["busy"] = st.get("bg_busy") or []`. My probe (fresh home, herdr-down file) now exits 0 and logs `herdr does not answer`; the extended herdr-down test deletes the state file and ticks without raising. `test_squad_watchdog` and `test_squadboard_agents`: 88 OK. No other file changed.

## QA blackbox

### QA blackbox 03: watchdog reads the bg token (final sha 3b1cd8e)

Method: `squad-watchdog tick` run as a black box in scratch homes (own roster.md, goals.md), recorded herdr JSON via `--herdr-json`, `--now` stepping one minute per tick, a stub `herdr` on PATH that logs argv (no real prompt sent), `SQUAD_WATCHDOG_SLEEP_CMD` set to an `echo` (no real suspend). Scenarios ran on a clean `git archive` of 42ef899 and again on 3b1cd8e (the worktree held an uncommitted edit during the first run). No source read. Scratch dirs removed afterwards.

| AC / behaviour | live: what I did | what I saw (3b1cd8e) | Result |
|---|---|---|---|
| AC3/AC7 hold + exact lines | roster `mgr` idle, `tl` done with `bg=⏵ 1 shell`, ticks min 0-75 | `bg busy: tl has a background shell (⏵ 1 shell); counted as working for at most 60 min` once at 12:00; no idle start, no nudge while held | pass |
| AC4 cap | same run | 13:00 `bg cap: tl counted as working for 60 min; idle check resumes`, then `idle start` same minute, nudge 5 at 13:05, nudge 15 at 13:15 | pass |
| AC4 working pass resets | token 0-49, `working` at 50, token 51-115 | second `bg busy` at 12:51, cap at 13:51 (51+60), idle start then | pass |
| AC4 token absent one pass | absent at 30, back at 31 | `idle start` 12:30; 12:31 `bg busy` again, `idle end after 1 min ... tl busy (bg shell)` | pass |
| AC4 SQUAD_WATCHDOG_BG_MAX | `""`, `abc`, `-5`, `5`, `0` | first three: 60 min; `5`: busy 5 min, cap at 12:05; `0`: no `bg busy`, idle start at the first pass | pass |
| AC3 blocked agent with token | `tl` blocked + token; mgr working 16 min | no `bg busy` line; WAKE sent at 10 min; with mgr idle the idle start reads `tl blocked` | pass |
| working agent with token | `tl` working + token | no `bg busy` line | pass |
| AC5 machine check | sleep on, another squad's agent idle with token, roster idle | no sleep at min 11; one `sleep pc` at 13:05 (cap 13:00 + 5), no `bg busy` line for the other agent; control with no token sleeps at 5 min | pass |
| AC6 no early stop | every goal `done`, `tl` busy, ticks 0-58 | no `all goals done; watchdog stops`; stop line at 13:00 right after the cap; control with no token stops at the first pass | pass |
| tokens shapes | `tokens` null, `[]`, `{}`, `{"bg": ""}` | exit 0, no `bg busy` | pass |
| 0.9.5 state file | state without bg keys | exit 0, `bg busy` logged | pass |
| manager itself with `⏵ 1 shell · 1 monitor` | only agent | `bg busy: mgr ...` | pass |
| herdr down (3b1cd8e fix) | no `--herdr-json`; herdr exits 1, or not on PATH; fresh home, state without bg keys, and mid-hold | exit 0 each time; log `herdr does not answer ...`, then `herdr answers again`; hold resumes. On 42ef899 the same call died with `KeyError: 'bg_busy'` | pass (fix confirmed) |
| AC8 docs | grep, README, changelog | `SQUAD_WATCHDOG_BG_MAX` in `bin/squad-watchdog` and README row; README row for `hooks/herdr-bg`; plugin.json 0.9.6, no `0.9.5` in `.claude-plugin/`, `v19` on top of changelog | pass |
| AC1, AC2, AC9, AC10 | not mine (unit tests, code) | - | n/a, QA whitebox |
| AC11 | version and changelog seen above | - | pass |

Follow-ups (not AC): none. The repeated `all goals done; watchdog stops` lines in my run are my driver ticking on after the stop; `run` returns at the first one.

Verdict: PASS for 3b1cd8e.
