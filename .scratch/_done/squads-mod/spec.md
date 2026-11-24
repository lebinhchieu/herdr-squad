# Spec: /squads pane (squads-mod)

Status: final business AC (BA), 2026-11-12; all open points answered by Chieu. Target path: `.scratch/squads-mod/spec.md` (the scope's first Developer task commits it, FILE-11).
AC agreement with QA blackbox: AGREED 2026-11-12 (REV-8). Review in `tasks/qa-b-ac-review.md` (A1-A6, B1-B10, C1 applied); two last wording notes (AC2.4 "has tasks", rule 5 "tasks_total > 0") folded in.

## Need
Chieu runs several squads, goals and scopes. He wants to open one pane and see, for each one: does it wait on me, is it stuck, what do I do next. Then he wants the exact command for that thing, without remembering names and flags.

The pane is an **index and launcher**. It is not a second board. Detail of tasks, time and messages stays in `squad-board`; questions stay in the PO inbox pane.

## Scope
In: `/squads` mod pane; tree squads > goals > scopes of the active repo; name plus five facts and one "next step" line per row; a detail view with every command for the picked item and when each applies.
Out: task lists, time, cost, transcripts (board); answering questions (inbox pane); other repos; editing any squad file.

"Active repo" = the main repo root of the Claude Code session (a session inside a Developer worktree still sees the squads). Only `<git root>/.claude/squads/*` is read. Other repos are never scanned (same as `squad-board`).

## Row facts (reused, not invented)
The pane uses the facts of `bin/squadboard_list.py` (`scope_row`, `_goal_row`) with the **same definitions**: the board's six minus `new`, so five facts (needs you, stuck, tasks, last active, agents working) plus the name, so the board and the pane never disagree. "Next step" is derived from them. A goal row is the sum of its scopes. Sort: needs you (most first), then stuck (most first), then last active (newest first).

**Squad row:** name and one number, needs you (sum over its open scopes), plus how many open scopes it has. It folds and unfolds. At narrow width the name and needs you stay.

**Title:** "N need you", N = the sum of open questions over all open scopes (questions, not rows; goals are not counted twice). With N = 0 the title shows no number.

| Rank | Fact | Meaning (board definition) | Narrow width |
|---|---|---|---|
| 1 | name + kind | goal, scope, "no goal" for a lone scope | always |
| 2 | needs you N | open questions + unread items in the home's inbox files | always when N > 0 |
| 3 | next step | one short phrase, table below | always |
| 4 | stuck N | tasks with an open BLOCKED, or returned and not all PASS | when N > 0 |
| 5 | tasks x of y | tasks done (merged) of all tasks | width allows |
| 6 | last active | newest message, commit or file time | width allows |
| 7 | agents working | roster agents working now (herdr) | width allows |

`new` (N new since I last looked) is **not in iteration 1**. The board keeps the last-seen time in the browser; a terminal pane has no such place, and a new store is a new decision. A fact that cannot be read shows `?`, never 0 (the board's `unknown`).

## Next step (new term; glossary gap for PROMO-3a)
One phrase per row. First rule that matches wins. Rules read only the five facts. Rule 1 fires only when a fact that drives the rules (needs you, agents working) cannot be read. An unreadable task list shows tasks as `?` and falls to rule 6 "No tasks yet" (else every scope without ticket files would say "Cannot read"). Computed in Python (`squadtree.next_step`), one test per rule.

| # | Row | When | Next step shown | Command offered first |
|---|---|---|---|---|
| 1 | open scope or goal | needs you or agents working is `?` | "Cannot read <inbox or herdr>: open board" | board |
| 2 | open | needs you > 0 | "Answer N question(s)" (goal: "in <scope>") | inbox (list open) |
| 3 | open | stuck > 0 | "N task(s) stuck" | board |
| 4 | open | tasks_total > 0 and done = total | "All tasks done: close" | close `--dry-run` |
| 5 | open | tasks_total > 0 and agents working = 0 and done < total | "Nobody working: resume" | resume |
| 6 | open | tasks_total = 0 or `?` | "No tasks yet" (even when agents are working) | board |
| 7 | open | agents working > 0 | "Working. Nothing for you." | board |
| 8 | goal | no open scope left | "All scopes closed: close goal" | close goal `--dry-run` |
| 9 | done (closed) | always | "Closed. Read the report." | report |

Rule 8 applies to a goal before 2 to 7 only when it has no open scope. `squad-close` itself refuses a goal without a `promoted:` line or with an open scope; the pane shows the command and never hides that refusal.

## Commands table (one source)
One table in code lists every command; a new command is added in one place. The detail view filters it by the picked item. Columns: name, template, who normally runs it, changes state (read / writes / destructive), applies to, applies when.

| Command | Template | Runs it | Changes | Applies to | Applies when |
|---|---|---|---|---|---|
| Resume | `squad-start --resume NAME` | Chieu | starts a Manager tab | open lone scope, open goal | no agent is working (agents working = 0); else "Not yet: agents are working". A scope in a goal shows the **goal's** name (squad-start refuses the scope name). |
| Board | `squad-board --squad S --goal G` or `--scope X` | Chieu | read, keeps running: stop with Ctrl-C | any goal or scope, open or done | always. |
| Report | `squad-report NAME --squad S` | Chieu | writes report files | any goal or scope | always shown (best at check-in or after close) |
| Report status | `squad-report status NAME` | Chieu | read | any scope, open or done (not goals) | tells fresh, stale or missing |
| Inbox list | `squad-inbox --home DIR list --open --no-write` | Chieu | read | open scope or goal | needs you > 0; else "Not yet: no open questions" |
| New work | `squad-start "<text>" --squad S` / `--in-goal G --name N` | Chieu | starts a Manager tab | squad (lone scope or goal); goal (new scope) | text needed: the copy has a placeholder. On a flat squad: "Not yet: flat layout: squad-start refuses it". |
| Close scope | `squad-close S --scope X [--dry-run]` | Chieu | destructive | open scope | all tasks done; retro filled (the CLI refuses otherwise) |
| Close goal | `squad-close S --goal G [--dry-run]` | Chieu | destructive | open goal | no open scope; `promoted:` set |
| Close squad | `squad-close S` | Chieu | destructive | squad | work finished; shown with a warning (retires every agent, archives the squad) |
| Watchdog status | `squad-watchdog status --home DIR` | Chieu | read | open scope or goal | always |
| Sleep when idle | `squad-watchdog sleep on\|off --home DIR` | Chieu | writes a switch | open scope or goal | always shown (use when leaving the machine) |
| Retire Manager | `squad-retire <squad>-mgr-<name>` | Chieu | destructive | closed lone scope or closed goal | after close (the Manager stays alive) |
| Role commands | `squad-spawn`, `squad-respawn`, `squad-team`, `squad-usage`, `squad-task`, `squad-merge-check`, `squad-review-pack`, `squad-label`, `squad-evidence`, `squad-process` | Manager, Team Lead, roles | varies | open scope | listed in a closed group "Run by the team": shown for completeness, with who runs them |

Chieu asked that **all commands** show; the last row keeps them visible without crowding his own commands. Each entry has a one-line "when it applies" in plain words. A command that does not apply to the item's kind is hidden. A command that applies to the kind but whose condition is false now stays visible with "Not yet: <reason>": Resume (agents working), Close scope (tasks open), Close goal (a scope is open), Inbox list (no open questions). Board, Report, Report status, Watchdog status and Sleep are always shown without a reason.

## Safety rule
**Chieu chose copy only (2026-11-12).** No command is ever run by a click, read-only or not. A click copies the full command text and shows "copied". The pane runs nothing and shows no command output. `--force` is never offered on any command.

## Edge states
- No squads in the repo: "No squads here." plus how to start one (`/squad:squad-init`).
- Flat (legacy) squad: the squad row shows "flat squad: not supported" and no children (as the board, ADR 0004). Picking it shows Close squad (ready) and New work as "Not yet: flat layout: squad-start refuses it".
- Several squads: all listed, each with its goals and scopes.
- Done items (`scopes/_done`, `goals/_done`): in a closed group "Done" under their squad (a done scope of an open goal stays under that goal, marked done), newest close first. A done row shows name, brief, closed date and next step only (no facts: keeps the pane cheap); a done scope of an open goal still counts in the goal's tasks. Done items offer Board and Report; a done scope also offers Report status; a closed lone scope or goal also offers Retire Manager.
- A folder name that is not a safe name (a space, `;`, `$(`, `../` and the like) gets no commands. Control characters and colour codes in a name or brief never reach the screen.
- Data refresh: the Refresh control and a timed update (10 s) re-read the data with one read-only data command. The list position and folds are kept.
- Narrow pane (6 body rows at 24 terminal rows, per the po-inbox-tui audit): rows follow the rank column above; lower ranks drop first; a `↓ N more` hint shows rows below. Height comes from the host, never a constant (ADR 0007 line).
- The pane reads and writes no squad file; data comes from the existing readers (Tech Lead decides the seam).

## User stories and business AC
1. **See what needs me.** As Chieu, I see every squad, goal and scope of the repo, sorted by what needs me, so I know where to go first.
   - AC1.1 Given a repo with squad P (goal G with scopes A, B; lone scope C), when I open `/squads`, then I see P, G, A, B, C with A and B under G and C under a "no goal (N)" group of P (a group row for lone scopes, not a tag on each row).
   - AC1.2 Given A has 2 open questions and B has none, when the list shows, then G shows needs you 2, A shows 2, and A sorts above B.
   - AC1.3 Given a scope with no ticket files (tasks `?`), then that row still lists and says "No tasks yet", also when agents are working. Given inbox or herdr cannot be read, then it says "Cannot read ...: open board".
   - AC1.4 Given the same squad and the same moment, after a refresh, then every number on an open row equals the number the board's goal and scope list shows for that row. A small difference right after a state change is not a defect; a refresh makes them equal. (Done rows show no facts.)
   - AC1.5 Given A has 2 open questions and C has 1, then the title says "3 need you". Given none, then the title shows no number.
   - AC1.6 Given two rows with equal needs you, then the one with more stuck is first; with equal stuck too, the one active more recently is first.
   - AC1.7 Given I open `/squads`, then each squad is a row (name, needs you total, open scopes); it folds and unfolds; picking it shows New work and Close squad, with a warning on Close squad.
2. **Know the next step.** As Chieu, each row says what I do next.
   - AC2.1 Given the next step table, when a row has needs you 1, then it says "Answer 1 question(s)" even if stuck is also > 0.
   - AC2.2 Given all tasks of a scope are done, then its row says "All tasks done: close".
   - AC2.3 Given a scope is closed, then its row says "Closed. Read the report."
   - AC2.4 Given a scope with tasks, agents working and nothing waiting, then it says "Working. Nothing for you."
3. **See all commands for a goal or scope.** As Chieu, I pick a row and see its commands and when each applies.
   - AC3.1 Given I pick an open lone scope, then I see Resume, Board, Report, Inbox list, Close scope, Watchdog status, Sleep when idle with a "when it applies" line each, and "Run by the team" closed. The detail header shows the item's next step and facts, the same numbers as the list.
   - AC3.2 Given I pick a scope inside a goal, then Resume shows the goal's name.
   - AC3.3 Given I pick a closed lone scope or closed goal, then I see Board, Report and Retire Manager; a closed scope also shows Report status. Given a closed scope of an open goal, then Board, Report and Report status only (the goal's Manager stays).
   - AC3.4 Given not all tasks are done, then Close scope stays visible with "Not yet: tasks open".
   - AC3.6 Given agents working > 0, then Resume shows "Not yet: agents are working"; given agents working = 0, Resume shows with no reason. Given needs you = 0, Inbox list shows "Not yet: no open questions". Board, Report, Watchdog status and Sleep when idle always show with no reason.
   - AC3.7 Given the Board command, then its entry says "keeps running: stop with Ctrl-C".
   - AC3.5 Given a new command is added to the commands table, then it shows in the detail views it applies to with no other change.
4. **A goal shows its scopes.** As Chieu, picking a goal lists its scopes with the same facts.
   - AC4.1 Given goal G with 3 scopes, when I pick G, then I see 3 scope rows and G's commands (Resume, Board, New scope, Close goal).
   - AC4.2 Given a goal has an open scope, then its Close goal row says "Not yet: scope A is open".
5. **Commands are safe.** As Chieu, I never change state by a stray click.
   - AC5.1 Given any command of any item (read-only ones too), when I click it, then nothing runs: the full command text is copied and the footer says "copied". Given the copy does not work (no clipboard), then the full text stays on screen and the footer says the copy failed, not "copied".
   - AC5.2 Given the command needs a value (New work text), then the copy contains a clear placeholder.
   - AC5.3 Given I paste a copied command into a terminal, then it is complete and correct for that item: squad name, goal or scope name (a scope in a goal: the goal's name for Resume; Retire Manager: `<squad>-mgr-<name>`) and home folder are filled in, and the command runs or refuses as the table says (Close with `--dry-run`).
   - AC5.5 Given a scope folder whose name has a space, `;`, `$(` or `../`, then the row still lists, no command is offered for it, and the detail says "Name not safe for a command: rename the folder". Given a name or brief with control characters or colour codes, then the screen shows plain text only.
   - AC5.4 Given I press an item or a command row, then no process starts and no squad file changes (check with `git status` and the process list). The pane's own data refresh (the Refresh control and the timed update) runs the read-only data command and is not a press on a command.
6. **Edge states.**
   - AC6.1 Given no squads, then "No squads here." and the start hint show.
   - AC6.2 Given a flat squad, then it shows "flat squad: not supported", no rows under it, and picking it shows Close squad (ready) and New work as "Not yet: flat layout: squad-start refuses it".
   - AC6.3 Given 30 rows and a pane of 6 body rows, then needs-you rows come first and `↓ N more` shows the rest.
   - AC6.4 Given the pane is narrow, then name, needs you and next step stay visible; lower ranks drop first.
   - AC6.5 Given done items exist, then they sit in a closed "Done" group, newest close first; a done row shows name, brief, closed date and "Closed. Read the report." and no facts; a done scope of an open goal stays under that goal marked done and still counts in the goal's tasks.
   - AC6.7 Given two squads in one repo, then both are listed with their goals and scopes. Squads of other repos are never listed.
   - AC6.8 Given the session started inside a Developer worktree, then the main repo's squads are listed.
   - AC6.9 Given I type `/` and a text, then rows are filtered by name, and "no match" shows when nothing fits.
   - AC6.10 Given I pick a row and press Esc in its detail, then I return to the same row of the list, with the same folds.
7. **Read only.** As Chieu, opening the pane changes no squad file.
   - AC7.1 Given any state, when I open, pick and leave, then `git status` and the squad folder show no new or changed file.
8. **Fresh and sound data.** As Chieu, the pane shows the current state and tells me when it cannot.
   - AC8.1 Given a question is answered on disk (or a task state changes), when the pane refreshes (control or the 10 s update), then the row shows the new number, and list position and folds are kept.
   - AC8.2 Given the refresh fails, then the last good list stays, an error shows with "Try again" and says nothing was changed.
   - AC8.3 Given the first read is not done, then "Reading .claude/squads ..." shows.
   - AC8.4 Given this repo's real squads (3 squads, 25 scopes), then the pane opens and lists them without error within 3 seconds.

## Open points for Chieu (all answered 2026-11-12)
1. **ADR conflict.** ADR 0007 says "no cross-home view (`squad-board` stays the cross-home view)" and ADR 0020 says the board shows one goal or scope and "no cross-squad view". `/squads` lists many homes in one pane. **Answered by Chieu (E2 a): yes, allow it.** The pane is a list only: facts and commands, no task or message detail, no writes, one repo; detail stays in the board. It needs a new ADR (amends the two lines). The new ADR (draft `tasks/adr-0026-draft.md`) records it. Nothing blocks now.
2. **Click: copy or run.** Answered by Chieu: copy only. No run.
3. **`new` since last look is cut for iteration 1** (no place to keep the last-seen time in a terminal). Answered by Chieu: stays cut; revisit when he asks.

## Glossary gaps for promotion (PROMO-3a)
- **Next step**: the one phrase on a `/squads` row, from the five row facts by fixed rules. Not a task state.
- **Commands table**: the single list of squad commands with who runs each, what it changes and when it applies.
