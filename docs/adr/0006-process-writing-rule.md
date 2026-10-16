# The Writing rule for `process.md` lives in the Manager's file

Status: accepted (refine-process)

Amended by 0010: the byte budget was removed (PO, tl-manages-team); the rest stands.

**Decision:** the Writing rule for `process.md` (one rule per bullet, stated once, actor and limit named, no hedges, history, dates or restating sentences, at most 60 words per bullet or cell, a byte budget) lives in `agents/manager.md`, the only role that edits `process.md`, not in `process.md`. `bin/processlint.py` checks it mechanically; the suite lints the template on every run; `apply` warns on the combined file.

**Why:** every agent reads `process.md` at start, so its size is every session's starting cost; the rule is needed only when editing.

**Consequences:**
- A new rule replaces or merges with an existing one, or the PO raises the budget (the figure is in the Manager file and the `processlint` default; a test pins them equal); exceptions are listed in `tests/test_process_writing.py` with a reason. The rule reaches squads by plugin update, not by the process migration.
- A rule stated twice in `process.md` counts as one rule: merging duplicates is allowed. Removing a rule that appears once, moving it out of the file, or changing a number or an owner is a PO decision via the Manager.
- The `process.md` byte budget is 22,500 B, set by the PO; the template was 27,745 B before the trim.
- A rule a teammate without the squad must also follow (the project's code, tools, test commands, conventions) goes into the project's instructions file named in `project.md`, through a task the PO merges, never into `process.md`; `process.md` holds only how the squad works, true for any project. The Manager's Writing rule carries this as its first bullet; the repo's test rules are in `CLAUDE.md` → Running tests.
