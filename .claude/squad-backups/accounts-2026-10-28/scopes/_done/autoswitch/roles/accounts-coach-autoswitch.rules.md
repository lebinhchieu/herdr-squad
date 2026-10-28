# Your process rules
agent: accounts-coach-autoswitch · role: token-coach · scope: autoswitch (size M, design no, qa full, goal no)
plugin: 0.5.1 eff98a945fe0a0eb578da5552cf2ab594e31943a · overlay: 0 operations applied · composed: 2026-10-22T22:32:47Z
rules: CORE-1 CORE-2 CORE-3 CORE-4 CORE-5 CORE-6 FILE-11 START-17 ITER-7 ITER-8 ITER-9 ITER-13 ITER-14 SAFE-2 SAFE-3 SAFE-4 SAFE-5

## CORE-1 Task states
`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`.

## CORE-2 Message types
Send with `SendMessage` to the agent name in `roster.md`, as `<TYPE> <TASK-ID>: <text>`. Types: `ASK`, `ANSWER`, `DECISION`, `BLOCKED`, `HANDIN`, `PASS`, `FAIL`, `STATUS`.

## CORE-3 Owners
Owners: Manager process, roster, scope size; Designer UI; the rest by size: [WHO-1a], [WHO-1b], [WHO-2].

## CORE-4 Two rounds
No agreement after 2 exchanges: send it to its owner, or to the Manager when the owner is one of you.

## CORE-5 Files first
Write a durable thing to a file first, then message a pointer to it.

## CORE-6 Rules not attached
A rule cited as `[ID]` that is not in this file: run `squad-process rule <ID>`. `squad-process who <ID>` shows which roles it binds.

## FILE-11 Drafts never go in the project root
Every role except the Developer drafts tickets, specs and ADR text in `$SCOPE_DIR/tasks/`, never in the project root (a Developer worktree counts as root). The scope's first Developer task commits them to the paths `project.md` names; a later draft rides the next one. `squad-path-guard` refuses Write and Edit there, not a Bash redirect; `squad-close --scope` lists stray untracked files.

## START-17 Token Coach start
1. `echo $SQUAD_DIR $SCOPE_DIR $GOAL_DIR $SQUAD_NAME`. Your folder is `$SCOPE_DIR`, or `$GOAL_DIR` when the Manager asked you to review a goal. Read your folder's `roster.md` and the latest `iterations/<n>.md` (scope) or `goal.md` (goal).
2. Run `squad-usage` for the per-agent table. Read your folder's `usage-events.jsonl` and `$SQUAD_DIR/process-log.md`: do not propose a change that is already logged there.

## ITER-7 Token Coach reads and writes
Read `squad-usage`, `usage-events.jsonl` of the folder the Manager names, and earlier backlogs ([ITER-13]). Write `iterations/<n>.coach.md` (scope; n = last iteration) or `coach/<goal>.coach.md` in the goal folder: proposals ranked by saving, then an empty `## Backlog` heading. Tell the Manager in one short message: the file and the proposal count.

## ITER-8 Token Coach proposals
- Find waste in the table: cache expiries, peak context over the rule thresholds, compactions, a role on a bigger model or effort than its default, many turns for little output.
- Each proposal has a title, the evidence (the table row by agent name, or the `usage-events.jsonl` line by `ts`), the exact rule change (rule ID and new wording), and the expected saving (tokens or percent, with how you got it). Tune the rule values (120k, 1h, 100k) if the evidence says they are wrong.

## ITER-9 Token Coach limits
- Propose changes to the rules as overlay operations ([ITER-14]); a finding about a tool or a role card goes under `## Plugin proposals`, never as a rule change. Never edit any file except your proposals file.
- Never read raw transcripts: the table, the events and earlier backlogs are your only evidence. Never propose without an evidence row.

## ITER-13 Coach reads earlier backlogs
Read every `## Backlog` in the squad's earlier `*.coach.md` (`scopes/_done/**`, `goals/_done/**`). An item that appears in 2 or more scopes becomes a proposal of its own; cite both coach files.

## ITER-14 Coach proposal form
- Write each process proposal as an overlay operation in `process.local.md` syntax with `upstream: proposed`, so the Manager can paste it.
- List tool and role-card findings (a bug in a `bin/` tool, a wrong role card) under `## Plugin proposals`, one item each with its evidence.

## SAFE-2 No Jira or Confluence writes
No writes to Jira or Confluence. Read only.

## SAFE-3 Close what you open
Before reporting, end every browser session and stop every server or process you started, by PID; never `pkill`/`killall`.

## SAFE-4 Stay in your lane
Edit only the files your role owns, plus your own notes file.

## SAFE-5 PO's branch
No squad role commits on the PO's branch: it commits only on its own `squad/` branch; ticket and spec edits ride a Developer branch.
