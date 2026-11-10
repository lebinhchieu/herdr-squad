## Behaviour

`squad-spawn <role> <name> --scope S --task NN` now builds the first prompt with the new `bin/squad-task-prompt` (+ `bin/squadtaskprompt.py`). Inputs: the ticket (`squadreviewpack.find_ticket`, same finder as 05), its `Duties:` and `Files:` lines, scope.md `team:`, roster.md. The HANDIN target comes from `squadrules.resolve_duties(team)["handin-target"]` (no second copy of the chain). The two ticket lines are quoted with `json.dumps`. `--prompt` text is appended after the built part. A missing ticket, `Duties:`, `Files:` or target roster row exits 2 before any worktree, label or herdr call. A checker role (qa-whitebox, qa-blackbox) gets a prompt and claims nothing; the Developer is named only when a roster row `Owns` ticket NN. `--dry-run` prints `would run: herdr agent prompt ...`.

Test fixture change (needed by AC3): `SpawnTaskClaimTest` now writes tickets 03/04 with `Duties:`/`Files:` and manager/QA roster rows (`add_task_fixtures`), because `--task` without a ticket now refuses. No assertion changed. `test_a_failed_agent_start_leaves_the_old_overrides_file` fails the same way on the unchanged HEAD (pre-existing, not from 06).
Also fixed: `squadreviewpack.py` used `Path.write_text(newline=)`, which `test_windows_safe` rejects; now `open(..., newline="\n")`.

## AC trace

| AC | Test | How run |
|---|---|---|
| AC1 prompt content, `--prompt` after (T5) | `SpawnTaskPromptTest.test_a_qa_team_hands_in_to_both_qas` | `cd tests && PYTHONPATH=. python3 -m unittest test_squad_spawn` |
| AC2 / T2 HANDIN target | same test; `test_a_no_qa_team_hands_in_to_the_team_lead_else_the_manager` | same |
| AC3 / T1 refusal, zero herdr calls, no worktree | `test_a_ticket_with_a_missing_field_or_roster_row_stops_the_spawn` (no Duties, no Files, no ticket, `../x`, no team-lead row; real run, not dry) | same |
| T4 quoting | `test_ticket_lines_are_quoted_data_and_nothing_runs` (quotes, backticks, `$(touch pwned)`) | same |
| T6 checker, dev claim unchanged | `test_a_checker_gets_a_prompt_and_claims_nothing`; `SpawnTaskClaimTest` unchanged assertions | same |
| AC4 / T7 | `test_squad_spawn` 105 tests, 1 failure (pre-existing, see above); hits of `grep -rl squad-spawn tests/`, `test_no_bare_bash`, `test_hooks_json`, `test_windows_safe` OK | targeted runs |
| T3 real sample | below | manual |

## Real dry-run sample (T3)

`SQUAD_DIR=.../squads/plugin HERDR_ENV=1 bin/squad-spawn <role> x --scope fable-advisor --task 06 --prompt EXTRA --dry-run`, prompt line only:

### dev
```
would run: herdr agent prompt x Ticket 06 of scope fable-advisor. Ticket file: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor/tasks/06
-spawn-task.md. Scope folder: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor. Team: qa-white, qa-black. Duties (quoted from the ticket
): "plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-own
er=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).". Files to read first (quoted from
 the ticket): "`bin/squad-spawn`, tests that cover it (`grep -rl squad-spawn tests/`)". You are x, the Developer. Your working directory is your worktree. Build
 this one ticket as written; run squad-label first. HANDIN to plugin-qaw-fable-advisor and plugin-qab-fable-advisor. Ask plugin-qaw-fable-advisor for technical 
acceptance criteria and plugin-mgr-fable-advisor for anything else. EXTRA
```
### qa-whitebox
```
would run: herdr agent prompt x Ticket 06 of scope fable-advisor. Ticket file: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor/tasks/06
-spawn-task.md. Scope folder: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor. Team: qa-white, qa-black. Duties (quoted from the ticket
): "plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-own
er=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).". Files to read first (quoted from
 the ticket): "`bin/squad-spawn`, tests that cover it (`grep -rl squad-spawn tests/`)". You are x, qa-whitebox. Check this ticket when plugin-dev-fable-a sends 
HANDIN; send PASS or FAIL to that Developer. Plain questions go to plugin-mgr-fable-advisor. EXTRA
```
### qa-blackbox
```
would run: herdr agent prompt x Ticket 06 of scope fable-advisor. Ticket file: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor/tasks/06
-spawn-task.md. Scope folder: /home/chieule/workspace/squad/.claude/squads/plugin/scopes/fable-advisor. Team: qa-white, qa-black. Duties (quoted from the ticket
): "plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-own
er=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).". Files to read first (quoted from
 the ticket): "`bin/squad-spawn`, tests that cover it (`grep -rl squad-spawn tests/`)". You are x, qa-blackbox. Check this ticket when plugin-dev-fable-a sends 
HANDIN; send PASS or FAIL to that Developer. Plain questions go to plugin-mgr-fable-advisor. EXTRA
```
