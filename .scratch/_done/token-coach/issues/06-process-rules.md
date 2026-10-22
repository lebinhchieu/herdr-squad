# 06 Cost rules in process.md

Status: resolved
Blocked by: 04, 05

Add a short Cost rules section to `templates/squad/process.md` with the 5 rules from spec.md, and add the respawn step to each role's start-of-session text. Keep it short; one rule per line.

## Comments

- `templates/squad/process.md`: new `## Cost rules` section (before Safety), the 5 rules one per line, plus a files-table row for `usage-events.jsonl`.
- Added a numbered "Cost rules" start-of-session step (write notes, run `squad-respawn $SQUAD_NAME` when the hook fires) to `agents/{ba,dev,qa-blackbox,qa-whitebox,team-lead,tech-lead}.md`.
- **Manager skipped on purpose:** the hook exempts it (PO-facing session; `squad-respawn` of itself would drop the PO conversation). It applies rule 5 and the retro step (07).
- Rules 1 and 4 are judgment (the hook only detects 2 and 3); the section says so.
- Test: docs only; `python3 -B -m unittest discover -s tests` still OK. Files already had unrelated uncommitted edits; I only added lines.
