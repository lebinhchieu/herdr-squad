Status: ready-for-agent
Type: task
Task ID: 02
Touches: `templates/squad/process.md`, `templates/squad/project.md`, `skills/squad-init/SKILL.md`, `skills/squad-process-update/history/process-v6.md` (new, a copy of the template), `skills/squad-process-update/changelog.md` (new `## v6` block on top)
Does not touch: `.claude/squads/**` (git-ignored; the Manager updates the squad copy after merge), `agents/*`, `bin/*`, `tests/*` unless a test hard-codes the version (then update only that line)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_history test_processlint test_process_writing test_process_citations test_templates test_instructions test_squadprocess test_squadprocess_show test_squadprocess_apply` and `python3 bin/processlint.py templates/squad/process.md`
Blocked by: none

# 02: process v6, evidence next to the ticket

**Done when `process.md` states the evidence rule once, in the section that owns it, the template is `process-version: 6`, and the history guards pass.**

## What (wording is the Tech Lead's; the Developer may tighten it to pass `processlint`: bullets at most 60 words, one bold label of at most 15 words, no hedges, no dates)
1. **Files table** (`## Files are the truth, messages are the talk`): replace the `evidence/<task>/` row by two rows: `<ticket path minus .md>.evidence/` (Developer writes; `evidence.md` is the one file the PO reads, `img/` its screenshots) and `evidence/<task>/` (reviewers' working files `qa-w.md`, `qa-b.md`, `tl-review.md`, suite receipts; the PO never needs it).
2. **Task lifecycle**: replace the last bullet "Evidence goes where `project.md` says ..." with the rules, one per bullet:
   - Evidence lives next to the ticket in `evidence.md` (layout in `spec.md` of this scope: folder = ticket path with `.md` → `.evidence/`; for a project without ticket files, next to the `tasks/<id>.md` file). Screenshots are embedded as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.
   - The Developer writes `## Behaviour` and commits it with its code. After every checker passed, the Developer adds each reviewer file with `squad-evidence add` and commits; the Tech Lead checks that commit with `squad-evidence check --base <passed sha>`.
   - `qa-b.md` exists in M and L, `tl-review.md` in S.
3. **Safety → merge**: "that both checkers passed the sha" → also accept the evidence sha after it (a later sha whose diff to the passed sha touches only `*.evidence/` folders, as `squad-evidence check --base` shows). Edit the one bullet that owns the "Before:" check; elsewhere at most a pointer.
4. **Sizes / Done**: "evidence saved" stays; no new text.
5. **Suites bullet**: "Save a receipt in the evidence folder" → "in `$SCOPE_DIR/evidence/`" (receipts are not part of the ticket's file).
6. **Header table**, row "Developer, QA ...": "(QA: also the task's evidence folder)" → "(QA: also the task's `evidence.md`)".
7. `templates/squad/project.md` Evidence row: `next to the ticket: <ticket path minus .md>.evidence/ (reviewers' working files and receipts: $SCOPE_DIR/evidence/)`.
8. `skills/squad-init/SKILL.md` step 6: the "Commit the durable files only" list stays; add one clause that ticket evidence is part of the repo, not the squad folder. Step 2: no change unless it names the old default.
9. Snapshot `history/process-v6.md` = the template byte for byte; changelog `## v6 — 2026-10-19` block: one item per changed section with `sections:`, `change: rule`, one-line `why: PO wants evidence next to each ticket with screenshots shown in the markdown`, `old: snapshot`, `new: snapshot` (format of the v5 block).

## Technical AC
1. `tests/test_process_history.py` passes: version line 3 = 6, snapshots 1..6 without gaps, changelog blocks 2..6, v6 snapshot equals the template, every listed section exists in the snapshot.
2. `python3 bin/processlint.py templates/squad/process.md` exits 0 (quote the output).
3. `grep -n "evidence" templates/squad/process.md` shows no remaining sentence that says evidence goes to `$SCOPE_DIR/evidence/<task>/` as its home, no copied rule text (one rule, one place; elsewhere a pointer of one clause).
4. No change outside the Touches list; `git diff --stat` is in the evidence.
5. A squad made from the template is current and detection is silent (existing test). `squad-process plan` on a v5 copy of the template lists a v6 item whose sections are `clean` (run it on a throwaway squad dir; paste the output).
6. Evidence: `evidence.md` in this ticket's evidence folder (layout contract) with the command outputs above as fenced blocks.
