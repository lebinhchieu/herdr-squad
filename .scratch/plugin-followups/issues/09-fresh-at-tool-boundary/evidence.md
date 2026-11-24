# Evidence: 09 fresh check also runs at a tool boundary
sha: 940939b

## Behaviour

Code sha 940939b (base 6b1b601, tickets 10 and 11 below it). Files: `bin/squad-usage-hook`, `hooks/hooks.json`, README row `squad-usage`, `tests/test_squad_usage_hook.py`, `tests/test_hooks_json.py`; plus, agreed with the Tech Lead (ANSWER 09), `bin/squad-usage` and `tests/test_squad_usage.py`: `--check-detail` now prints `none<TAB>ctx<TAB>line<TAB>turns` when no rule fires (`--check` and the `fresh` line are unchanged; `--help` says so), because the stamp needs ctx and line on a miss. The hook treats `none` as no rule. `overwritten` in the plan's stamp list is no field (Tech Lead): the file is rewritten each run.

- AC1: `test_usage_hook_on_stop_and_once_on_post_tool_use_without_matcher` (test_hooks_json): exactly one `squad-usage-hook` under PostToolUse (no matcher, `timeout` 10) and one under Stop. Base: 0 and 1.
- AC2: `test_fresh_notice_is_context_json_exit_0_once_per_session`: PostToolUse, transcript at 130k past the 110k line, no record: stdout `{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"Cost rule 'fresh' fired: ..."}}`, exit 0, empty stderr, one `fresh` record; stamp deleted and a second call: no output, still one record.
- AC2 under concurrency (review finding, fixed): `test_parallel_calls_of_one_session_record_and_notify_once`: 6 parallel calls give 1 notice and 1 record. Red on 75b0117 (dedupe outside the lock) 3 of 3 runs, green on 940939b 3 of 3 runs.
- AC3: `test_growth_under_the_step_skips_the_check_and_keeps_the_stamp`: stamp size = size - 65,535: no output, stamp byte-equal, no record; control with size - 65,536: the check runs, `fresh` printed, stamp size moves to the transcript size. `test_a_stamp_of_another_session_does_not_throttle`: a respawned session is checked at once.
- AC4: `test_manager_unknown_session_and_missing_transcript_are_silent`: Manager, unknown session, non-squad session, missing transcript: exit 0, empty stdout and stderr, no record.
- AC5: `test_stamp_holds_ts_session_size_ctx_line_after_post_and_after_stop`: after a PostToolUse run and after a Stop run (no rule firing) the stamp holds `ts`, `session`, `size` (= transcript bytes), `ctx` (>= 49,999), `line` (110,002).
- AC6: the 13 Stop tests are unedited (the diff only moves `setUp`/`run_hook`/`transcript` into `HookBase` and gives `transcript` an optional `pad`) and pass; `test_stop_stays_exit_2_with_stderr` checks Stop stays exit 2 with the text on stderr. test_squad_usage_hook: 20 tests OK.
- AC6 latency, measured: 100 skipped PostToolUse calls on a 1,048,832-byte transcript with a current stamp: `real 0m0.726s` in total (0.767 s on a first run), about 7 ms each, limit 10 s. The reviewer measured 0.65 s on 5.5 MB.
- Real data (REV-5a, read-only; `SQUAD_DIR` a /tmp dir, `SCOPE_DIR` unset): this session's transcript (687 KB): hook exit 0, no output, stamp `{"ts":"2026-11-24T17:18:07.936Z","session":"9dd05f4b-...","size":798187,"ctx":71126,"line":102169}`, no `usage-events.jsonl`; a second call right after: exit 0, no output (throttled).
- Tests (foreground, one file at a time, all OK): test_squad_usage_hook 20, test_hooks_json 7, test_squad_usage 40 (new `test_check_detail_prints_none_with_the_numbers_when_no_rule_fires`), grep hits test_session_lookup 16, test_squad_manager_guard 25, test_squad_respawn 34; SQ-10 trio: test_windows_safe 14, test_utf8_helpers 14, test_instructions 16.
- Not live: the PostToolUse entry reaches running agents at their next session start, so no agent has fired it yet.

## Review

Fresh sonnet/high subagent on `6b1b601..75b0117`; checks are in `## Checks`.
- Standards: the stamp write let a `Permission denied` redirect error reach stderr when `roles/` is read-only (exit stayed 0): fixed by wrapping the redirect in `{ ...; } 2>/dev/null`. The test module docstring named only the Stop hook: fixed. Noted, no change: a run where `squad-usage` prints nothing still writes the stamp (size set, ctx 0, line 0), as the design says "after every run".
- Spec: AC1 to AC5 met; Stop path unchanged. One bug: the once-per-session dedupe was check-then-append outside the lock, so 6 parallel PostToolUse calls gave 3 records and 3 notices. Fixed: the check now runs inside the flock or mkdir lock and only the call that appends prints the notice; test above.
- Checked and fine: IFS unit-separator reads, invalid JSON input, BSD `wc -c` padding, atomic `mv` of the stamp, other-session / shrunken / corrupt stamp all run the check.

## Checks

| AC | Dev: test or capture | QA whitebox | QA blackbox |
|---|---|---|---|
| AC1 | `test_usage_hook_on_stop_and_once_on_post_tool_use_without_matcher` OK: 1 under PostToolUse, 1 under Stop | - | - |
| AC2 | `test_fresh_notice_is_context_json_exit_0_once_per_session` OK; `test_parallel_calls_of_one_session_record_and_notify_once` OK, red on 75b0117 | - | - |
| AC3 | `test_growth_under_the_step_skips_the_check_and_keeps_the_stamp` OK: stamp unchanged at 65,535, moves at 65,536 | - | - |
| AC4 | `test_manager_unknown_session_and_missing_transcript_are_silent` OK | - | - |
| AC5 | `test_stamp_holds_ts_session_size_ctx_line_after_post_and_after_stop` OK | - | - |
| AC6 | 13 Stop tests OK unedited; 100 skipped calls on 1 MB: `real 0m0.726s` | - | - |

## Changelog line

usage hook: also runs after a tool call (PostToolUse, throttled to one check per 64 KiB of transcript growth, stamp `roles/<agent>.usage-check`) and `squad-usage --check-detail` prints `none` plus the numbers when no rule fires; why: `fresh` ran only when a turn ended, so a long run of tool calls went 70k to 240k past the line with no notice.
