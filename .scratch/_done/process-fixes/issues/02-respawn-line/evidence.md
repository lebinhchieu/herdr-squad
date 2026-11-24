# Evidence 02 One respawn line per session

## Behaviour
AC1. Command: `bin/squad-usage --check x --transcript <fixture>` on four fixture transcripts (read at 40k, first Write at 99k, then a last turn). Seen:
- first action 99k, last 148k: prints nothing (line 149k).
- first action 99k, last 150k: prints `fresh`.
- first action 150k, last 179k: nothing; last 181k: `fresh` (line capped at 180k, not 200k).
- Tests: `test_check_fresh_at_first_action_plus_50k` (110k line, 99k-start line 149k), `test_the_line_never_passes_180k`, `test_the_first_action_is_the_first_edit_write_or_send_not_a_read`, `test_before_a_first_action_only_the_cap_applies`, `test_a_subagent_action_does_not_set_the_line`, `test_an_idle_session_past_its_line_is_fresh_there_is_no_idle_line`.
- Stop hook: `test_fixture_over_the_line_gives_fresh_message_and_event` (first action 60k, last 130k: exit 2, message names the respawn line, no `120k`).
- Manager: `test_the_line_is_the_sessions_own_not_a_fixed_number` (first action 99k: 144k silent, 150k notice `over its 149k line`).

AC2. `grep -rnE '\b(100k|120k|90k)\b|100_000|120_000' bin templates README.md hooks agents skills` finds nothing. COST-1, 2, 3, 5, 5a, 6a, 6b, 8, 9, NOTE-3 and the iterations.md text point at COST-3 / `fresh`; COST-3 defines the line once. `bin/squad-process lint` rc=0. The 80k (COST-6) and 60k (COST-10) values are not respawn lines and stay.

AC3. Fixed-line rules found outside the plugin, not edited:
| File | Rule | Fixed value |
|---|---|---|
| `.claude/squads/plugin/process.local.md:25` | SQ-3 (this squad's overlay) | over 100k |
| `.claude/squads/board/process.local.md:8` | SQ-1 Manager reads usage | over 100k |
| `.claude/squads/board/process.local.md:10-15` | SQ-2 Developer band | 100k at ticket open, 100k at HANDIN |
| `.claude/squads/board/process.local.md:29` | SQ-4 QA finishes the check | never pass 100k |
| `.claude/squads/board/process.local.md:36` | SQ-5 Developer reads its row | over 100k at HANDIN |
| `.claude/squads/board/process-log.md:8-9` | log of SQ-1, SQ-2 | 100k |
| `docs/adr/0016-process-composed-per-role.md:63` | Developer retirement (history) | 120k |
| `.claude/squads/accounts/process-log.md:8` | log line | "120k is COST-3 already" |

## Tests
Run (touched and `grep -rl` hits): test_squad_usage 23, test_squad_usage_hook 10, test_squad_manager_guard 25, test_dev_rules_size 9, test_rules_wording 17, test_rules_contract, test_sizes, test_processlint, test_instructions, test_squadcompose, test_squad_respawn, test_squadruntime, test_templates, test_crlf_squad_files, test_hooks_json, test_utf8_helpers, test_windows_safe: OK. Size guard: Manager baselines raised by the exact growth (118-132 B).

## Review
AC trace:
AC1 | tests/test_squad_usage.py (6 tests above), test_squad_usage_hook.py, test_squad_manager_guard.py | `cd tests; python3 test_squad_usage.py` (same for the others)
AC2 | templates/squad/process/cost.md, notes.md, iterations.md; test_rules_wording::test_lint_resolves_every_pointer; grep above | `bin/squad-process lint`; `cd tests; python3 test_rules_wording.py`
AC3 | table above (`## Behaviour`, AC3) | read; no overlay or ADR file edited (`git diff --stat` shows none)
