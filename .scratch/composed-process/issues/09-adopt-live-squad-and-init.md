Status: ready-for-agent
Type: task
Task ID: 09
Touches: `bin/squadadopt.py` (new), `bin/squad-process` (add `adopt`), `skills/squad-init/SKILL.md`, `skills/squad-process-update/SKILL.md` (old-squad path), `tests/test_squadadopt.py` (new), `tests/fixtures/upgrade/` (adds the live squad overlay), `bin/squadprocess.py` (retire `show` and the role map once nothing calls them), `tests/test_squadprocess_show.py` (retired with it)
Does not touch: the live squad folder `.claude/squads/plugin/` (the PO-confirmed run is a deploy step, below)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadadopt test_squadupgrade test_squad_start test_windows_safe`
Blocked by: 06, 07, 08

# 09: Adopt existing squads; new squads start composed

**Done when `squad-process adopt --squad-dir <dir> [--dry-run]` turns a squad's `process.md` copy and full settings files into an overlay, a pin and local settings, and `squad-init` creates new squads that way.**

## What
- **`adopt`:**
  - diffs the squad's `process.md` against `history/process-v<its version>.md`;
  - maps each local change to a rule ID through 03's `mapping.md` and writes `replace`, `add` or `remove` operations with `upstream: proposed`;
  - lists anything it cannot map for the PO, writes nothing until each is resolved with `--resolve`, and never guesses;
  - archives `process.md` as `process.v<N>-archived.md`;
  - writes `plugin.pin`;
  - turns each `settings/<role>.json` into `<role>.local.json` holding only its difference from the template, with `codePaths` extracted.
- **`squad-init`:** creates `process.local.md` (empty, with a header), `plugin.pin`, `settings/*.local.json` and `project.md`. It never copies `process.md` or full settings.
- **Retire:** `squad-process show` and `ROLE_SECTIONS` once no command or card calls them; the old `apply` stays behind `--legacy` for squads that have not adopted.

## Technical AC
1. A dry run on a copy of `.claude/squads/plugin/` is recorded in the evidence. Because 03 shipped the live Coach rules, the expected result is an overlay with few or no operations; every leftover is listed. The produced overlay is copied to `tests/fixtures/upgrade/live-squad.local.md` for 07's CI test.
2. A fixture squad with one local edit, one deleted bullet and one unmappable paragraph produces two operations and one PO item; nothing is written without `--resolve` for that item.
3. The archive file exists and `process.md` is gone after a non-dry run on a fixture.
4. A fixture `squad-init` run produces no `process.md` and a valid `squad-process lint --squad-dir`.

## Deploy step (PO, after merge)
The squad folder is git-ignored, so after the merge the Manager runs `squad-process adopt --squad-dir .claude/squads/plugin --dry-run`. It shows the output to the PO as one inbox item and runs it for real on the PO's yes. Open scopes keep running on their old path until they close.
