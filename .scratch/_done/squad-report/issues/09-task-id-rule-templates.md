Status: ready-for-agent
Type: task
Task ID: 09
Touches: `templates/squad/process.md` (one bullet + version line), `skills/squad-process-update/history/process-v5.md` (new snapshot), `skills/squad-process-update/changelog.md` (new `## v5` block), `templates/scope/roster.md`, `templates/goal/roster.md` (one sentence each), one test line in `tests/test_pod_rules_process.py` (or a new `tests/test_task_id_rule.py`)
Does not touch: this squad's live `process.md` (the Manager already has the line there, PO-approved E3), `agents/*.md`, any `squadreport*`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_history test_pod_rules_process test_process_writing test_processlint test_templates test_squadprocess test_squadprocess_apply`. Independent of 01-08.
Blocked by: none. Parallel with everything.

# 09: The Task ID rule in the plugin's templates (Q23, PO approved)

**Done when a squad made from the plugin gets the same Task ID rule this squad already runs on.** PO approved option (a) incl. Q23 (E3). Business AC10.1; spec → Technical → "Round-3 follow-ups" (about 40 tokens read once per role per session).

## What
1. `templates/squad/process.md`: bump line 3 to `process-version: 5` and add, in `## Messages` right after the "Point at files and lines..." bullet, **exactly** the bullet already in this squad's `process.md`: `- **Task ID:** every agent writes the ticket number \`NN\` alone as the task ID, never an alias, slug or prefix; a Developer's roster \`Owns\` reads \`ticket NN\`.` (copy by `grep -n 'Task ID' .claude/squads/plugin/process.md`; do not reword).
2. `skills/squad-process-update/history/process-v5.md` = the new template verbatim (the test requires equality); `changelog.md` gets a `## v5 — 2026-10-19` block (snapshot line; one item "Task ID is the ticket number": `sections: ## Messages`, `change: rule`, `why:` one line, `old: snapshot`, `new: snapshot`), in the format of the v4 block.
3. `templates/scope/roster.md` and `templates/goal/roster.md`: one sentence after the bold intro line: "A Developer's `Owns` reads `ticket NN`." Check `test_templates.py` for roster-template pins; if one fails for a good reason, change the pin in that test and say so.
4. Test: the template has the bullet; `process-v5.md` has it and `process-v4.md` does not.

## Technical AC
1. `test_process_history` green: snapshots 1..5 without gaps, changelog blocks 2..5, current snapshot == template, a squad made from the template is `current`.
2. `git diff templates/squad/process.md` is the version line plus one bullet (two changed hunks); the bullet is byte-identical to the live one (`diff <(grep 'Task ID' .claude/squads/plugin/process.md) <(grep 'Task ID' templates/squad/process.md)` empty, quoted).
3. `processlint`/writing tests pass (one rule per bullet, no new heading).
4. Migration note for the hand-in: a squad at v4 that keeps its own copy of this line shows a `local` (identical) section in `squad-process plan`; quote one `squad-process plan --json` run against a v4 squad copy that does and does not have the line. No data migration. Rollback = revert the commit.
5. Primary behaviour only (qa: light).
