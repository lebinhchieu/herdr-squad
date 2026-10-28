Status: done
Blocked by: Part A none; Part B: the PO's approval of the `agents/` edit (check-in)
Task ID: RB-05
Files touched: `templates/squad/process.md`, `skills/squad-process-update/history/process-v3.md` (new), `skills/squad-process-update/changelog.md`; Part B only after approval: `agents/manager.md`

# RB-05: Process template v3 and the one board example in the Manager's file

**Done when the template no longer says the Manager reads a board and a squad can take the change through `/squad:squad-process-update`.** Requirement: `spec.md` R-13, R-14, R-15. ADR 0005 applies: every template change bumps the version.

## Part A: process v3 (ready for a Developer)
1. `templates/squad/process.md` line 3 `process-version: 3`; the Messages bullet becomes exactly: `- The Manager never pushes `STATUS`: it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity.` No other line changes. (The Manager's pane view is herdr's, not the board's recorder, so "pane activity" stays; no test pins this sentence.)
2. `skills/squad-process-update/history/process-v3.md` = byte copy of the new template (`test_current_snapshot_is_the_template`). **`process-v1.md` and `process-v2.md` are not edited** (BA R2: they let a squad's own edits be told from the plugin's text).
3. `changelog.md`: a `## v3 — <date>` block, one item, title `Board removed`, `sections: ## Messages`, `change: reword`, `why: the squad board is removed, so the Manager no longer reads it`, `old:`/`new:` as the file's fenced text format for the two sentences (copy the shape of the v2 items; `test_process_history` parses it).
4. The squad's own `$SQUAD_DIR/process.md` is **not** edited by anyone in this scope: the PO runs `/squad:squad-process-update`.

## Part B: `agents/manager.md` (role instruction: do not edit until the Manager writes `Approved by PO: <date>` under Comments)
5. Line 59 example `TAB-04 board labels` becomes `TAB-04 tab labels`. One phrase, nothing else in the file. (Ticket TAB-04's real title is "board labels" in `.scratch/squad-tabs/issues/04-board-labels.md`; that file stays history.)

## Technical AC
1. `python3 -m unittest test_process_history test_templates test_processlint test_process_writing test_process_citations test_squadprocess test_squadprocess_apply test_squadprocess_show test_instructions` (from `tests/`) green; `bin/squad-process check` on a scratch squad built from the v2 snapshot prints the update message and changes no file (R-14).
2. `git grep -inw board templates agents skills/squad-process-update/changelog.md` shows only the changelog's v3 block: its title "Board removed", its `why:` line and the `old:` text (and `agents/manager.md` nothing after Part B).
3. Diff: template one line + version line; snapshot v3 is a new file; changelog adds one block; no `history/process-v[12].md` line changes (`git diff --stat` proves it).
4. `processlint` (the writing rule of ADR 0006) passes on the template.
- Receipt hygiene: run targeted tests with `PYTHONDONTWRITEBYTECODE=1`; `rm -rf bin/__pycache__` (gitignored, so `clean=yes` misses it; `test_no_pyc` fails on it) before the receipt run; `dev-evidence.md` quotes the receipt's real tail.

## Comments

Approved by PO: 2026-10-16 (inbox E1: "(a) approve: TAB-04 board labels → TAB-04 tab labels")
