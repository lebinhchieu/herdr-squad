# Task 03: away mode rule

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (the goal promotes in its last scope, goals/watchdog2/promote.md); full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag, user-visible change or business doubt: `BLOCKED <task>`.

Status: ready (build after 02 is handed in; same Developer, same worktree)
Source: `goals/watchdog2/goal.md` (answers of Chieu: away mode) and `shared/decisions.md`. Read the `templates/squad/process/` file that holds the Manager's escalation rules (`who.md`, `messages.md`) and how rules are written there ("Writing a rule" in the Manager card: one rule, stated once, who acts, when, limit, no history).
Files: one rule added in `templates/squad/process/` (the file where it fits best), and the rule tests/goldens that pin rule lists (`grep -rl` finds them). Do not edit `agents/*.md`.
Ticket: commit this file's content as `.scratch/watchdog2/issues/03-away-mode-rule.md` in your first commit.
Base: main (stack on task 02's branch if you need its `away` file name).

## AC
- AC1 One new rule, binds the Manager (and the Team Lead when on the team): while `<home>/away` exists, Chieu is away.
- AC2 While away: the Manager keeps going on every clear point. A question another role can settle is settled by its owner (advisor first, as LC-25), never waiting for Chieu. A question that only Chieu can settle and that does not block other tickets is parked (`squad-inbox park`), and the Manager works on the other tickets.
- AC3 Key decisions always wait for Chieu, nothing else does: the "Always goes to PO" items (irreversible choice, goal or scope change, deadline or budget overrun), a team change that needs his yes, and any merge, push or deploy. Each goes to the inbox with `--blocks` naming only the work it holds; all other work goes on.
- AC4 While away the Manager notes each decision it made for Chieu in the iteration file (one line: what, why). When `away` is deleted ("I am back"), it writes ONE inbox read item: decisions made, parked questions, key decisions waiting.
- AC5 The rule composes into the Manager's rules (`squad-process lint` clean, `squad-process rule <ID>` prints it). Rule-list tests and goldens updated, none skipped.
- AC6 Task 02's hook text names this rule id.

## Technical AC (QA whitebox, agreed with the Developer in this file)
- T1 The new rule has the same header form as its neighbours (`## <ID> <title>`, then `roles: manager, team-lead`, `when:` only if the neighbours in that file use it, `topic:`). The id follows the file's scheme and is not used anywhere else (`grep -rn '<ID>' templates/ agents/ bin/ tests/`). `python3 bin/squad-process lint` exits 0 before and after.
- T2 The rule obeys the Writing rule (`bin/processlint.py` clean): at most 60 words per bullet, each point states who acts, when and the limit, no history, no dates, no mention of Chieu by name (say "the PO"). One rule, stated once; the Always-goes-to-PO list is pointed at by id (`[WHO-1a]`, `[WHO-1b]`, ...) or by name, not copied.
- T3 The rule says where the switch is in one place: `<home>/away`, where home is the Manager's `$SCOPE_DIR`, else `$GOAL_DIR`. It says "exists" means present, not its content.
- T4 Each of AC2 to AC4 is a separate, testable statement: settle (owner, advisor first by `[LC-25]`), park (`squad-inbox park`, with the real flags: `--text`, `--blocks`), key decision (inbox item with `--blocks` naming only that work), note per decision in the iteration file (one line: what, why), and the ONE read item on "back". Every `squad-inbox` flag it names exists: run `squad-inbox park --help` and `squad-inbox add --help` (or the CLI's own usage) and compare.
- T5 No conflict with an existing rule: the rule does not weaken `[MRG-1]`, any "Always goes to PO" row, or the `[LC-25]` advisor step. Where an existing rule says "wait for the PO", the new rule narrows who decides only for the items AC2 lists. QA checks `grep -rn "PO" templates/squad/process/{who,messages,iterations}.md` for a contradiction.
- T6 `squad-process rule <ID>` prints the rule for the Manager, and for `team-lead` on a team that has one; it does not appear in the cards of other roles (`squad-process who <ID>` shows manager, team-lead only). Show both outputs in `evidence.md`.
- T7 Rule-list tests and goldens: run `grep -rl '<touched path>' tests/` and `grep -rl '<new ID>' tests/`, run every hit (rules contract, rules wording, rules view, processlint, any compose golden). A golden is regenerated only by its own tool and the diff is read; none is skipped or loosened.
- T8 AC6: the hook text in `bin/squad-away-hook` names the new id exactly as the rule's heading spells it, and `tests/test_away_hook.py` has one assertion that `additionalContext` contains that id, so a rename breaks a test. `squad-process rule <that id>` must succeed, checked by the test or `evidence.md`.
- T9 No edit to `agents/*.md`, README, `bin/squad-watchdog`, or the plugin version. `process-log.md` row for the process edit is the Manager's, not the Developer's.
- T10 Targeted tests only; no full suite without Chieu's yes. The task is built on task 02's branch (stacked), and `git merge-base --is-ancestor <02 sha> <03 sha>` is true.

## Design notes (Developer fills in)
- Pick the next free rule id by the scheme the file uses; check `squad-process lint` before and after.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace.
- Repo CLAUDE.md "Running tests": a diff touching `templates/` needs `grep -rl '<touched path or changed string>' tests/` and every hit run, goldens included.
- Do not bump the plugin version.
