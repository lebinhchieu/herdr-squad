# Evidence 12: one task-id grammar (integration, promotion; no rule ids)

## Behaviour

Base 2b535f5, code sha 9ca062f. `SQUAD_*` unset, `PYTHONDONTWRITEBYTECODE=1`, tests run in the foreground with `< /dev/null`. The evidence folder is `12-task-ids/` (what `squad-evidence path` returns), not `12/`.

**Tests.** `cd tests && python3 -m unittest test_squadtask test_squad_log_message test_squad_review_pack test_squad_spawn test_windows_safe test_utf8_helpers test_instructions`: **Ran 216 tests, OK** (SQ-10 trio included: windows_safe 14, utf8_helpers 14, instructions 16). The `grep -rl` hits of the changed names, each run: test_squad_ledger 17, merge_check 9, merge_record 3, watchdog 114, manager_guard 25, respawn 34, report_digest 11, tickets 22, session_lookup 16, squad_start 49, crlf 6, old_language_inventory 2, rules_contract 18, templates 8, squadboard_tasks 26, squadplan 12: all OK. `squad-process lint`: exit 0.

**AC1.** `test_integration_and_promotion_are_tasks_and_rule_ids_are_not` (test_squadtask): `claim integration --owner dev`, `handin promotion --sha abc1234`, `handin integration --sha abc1234` exit 0; `show --json` holds exactly two rows, `integration` (owner dev) and `promotion`; `claim SQ-10`, `claim 12x`, `claim Integration` exit 2. Base: exit 2 for `integration`.

**AC2.** `test_a_rule_id_in_the_text_is_no_task_and_integration_is` (test_squad_log_message), real hook through jq: `HANDIN integration`, `FAIL integration`, `STATUS integration: SQ-10 files clean` log `integration`; `PASS promotion` logs `promotion`; `STATUS: building SET-01, 60%, no blockers` logs null (base: `SET-01`); `HANDIN 12x` null; `HANDIN SQ-10: ...` still logs `SQ-10` (history). The old test `test_status_with_colon_finds_task_later_in_text` pinned the removed fallback and was replaced by it.

**AC3.** Same squadtask test: `from_message` with a `HANDIN SQ-10` record leaves the event store unchanged.

**AC4.** `test_integration_and_inline_files_and_aim_build_the_prompt` (test_squad_spawn): `squad-spawn dev X --task integration --dry-run --repo ...` prints `squad-task claim integration`; `--task SQ-10` exit 2 `bad --task value`.

**AC5.** Same test: `tasks/integration.md` with `Depends on: none · Files: \`bin/squadtask.py\`` (inline) builds the prompt; a ticket with `Aim:` and no `Duties:` builds it (Duties = the Aim); a ticket with no Duties anywhere exits 2 `no Duties: line`. `test_integration_pack_comes_from_its_draft` (test_squad_review_pack): `squad-review-pack integration` writes its pack.

**AC6.** `test_the_task_id_table_agrees_across_python_jq_and_bash` (test_squad_spawn): ids `12, 007, integration, promotion` accepted and `12x, SQ-10, Integration, integration2, ""` refused by `squadtask.is_task_id`, by `squad-spawn --task` (bash) and by `squad-log-message` (jq; a first-token rule id is the logged history case).

**AC7.** First commit 46d2f4b: ticket files 09-17 (each with Duties, Files, Aim, Estimate, Depends on) copied unchanged from `tasks/tickets/`; followups 02, 07, 08 `Status: wontfix` with a comment `superseded by 14`, `12`, `10`. Its sha went to the Team Lead before any code.

**Real data (messages.jsonl of this scope, read only).** The new jq filter over all 205 records: `integration` 14, `promotion` 7, `12` 1, null 17. The base `task` field of the same file holds `SQ-10` 11 times and `SQ-26` 2 times (7 `HANDIN integration` records with null). `squad-task-prompt integration --scope-home <po-clarity>` on the real `tasks/integration.md`: exit 2 `no Duties: line` (that file has none and no Aim), as AC5 says.

## Review

One fresh-context sonnet (high) subagent review of 2b535f5..f2bb7ed with a Standards and a Spec list (the code-review skill was not run as such).

**Standards.**
1. `evidence_check` compared `int(nn)`: for `integration` it raised and W9 showed the Python error text. Fixed (digits only), commit 9ca062f.
2. The int/isdigit pairing appears in `find_ticket`, `find_drafts` and `developer_of`; a helper would shorten it. Not done: style only.
3. Usage text of `squad-task` and `squad-review-pack` said `NN` only. Fixed. README rows `squad-spawn` and `squad-task-prompt` updated; the `squad-review-pack` README row is not in this ticket's Files list and stays.
4. Test economy: one test per risk, existing files extended.

**Spec.** AC1-AC6 hold. `TASK_ID` used `\d` (Unicode digits in Python, not in jq): fixed to `[0-9]+`. Left for a follow-up (not in AC or Files): `squadtask.ticket_text` and `TICKET_FILE` are digits only, so `Blocked by:` of `tasks/integration.md` is not read; `squadplan._draft_text`, `squadtickets.NUM_FILE`, `squadreport_tasks` and `squadboard_files` read `tasks/NN.md` by digits, so the board does not list `integration` from a draft.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `test_integration_and_promotion_are_tasks_and_rule_ids_are_not`: OK | - | - |
| AC2 | `test_a_rule_id_in_the_text_is_no_task_and_integration_is`: OK | - | - |
| AC3 | same squadtask test, `from_message` HANDIN SQ-10 writes no event: OK | - | - |
| AC4 | `test_integration_and_inline_files_and_aim_build_the_prompt`: OK | - | - |
| AC5 | same test and `test_integration_pack_comes_from_its_draft`: OK | - | - |
| AC6 | `test_the_task_id_table_agrees_across_python_jq_and_bash`: OK | - | - |
| AC7 | `git show 46d2f4b --stat`: 9 added, 3 edited | - | - |

## Changelog line

Task ids: `squad-task`, `squad-log-message`, `squad-spawn --task` and `squad-task-prompt` accept `integration` and `promotion` and never a rule id; `--task` falls back to `tasks/<id>.md` and the `Aim:` line and reads `Files:` after ` · `; why: integration hand-ins were logged with no task and rule ids became task events.
