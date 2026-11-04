# 28 Tasks from the scope's definition
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: none (the Tasks panel keeps its table; one column is added, see Rules).
Status: ready-for-agent
Iteration: 2
Blocked by: none
Feature: 3, 7a (`tasks/features.md`, ticket 07); PO iteration 2, issue 4 (images 4, 5)

## What the PO gets
In squad `accounts`, scope `cswitch-bg`, the Tasks panel lists tasks 01 to 04 (it says "No tasks yet" today while Work time shows 01 to 04). Each row shows the original task: its title and the file where it lives, so he can find and follow it.

## Facts found (BA, read-only, 2026-11-04)
Squad `accounts`, scope `cswitch-bg`: `project.md` of the squad says tickets live in `$SCOPE_DIR/tasks/`. The real layout:
| What | Where |
|---|---|
| The task (original) | `.claude/squads/accounts/scopes/cswitch-bg/tasks/NN.md` (01, 02, 03, 04); first line `# NN <title>`; a `Status:` line (e.g. `done (Manager-confirmed; QA at the end)`, `handed in e8a7c5f, Manager-confirmed; QA at end`) |
| Evidence of a task | folder `tasks/NN/` (`evidence.md`) and `.scratch/cswitch-bg/issues/03-cautoswitch-stuck-pane/` (evidence, promote only; no ticket file) |
| Scope definition | `scope.md` of the scope (brief); no `tickets:` line in it |
| Plan table | none (`plan.md` absent) |
| Owner | `roster.md` row, Owns `ticket NN` |
Why the board shows 0: it only reads `.scratch/<slug>/issues/NN-*.md` (or a plan table). That folder has no ticket file, so no task row. The dashboard scope itself keeps its tickets in the same style as the repo rule (`.scratch/<feature>/issues/NN-<slug>.md`).

## Rules
- **Where tasks come from, in this order; the first source that has any task wins. No other source, no guessing by name or by messages.**
  1. The `tickets: <feature-slug>` line in `scope.md` → files `.scratch/<slug>/issues/NN-*.md`.
  2. Else `.scratch/<scope name>/issues/NN-*.md` (the committed tickets of the repo rule).
  3. Else the scope's own task files: `<scope folder>/tasks/NN.md` or `NN-*.md` (file name starts with the number), and `tasks/issues/NN-*.md` (drafts, as the dashboard scope keeps them before its Dev commits them).
  4. Else a task-id row in the scope's plan table (`plan.md`, `tasks/plan.md`, or the iteration plan the scope names): id from the first cell, title from the second.
