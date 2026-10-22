Status: ready-for-agent
Type: promotion
Task ID: 05
Touches: `docs/adr/0015-evidence-next-to-the-ticket.md` (new), `CONTEXT.md`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_history test_instructions`
Blocked by: 04 passed

# 05: promotion

**Done when `$SCOPE_DIR/promote.md` is committed into the project docs on the integration branch, with nothing the scope did not decide.** Follow the rule `project.md` names (the `/domain-modeling` skill's ADR and glossary format; ADR numbering continues from `0014`). Branch from 04's passed branch. The wording is in `promote.md`; do not invent more.

## Technical AC
1. ADR 0015 holds exactly the ADR text in `promote.md`; `CONTEXT.md` gets only the glossary entries in `promote.md` (Evidence folder, Evidence sha), in the Work section, in the file's existing format.
2. `git diff --stat` touches only the two files; test run quoted.
3. Evidence: this ticket's `evidence.md`.
