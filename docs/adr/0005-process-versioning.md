# `process.md` carries a version, and a squad updates it per section

Status: accepted (refine-process)

Superseded by 0016 once accepted (composed-process): squads keep an overlay, not a copy; the per-section update is retired.

**Decision:** `process.md` carries an integer `process-version:` line; the plugin ships `skills/squad-process-update/changelog.md` and `history/process-v<N>.md`, a pristine copy of each version, so a squad's own edits can be told from the plugin's text.

**Why:** the squad's `process.md` is edited by its Managers and drifts from the template; a blind merge or a replace loses rules or edits.

**Consequences:**
- Every change to the template bumps the number, adds a snapshot and a changelog item (a test pins the template to the latest snapshot).
- The update is per section, whole-or-nothing, and needs the PO's yes; detection is a warning only (`squad-start`, and the Manager's first prompt through `squad-spawn`); older flat layouts are out of scope (use `squad-migrate`).
- Nothing in a squad's `process.md` changes until the PO has confirmed the whole combined result (the plugin's changes plus the squad's own edits). Local edits survive unless the PO picks the plugin's wording in a conflict. If the PO declines, nothing is written.
- The Developer, QA whitebox, QA blackbox and Designer read a section view, `squad-process show <role>`, from the same one `process.md`; every other role reads the whole file. The role map is a constant in `bin/squadprocess.py`, pinned by a test to the template's role table; a squad's local edit of that table is not followed. The file is not split and the version is not bumped.
- A squad without a version line is version 1. A squad with a flat layout is refused and sent to `squad-migrate`. A section a squad deleted locally cannot keep `ours` while the plugin still has it: the PO takes the plugin's wording or supplies their own.

**Alternative rejected:** a textual three-way merge tool (conflicts land in prose the PO cannot judge).