- The old guess (the ticket folder with the most matching message tokens, `squadtickets.find_tickets` fallback) is removed. Report and board read the same one function, so they cannot disagree (T07.AC8 rule). A message token with no task (`REV-8`) is still not a task (T07.AC7).
- A row shows: the id, the **title** (the file's first `# ` line without the number; else the plan cell; else the file name), and **where it lives**: the path relative to the repo (e.g. `.claude/squads/accounts/scopes/cswitch-bg/tasks/01.md`). A plan-only row says "plan table, <file>". The path is a Columns-control column "Where" (default on, in Tasks) and a click opens the file (ticket 30).
- The ticket's `Status:` line is read by its first words; text after them is ignored. It never makes a new stage word; stage words stay those of ticket 07. The ledger (messages) still decides everything it decides today (merged, ready for review, sha changed, returned, checking).
| Status first words | Stage shown when the ledger says nothing else |
|---|---|
| `done` | done |
| `blocked` | blocked |
| `handed in` (e.g. `handed in e8a7c5f, Manager-confirmed; QA at end`) | checking as ticket 07 words it if a HANDIN is in the ledger; else in progress |
| `in progress` | in progress |
| `ready-for-agent`, `ready-for-human`, `needs-triage`, empty, any other | todo |
- Not task rows: a folder `NN-slug/` (evidence), the `issues-tech/` folder and its files, a file in `tasks/` whose name does not start with a number (e.g. `plugin-usage-context-drop.md`), `TEMPLATE.md`, `*.coach.md` / `*.summary.md`. A task is a regular file `NN.md` or `NN-<slug>.md`.
- If no source has any task: the panel says what it looked for: "No task files found. Looked in: <the folders it tried>." It never says that the Manager has not published tickets.
- Work time keeps listing tasks from its own data; the panel and Work time may differ only when a task has time but no definition. In that case the Tasks panel shows nothing extra (T07.AC7).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T28.AC1** Given squad `accounts`, scope `cswitch-bg` (real data, and the same case on the fixture), then the Tasks panel lists 4 rows 01 to 04, each with the title from its `# NN` line (e.g. 01 "Repro: what cswitch meets on a pane with background work"), and not "No tasks yet". Stage: 01 and 04 (Status `done…`) show "done" or "merged" when the ledger says merged; 02 and 03 (Status `handed in …`) follow the table above and the ledger; none shows "todo".
- **T28.AC2** Given those rows, then each shows "Where" as the repo-relative path of its file (`.claude/squads/accounts/scopes/cswitch-bg/tasks/0N.md`); a click on it opens the file (ticket 30 rule).
- **T28.AC3** Given a scope with `tickets: some-slug` and `.scratch/some-slug/issues/01-x.md`, then that folder is used even when the scope also has `tasks/` files (source 1 wins).
- **T28.AC4** Given a scope with no `tickets:` line, no ticket file in `.scratch/<scope>/issues`, and task files in its `tasks/` folder, then those list (source 3) and `.scratch/<other feature>/issues` of another scope is never used.
- **T28.AC5** Given a scope with no `tickets:` and both `.scratch/<scope>/issues/NN-*.md` and `tasks/` files, then the `.scratch` files list (source 2) and the `tasks/` files do not; given only a plan table, then rows list with "plan table, plan.md" as Where (source 4).
- **T28.AC6** Given tickets with Status `done (Manager-confirmed; QA at the end)`, `handed in e8a7c5f, …`, `ready-for-agent`, `blocked`, `in progress` and none, then each stage follows the table above (and a ledger word of ticket 07 wins where it applies).
- **T28.AC7** Given no source has a task, then the panel says "No task files found. Looked in: …" with the folders it tried, and the needs-you count is unchanged.
- **T28.AC8** Given a scope that has only a message token `REV-8` and no task, then no row (T07.AC7); given a folder of another scope that matches the task names, then it is not used.
- **T28.AC9** Given the report of the same scope (`squad-report`), then it lists the same tasks as the board (one shared function).
- **T28.AC10** Given the Columns control of Tasks, then "Where" is listed, checked by default, and can be hidden and moved like any column (T20.AC1-AC3); the Task column stays the identity column.
- **T28.AC12** Given `tickets: slug` in `scope.md` whose folder `.scratch/slug/issues` has no `NN-*.md` file, then the reader falls through to sources 2, 3 and 4 (not an empty panel).
- **T28.AC13** Given a scope that has evidence folders `NN-slug/`, an `issues-tech/` folder, `TEMPLATE.md` and a non-numbered file next to its tasks, then none of them is a row.
- **T28.AC14** Given scope `dashboard` (real data), then the Tasks panel lists tickets 01 to 30 from `tasks/issues` until they are committed, and from `.scratch/dashboard/issues` after (source 2).
- **T28.AC15** Given the scope picker row "tasks x of y" and the header count, then y equals the number of Tasks panel rows (the picker said 0 for the PO too).
- **T28.AC11** Given the same scope seen from a goal view, then each row also carries its Scope (T07.AC9) and the same Where.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Fixtures (QA blackbox X1)
In `tests/fixtures` or the fixture squad of ticket 02, three added scopes: (a) `accounts`-style: flat `tasks/01.md`..`04.md` with the four Status lines above, a `tasks/NN/` evidence folder, `TEMPLATE.md`, a non-numbered file, no `.scratch` ticket file; (b) `tickets: slug` whose folder has no `NN-*.md`; (c) only a plan table (`plan.md`) and no task files. Plus `issues-tech/` next to `issues/` in one of them.

## Touched files
Set by the Manager: `bin/squadtickets.py` (the one shared source rule), `bin/squadboard_tasks.py`, `bin/squadboard_list.py` if it keeps its own copy (its test keeps both equal), `templates/board/panel_tasks.js` (Where column, empty text); tests `tests/test_squadtickets.py`, `tests/test_squadboard_tasks.py`; a fixture for the `accounts`-style layout (flat `tasks/NN.md` + evidence folder). The report reader (`squadreport_tasks.py`) uses the shared function.

## Comments
- BA 2026-11-04: source order and "first source with tasks wins" are my reading of the PO's "take the tasks from the scope's definition; no old fallback". The PO's question "Jira, .scratch, or other" is answered by facts: for `accounts`/`cswitch-bg` they are in the scope folder, `tasks/NN.md`. No Jira reads (SAFE-2).
- Open for the Tech Lead: ticket 07 AC8 ("without `tickets:`, tasks still list") now means sources 2 to 4 (`.scratch/<scope>`, the scope's task files, the plan table); update its wording to point here.
