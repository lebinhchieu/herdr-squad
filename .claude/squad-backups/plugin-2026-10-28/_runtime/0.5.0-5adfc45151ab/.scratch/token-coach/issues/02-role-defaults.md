# 02 Model and effort defaults per role

Status: resolved
Blocked by: none

Add `model:` and `effort:` frontmatter to each `agents/*.md`, following the table in spec.md. Check whether the agent frontmatter supports `effort:`; if it doesn't, `squad-spawn` reads it and passes `--effort`.

## AC
- `squad-spawn --dry-run` for each role shows the model and effort from the table.

## Comments

- Added `model:` + `effort:` frontmatter to the 7 existing `agents/*.md` per the spec table (manager already had `model: opus`; got `effort: medium`).
- Checked: agent frontmatter does support `effort:` (low|medium|high|xhigh|max, per the sub-agents docs). I still read it in `bin/squad-spawn` (`fm()` helper) and pass `--model`/`--effort` explicitly, because the docs describe `effort:` for subagents and I could not confirm a top-level `--agent` session honours it. `--model`/`--effort` flags still override.
- Files: `agents/{manager,tech-lead,ba,team-lead,dev,qa-whitebox,qa-blackbox}.md`, `bin/squad-spawn`, `tests/test_squad_spawn.py`.
- Test: `python3 -B -m unittest tests.test_squad_spawn` → OK (all 7 roles + override).
- Note: those files already had unrelated uncommitted edits; I only added the two lines / the new block.
