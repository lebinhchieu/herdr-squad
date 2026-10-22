# T8 · suite rules: the Tech Lead runs the full suite, once
Status: ready-for-agent
Type: task
Blocked by: T1 and T4 (both passed). Branch from T1's whitebox-passed sha, then `git merge` T4's passed commit into your branch (T1 owns `process.md`, its v4 snapshot and changelog block; T4 owns the `agents/` edits you extend). Parallel with T3 (no shared file).
Repo: /home/chieule/workspace/squad
Spec: PO note in `$SCOPE_DIR/scope.md` → Notes from the PO · Design: ../design.md decision 14 · Technical AC: QA-W adds AC-9 (see below)

## Files this task touches (and no others)
`templates/squad/process.md`, `skills/squad-process-update/history/process-v4.md` (stays a byte copy of the template), the existing `## v4` block of `skills/squad-process-update/changelog.md` (add the changed sections; no `## v5`: v4 is not released), `CLAUDE.md` (Running tests), `tests/test_suite_rules_process.py` (new). Also `agents/dev.md` and `agents/tech-lead.md` (after T4's merge; touch only the suite lines below).

## Do
1. **Safety → replace the `Long suites` bullet** (and its two sub-bullets) with a `Suites` bullet and sub-bullets. Each at most 60 words; processlint clean. Content, in your own tight wording:
   - Developers and QAs run only the test files their diff touches. They never run the full suite, and two suite runs never overlap.
   - The Tech Lead decides when the full suite runs and runs it: once for a batch of tasks, or at the end of the scope or iteration. A scope goes to the PO only with a passing run (`--tz` where `project.md` names it) on its integration sha.
   - How: in the background, wait for its completion notice (never `pgrep -f` or `pkill -f`), commit every fix first, never restart a run; receipt in the evidence folder, first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the OK line.
   - A failing run: the Tech Lead names the task whose files fail; it returns to its Developer and counts as a return.
   - QA reads the Tech Lead's receipt when one covers the sha (same sha, clean, OK); with none it checks targeted tests and the diff. It never runs the suite.
   - Keep the sentence that `project.md` may name the runner. Keep the rule "Close what you open" untouched.
2. **Two other lines** that say who runs the suite: `Inside a goal` integration bullet ("runs the full suite and hands in" → runs the targeted tests and hands in; the Tech Lead then runs the full suite) and the `QA mode` `light` line ("QA runs the suite" → "QA runs the targeted tests"; "a failing suite" → "a failing test"). Grep the template for any other "full suite"/"suite" wording and make it agree; change nothing else.
3. **`CLAUDE.md` → Running tests:** the runner line stays. Replace "wait as in the Suites bullet of `agents/dev.md`" with a pointer to `process.md` → Safety → Suites. Add one line first: only the Tech Lead runs the full suite; everyone else runs the files they touched. Change no other line there.
4. **Snapshot and changelog:** copy the template to `history/process-v4.md` again; add the Safety, Inside a goal and Task lifecycle (QA mode) sections to the existing v4 block (format of the other items). `tests/test_process_history.py` and `tests/test_squadprocess*.py` stay green.
5. **`tests/test_suite_rules_process.py` (new)**, reads the template: the `Suites` bullet exists and `Long suites` does not; the Tech Lead runs it; Developers and QAs never; no overlap; the batch / end-of-scope-or-iteration timing; the receipt first-line format; the integration bullet and QA `light` line no longer make a Developer or QA run the suite; `CLAUDE.md` points at `process.md` → Safety → Suites and not at `agents/dev.md`.
6. **`agents/dev.md`:** replace the `Suites` bullet with: run only the test files you touched, never the full suite, never two suite runs at once (`process.md` → Safety → Suites); drop the background/wait/receipt text. `Special tasks`: the integration task merges, runs the targeted tests for the changed files and hands in; the Tech Lead runs the full suite after. **`agents/tech-lead.md`:** the `Plan the integration task` bullet drops "runs the full suite" for the same reason; add one short duty bullet: you decide when the full suite runs (once for a batch of tasks, or at the end of the scope or iteration), you run it and save the receipt, and a failure names the task that returns (`process.md` → Safety → Suites). `tests/test_pod_contact_routes.py` (T4) must stay green; add no Manager line.
7. No heading added, renamed or removed. `python3 bin/processlint.py templates/squad/process.md` exits 0. Run only the test files you touched (`tests/test_process_*`, `tests/test_suite_rules_process.py`, `tests/test_squadprocess*`, `tests/test_process_history.py`); never the full suite.

## Technical AC (QA-W to confirm as AC-9)
- The old rule and its three wording homes (`process.md` Safety, `agents/dev.md` Suites bullet, `CLAUDE.md` pointer, `agents/tech-lead.md` integration bullet) agree: grep `full suite`, `Suites`, `receipt` over `templates agents CLAUDE.md` and list the lines in `dev-evidence.md`. No file tells a Developer or QA to run the full suite.
- Test and process-text changes only; no change to `tests/run_suite.py`.

## Business AC
PO note 2026-10-17 (scope.md): Developers and QAs never run the full suite or run it in parallel; the Tech Lead decides when; the rules live in `process.md`.
