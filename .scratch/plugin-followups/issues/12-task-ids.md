# 12 One task-id grammar: integration, promotion, no rule ids

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/04-task-ids.md`, Token Coach proposal 4; absorbs followups 07)
Blocked by: none
Aim: Task ids accept integration and promotion, never rule ids
Estimate: 3h
Depends on: none

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/12.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. **First commit, before any code:** add the ticket files 09-17 from `$SCOPE_DIR/tasks/tickets/` to `.scratch/plugin-followups/issues/` unchanged, and set followups 02, 07 and 08 to `Status: wontfix` with a comment `superseded by 14`, `12` and `10`; send the Team Lead that sha. No other Developer commits a ticket file.
Files: `bin/squadtask.py`, `bin/squad-log-message`, `bin/squad-spawn`, `bin/squadtaskprompt.py`, `bin/squadreviewpack.py`, README rows `squad-spawn` and `squad-task-prompt`, `.scratch/plugin-followups/issues/09..17-*.md`, `.scratch/plugin-followups/issues/02-evidence-checks-md.md`, `07-ticket-duties-line.md`, `08-usage-last-session.md`, `tests/test_squadtask.py`, `tests/test_squad_log_message.py`, `tests/test_squad_spawn.py`, `tests/test_squad_review_pack.py`

## Problem
`squad-task` rejects `integration` and `promotion` (exit 2: `claim needs one ticket number`), so those tasks have no record; `squad-log-message` logs `HANDIN integration` with task null (7 such records in this scope's `messages.jsonl`). Its jq fallback takes the first rule id anywhere in the text, so 3 hand-ins were logged as task `SQ-10` and `from-message` turned them into task events. `squad-spawn --task` refuses a ticket with no Duties line (followups 07), and refuses the task files whose `Files:` follows ` · `.

## Change
- One definition in `squadtask.py`: `TASK_ID = r"\d+|integration|promotion"` and `is_task_id(s)`. The other copies (jq in `squad-log-message`, `HANDIN_TASK`, the bash regex in `squad-spawn`, `squadtaskprompt.parse`, `squadreviewpack.parse`) accept the same set.
- The rule text MSG-3 stays as is (numbered tickets remain the rule; the two names are tolerated spellings): the Developer rules have no byte headroom.
- `squad-log-message`: drop the fallback "first rule id anywhere in the text"; a rule id as the first token is still logged as before. `from_message` writes no event for a task that is not `is_task_id`.
- `squad-task-prompt` and `squad-spawn --task`: Duties come from the ticket, else `tasks/<id>.md`, else the ticket's `Aim:` line; `Files:` is found at line start or after ` · `; no Duties anywhere still refuses. `find_ticket` finds `tasks/integration.md`.

## AC
- AC1: `squad-task claim integration --owner X` and `handin promotion --sha S` exit 0 and fold to one row each; `claim SQ-10` and `claim 12x` exit 2 (base: exit 2 for `integration`).
- AC2: `squad-log-message`: `HANDIN integration: ...` and `FAIL integration: ...` log task `integration`; `STATUS integration: ... SQ-10 ...` logs `integration`; a text with no leading id that mentions `SQ-10` logs task null (base: `SQ-10`).
- AC3: `from-message` with a `HANDIN SQ-10` record writes no event.
- AC4: `squad-spawn dev X --task integration --dry-run` prints `squad-task claim integration`; `--task SQ-10` exits 2.
- AC5: `squad-task-prompt` builds from `tasks/integration.md` (inline ` · Files:`) and from a ticket with `Aim:` and no `Duties:`; a ticket with no Duties anywhere exits 2.
- AC6: one test runs a table of ids through the python, jq and bash copies and they agree.
- AC7: the first commit holds ticket files 09-17 (each with `Duties:`, `Files:`, `Aim:`, `Estimate:`, `Depends on:`) and the three followups `wontfix` edits; its sha is sent to the Team Lead before code.

## Comments
