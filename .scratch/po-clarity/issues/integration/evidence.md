# integration: 02, 07 and main merged into 05's branch: evidence

## Behaviour

Merge order on 05's branch (`e0ab63b`): 02 (`e2b05c8`), 07 (`eaab72e`), then `main` (`9b74b02`). Conflicts: only `skills/squad-process-update/changelog.md` (02, main) and `.claude-plugin/plugin.json` (main).
- `plugin.json` keeps 0.11.0; changelog v31 sits above main's v30; v29 (0.10.11) is untouched; ADR 0034 comes from main.
- 02's own `## v29` heading (ITER-19 text) is not kept: its bullet is in v31 (the plan said one heading), with the ITER-19 word added to the process-update line of Deploy.
- v31 now has one bullet each for 01, 03, 04, 07, 05, 02 and LC-9c. Deploy names 0.11.0, a `squad-board` restart (07's image mode of `/api/file`), the po-inbox restart, and the `squad-inbox add` bare-ID refusal every Manager meets (exit 2); Rollback says the refusal goes with the revert.

Two tests failed on the integrated tree and on their own bases, so both were fixed here (one line each):
- `test_squadinbox::ProjectionTest::test_contract_shape`: red on 05's sha `e0ab63b` (the `KEYS` set lacks the `plan` key 05 added). `KEYS` now has `plan`.
- `test_session_lookup::HookTest::test_every_squad_hook_of_hooks_json_calls_the_lookup`: red on `main` (the new `squad-handin-gate` hook is in `hooks.json` but not in `HOOKS`); `bin/squad-handin-gate` calls `squad-whoami`, so it belongs there. `HOOKS` now has it.

Tests (SQUAD_* unset, `PYTHONDONTWRITEBYTECODE=1`, from `tests/`, foreground, `< /dev/null`), all OK on the final tree:
- Named set: `test_squadboard_panels` (66), `test_rules_wording` (31), `test_instructions` (16), `test_processlint` (31).
- SQ-10 trio: `test_windows_safe` (14), `test_utf8_helpers` (14), `test_instructions` (16).
- Others touched or merged in: `test_hooks_json` (6), `test_squadtask` (19), `test_squadboard_server` (20), `test_squadinbox` (59), `test_session_lookup` (16).
- `grep -rl` hits of the changed paths: `test_po_inbox_contract`, `test_squadplan`, `test_squadboard_inbox`, `test_squadboard_files`, `test_squadboard_page`, `test_squadboard_tasks`, `test_squadtickets`, `test_squad_evidence`, `test_templates`, `test_squadcompose`, `test_squadupgrade`, `test_old_language_inventory`, `test_squad_merge_check`, `test_squad_review_pack`, `test_squad_close`, `test_squad_start`, `test_squad_team`, `test_squad_log_message`, `test_promotion_0_6_0`, `test_run_suite`, `test_squadboard_list`, `test_squadboard_grid`, `test_squadruntime`.
- `squad-process lint` exit 0. `claude plugin test`: 652 pass, 0 fail (po-inbox pane, incl. 05's plan line).
- Full suite: not run (no yes from Chieu; the Tech Lead runs the SQ-10 trio and asks).

Board, both changes on one page (`squad-board --squad <demo copy> --scope alpha-ui`, demo copy of the fixture; inbox item E2 blocks task `02`, ticket `tasks/01-order-page.md` added). E2 shows 05's plan line `task 1 of 1 · step 1 · next: nothing, last one` under its title, and the Files panel row for the ticket has 07's Preview open (title, Aim, Problem), with no clash between the two panels. Browser and both servers were closed after.

![plan line on E2 and the ticket Preview open on one board](img/board-plan-line-and-preview.png)

## Review

Run: `/mattpocock-skills:code-review` since 05's sha `e0ab63b` (two sub-agents, sonnet, high).
