# 02 `homes --apply --yes` respawns the moved homes' live agents: evidence

## Review
AC trace (run from `tests/`: `python3 -m unittest test_squadupgrade.Homes`):
- AC1 | `Homes.test_respawn_prompts_then_respawns_in_order_with_each_own_home_and_skips_the_caller` (prompt before respawn per agent, pod before coordinator, no call for caller, SQUAD_DIR + one of SCOPE_DIR/GOAL_DIR per agent's home) | unittest
- AC2 | same test: respawn path = `<target runtime>/bin/squad-respawn`, no `--force` | unittest
- AC3 | `Homes.test_a_prompt_without_done_leaves_the_agent_pending_exit_4_and_the_rest_respawn` | unittest
- AC4 | `Homes.test_no_herdr_call_without_yes_or_with_no_respawn_and_the_plan_is_listed` (empty `HERDR_LOG`) | unittest
- AC5 | first test: roster row `retired` never called; `DEAD` agent prints `not running s2-tech` | unittest
- AC6 | three whole-repo tests + `test_squad_respawn`, quoted below; subprocess calls are list argv with `sys.executable` | unittest
- AC7 | `## Behaviour`, "Not verified"
- AC8 | first test: last stdout line is the `caller mgr: ...` line; the pending test asserts no `caller` line without a caller row | unittest
- AC9 | pending test: `--timeout 50` in the prompt call; `prompt_ms()` falls back to 300000 on `x` | unittest
- AC10 | `Homes.test_a_home_refused_at_read_is_named_by_apply_and_exits_2` (stderr `refused scope solo`, exit 2, snapshot unchanged) | unittest
- AC11 | choice: the table is printed before the move (its `pin now` is the old pin); each `moved <home>: old -> new` line is the result | read `run()` in `bin/squadhomes.py`

## Behaviour
Tests (from `tests/`): `python3 -m unittest test_squad_respawn test_windows_safe test_utf8_helpers test_instructions test_squadupgrade`: 117 tests, OK. `test_squadupgrade.Homes test_squad_close` (hits of `grep -rl fake_herdr tests/`, squadtest.py gained a `FAIL_PROMPT` case): 88 tests, OK.

Design notes: a prompt that exits non-zero (herdr's `--wait` timeout) or does not return within timeout + 30 s is `pending`; the herdr stdout is not parsed for the word DONE (retire does the same). Test stub: B's `bin/squad-respawn` in the fixture plugin records argv and env to `HERDR_LOG`.
Exit codes: 0 all respawned / not running, 4 moved but one pending, 3 `--yes` missing (output lists `would respawn:` lines).

Not verified (stub only): a real agent mid-turn answering PIN-MOVE, the real `squad-respawn` run by this tool, and the new herdr tab. Chieu checks at merge: run `squad-process homes --apply --yes` in a real squad with one live agent and confirm its new tab opens from its notes.
