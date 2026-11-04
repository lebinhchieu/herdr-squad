# 29 Files shows the .scratch dir and the squad dir
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: none (two more rows in the existing Files table; no new screen).
Status: ready-for-agent
Iteration: 2
Blocked by: none for the ticket rows; the PO's yes on the folder-row reading (open point O2, via the Manager) before the Dev builds the folder rows
Feature: 8 (`tasks/features.md`, ticket 14); PO iteration 2, request 1

## What the PO gets
In Files he sees the two places the squad writes to: the repo's `.scratch` folder and the squad's own folder, as rows he can open in VS Code (ticket 30). Today Files only lists some files, so he cannot get to the folders.

## Rules
- **BA reading of "show the .scratch dir and the squad dir"** (the PO may correct it): Files gets two **folder rows** at the top of its table, always shown, for every choice (goal or scope): (1) the repo `.scratch` folder; (2) the squad folder (`.claude/squads/<squad>`). These are the two roots the board is allowed to open (ticket 03 allow-list).
- A folder row has: name (`.scratch`; the squad folder's name), kind `folder`, what "folder", the full path, last changed (the folder's own change time, local zone). Folder rows are not counted in "files seen" or "truncated", and they are shown even when the list below is empty.
- The ticket files themselves are listed too (kind `ticket`): `.scratch/<slug>/issues/NN-*.md` and `.scratch/<slug>/spec.md` of the scope's ticket folder (ticket 28 source 1 or 2), and the scope's `tasks/NN.md` files when ticket 28 source 3 is the one used. Today only the ticket plan and evidence are listed, so the original tasks are not.
- Everything else in ticket 14 stays (the other kinds, ADRs not listed, the allow-list, the report rows).
- Folder rows are built only from the allow-list roots; a path outside it never gets a row (T14.AC3). Folder rows come first and keep their place when the PO changes the Columns control (the Files identity column stays File).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T29.AC1** Given any scope choice, then the Files table starts with two rows whose File text is exactly `.scratch` and `.claude/squads/<squad>` (e.g. `.claude/squads/board`), each with kind "folder", the full path as tooltip, and a last-changed time in the local zone equal to the folder's own change time.
- **T29.AC2** Given a goal choice, then the same two folder rows show.
- **T29.AC3** Given a scope with no files at all, then the two folder rows still show (not "empty").
- **T29.AC4** Given the scope `cswitch-bg` of squad `accounts`, then Files lists `tasks/01.md` to `tasks/04.md` with kind "ticket"; given a scope with `.scratch/<slug>/issues/NN-*.md`, then those files list with kind "ticket".
- **T29.AC5** Given a ticket folder of another scope, then its files are not listed.
- **T29.AC6** Given the two folder rows, then the paths are the real folders (no `..`, no symlink target outside); given a squad with no `.scratch` folder in its repo, then that row is not shown and nothing fails.
- **T29.AC7** Given the Columns control of Files, then hiding every column except File keeps the folder rows (shown by their name) and the other rows.
- **T29.AC9** Given `.scratch/<slug>/spec.md` of the scope's ticket folder, then it is listed with kind "ticket"; given a file that is both a ticket and in the old list (e.g. `tasks/NN.md` and ticket plan), then it is listed once.
- **T29.AC10** Given the Files panel's file count (the visible text, if the panel shows one), then it counts files only: the two folder rows are not in it.
- **T29.AC8** Given the existing Files AC T14.AC1, AC3, AC4, AC5, then they still hold.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Fixtures
The fixtures of ticket 28 (accounts-style scope with flat `tasks/NN.md`; a scope with `.scratch/<slug>/issues/NN-*.md` and a `spec.md`), and a squad whose repo has no `.scratch` folder.

## Touched files
Set by the Manager: `bin/squadboard_files.py` (folder rows, ticket kind rows; it reads the ticket folder through `squadtickets` — ticket 28 changes that function, so 28 and 29 are checked together); tests `tests/test_squadboard_files.py`.

## Comments
- BA 2026-11-04: other reading, if the PO meant "list every file inside these folders": it breaks ticket 14 (ADRs, logs, locks not listed) and can pass 500 rows. I chose the two folder rows + tickets. Open point O2: the Manager gets the PO's yes (or his other reading) before the Dev builds the folder rows; QA blackbox fails the folder rows if the PO meant the other reading.
