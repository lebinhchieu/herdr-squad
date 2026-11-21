# Evidence 04: usage events carry ctx; retire and spawn logged; orphan fresh flagged; 0.10.1

## Review
AC trace (ticket AC / QA whitebox T):
- AC1 / T1 | tests/test_squad_usage_hook.py::test_fixture_over_the_line_gives_fresh_message_and_event (ctx, line 110002, turns 2); tests/test_squad_usage.py::test_check_detail_adds_ctx_line_and_turns_while_check_stays_one_word | `python3 tests/test_squad_usage_hook.py`, `python3 tests/test_squad_usage.py`
- AC2 / T2, T3 | tests/test_squad_retire.py::test_retire_appends_a_retire_event_and_a_log_failure_only_warns; tests/test_squad_spawn.py::test_a_real_spawn_logs_one_spawn_event_but_a_respawn_and_a_dry_run_log_none; tests/test_squad_respawn.py (a respawn leaves exactly one new line) | `python3 tests/<file>.py`
- AC3 / T4, T5 | tests/test_squad_usage.py::OrphanFreshTest (flag, respawn/retire clears, missing/empty/corrupt log) | `python3 tests/test_squad_usage.py`
- AC4 / T6 | `grep -rn '0\.10\.0' .claude-plugin/` prints nothing (exit 1); plugin.json line 4 is 0.10.1; tests/skills/docs hits of 0.10.0 are changelog, ADR 0030 and tests/test_squadruntime.py (fixture), left alone
- T7 | test_windows_safe 14 OK, test_utf8_helpers 14 OK, test_instructions 16 OK; also test_squadruntime, test_squad_start, test_squadupgrade OK
- T8 | test_squad_usage 30 OK, test_squad_usage_hook 13 OK, test_squad_retire 4 OK, test_squad_respawn 33 OK, test_squad_spawn: 107 of 108 OK

Field name (T2): `rule` names the event (`fresh`, `respawn`, now `retire`, `spawn`), the same key as the existing records, so the hook's dedupe and every reader keep working. `retire` and `spawn` carry `scope`; `spawn` also `session`. Logger: new `bin/squad-event` (same flock / mkdir lock as squad-respawn). A respawn is told apart by `SQUAD_RESPAWN=1`, which squad-respawn sets for squad-spawn. The hook gets ctx, line and turns from `squad-usage --check-detail` (same summarize and respawn_line as the row); `--check` still prints one word.

Known failing on base: tests/test_squad_spawn.py::test_a_failed_agent_start_leaves_the_old_overrides_file (fails identically on 432b8ea; SQ-17 grep hits 10 earlier iteration files, so it is a repeat: Chieu needs to be asked / a fix ticket).

## Behaviour
Table note (T4): `note: fresh with no later respawn or retire: AGENT (ctx/line)`; ctx/line shown only when the fresh record carries them (old records print the name alone). A `fresh` followed by `respawn` or `retire` of the same agent is not flagged; blank, corrupt, non-object lines are skipped; a missing log is fine.

Real log lines read by the parser (`.claude/squads/plugin/scopes/pending-fixes/usage-events.jsonl`, written before this change, so no ctx):

    {"ts":"2026-11-21T14:32:04.723Z","agent":"plugin-dev-pending-fixes-2","role":"dev","session":"9c47...","rule":"fresh","action":"write roles/..."}
    {"ts":"2026-11-21T14:08:20.850Z","agent":"plugin-mgr-pending-fixes","role":"manager","rule":"respawn"}

Live run (read-only), last line of `squad-usage` on this squad:

    note: fresh with no later respawn or retire: plugin-dev-pending-fixes-2

(the Manager's respawn record is not flagged; dev-2's fresh has no later respawn or retire.)
