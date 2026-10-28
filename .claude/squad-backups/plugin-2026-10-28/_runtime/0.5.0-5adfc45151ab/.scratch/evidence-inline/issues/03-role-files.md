Status: ready-for-agent
Type: task
Task ID: 03
Touches: `agents/dev.md`, `agents/tech-lead.md`, `agents/qa-whitebox.md`, `agents/qa-blackbox.md`, `agents/manager.md`, `agents/team-lead.md`, `tests/test_instructions.py`
Does not touch: `templates/squad/process.md`, `bin/*`, `agents/ba.md`, `agents/designer.md`, `agents/token-coach.md`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_instructions test_process_writing test_process_citations test_pod_rules_process test_team_lead_role test_designer_handoff`
Blocked by: none

# 03: role files, screenshots inline

**Done when each role file tells its role where evidence goes and how a screenshot is shown, and a test pins it.**

## What (cite `process.md` rules by one clause; never copy their text; keep each file's existing structure)
- `agents/dev.md`: the S-size bullet "save behaviour evidence yourself in `dev-evidence.md`" becomes: write `## Behaviour` of the ticket's `evidence.md` (folder = ticket path with `.md` → `.evidence/`), save each screenshot in its `img/`, embed it as `![alt](img/<file>)` right under the AC it answers, commit it with the code. The `Design:` bullet: screenshots embedded the same way. Add one bullet "**Assemble the evidence.**" after the **After a `PASS`** bullet: once every checker passed, run `squad-evidence add <ticket> --heading "<H>" --from <review file>` for each review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, and send `HANDIN <task>: evidence sha <sha>` to the Tech Lead. The **Copy a report** bullet stays.
- `agents/tech-lead.md`: in S the `tl-review.md` stays in `$SCOPE_DIR/evidence/<task>/`; the check of the Developer's evidence now reads `evidence.md`, fails a screenshot that is not embedded (`squad-evidence check`), and on the `evidence sha` runs `squad-evidence check <folder> --base <passed sha>`. The design-screenshots line points at `evidence.md`.
- `agents/qa-whitebox.md`, `agents/qa-blackbox.md`: findings stay in `$SCOPE_DIR/evidence/<task>/qa-w.md` / `qa-b.md` (replace "the evidence place `project.md` names"); a screenshot is embedded in the review file with `![alt](path)` (absolute path or relative to the file); the Developer's `add` copies it. QA reads the ticket's `evidence.md` `## Behaviour` as the Developer's claim, not as proof (blackbox keeps its existing line).
- `agents/manager.md`: the check-in item lists, per ticket, the link to its `evidence.md` (a path in the repo or the Dev branch), not a folder; names the Dev branch and the evidence sha. `agents/team-lead.md`: the iteration summary's "evidence links" point at each ticket's `evidence.md`.
- `tests/test_instructions.py`: new tests that read the files: dev.md names `evidence.md`, `img/` and `squad-evidence add`; tech-lead.md names `squad-evidence check` and `--base`; qa-whitebox.md and qa-blackbox.md name `$SCOPE_DIR/evidence/` and embedding; no role file still says `dev-evidence.md`; the existing `test_dev_copies_reports_to_evidence_and_sends_a_diff_check_after_a_pass` still passes unchanged.

## Technical AC
1. The harness passes (quote the summary line). `grep -rn "dev-evidence" agents/` has no hit.
2. The `process.md` sections each file cites already exist (`test_process_citations`); no new section is cited.
3. Each edited bullet states who acts, when and the outcome; no sentence copies a `process.md` rule.
4. No change outside the Touches list; `git diff --stat` is in the evidence.
5. Evidence: `evidence.md` in this ticket's evidence folder (layout contract) with the grep and test outputs as fenced blocks.
