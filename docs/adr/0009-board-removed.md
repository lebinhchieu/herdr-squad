# The squad board is removed; the PO reads `squad-inbox`

Status: accepted (remove-board)

**Decision:** the plugin has no live board: no `squad-board`, `squad-board-start`, `/squad:squad-board`, recorder, `board` tab or guide. `squad-start` opens the Manager tab only.

**Why:** the PO no longer wants it. It was the largest part of the plugin (about 20 test files and a 45 KB guide) and carried its own layout adapter, state payload and pane-status rules that every other change had to keep in step.

**Consequences:**
- ADRs 0001, 0002 and 0003 described only the board and are superseded. ADR 0004's rule still holds for the CLI tools: a squad is per-scope when `scopes/` is a directory, otherwise flat; there is no setting, and each home keeps its own roster, escalations, logs, `iterations/` and `roles/`.
- ADR 0007 still holds except two lines: nothing reads `escalations.md` as a "Needs-you" list, and there is no cross-home view; `squad-inbox` is per home only.
- `messages.jsonl` and the `squad-log-message` hook stay because `squad-migrate` reads them; `activity.jsonl` stays in `squad-migrate`'s carry list so an old squad loses no file, but nothing writes a new one.
- `process.md` is at version 3: the Manager no longer "reads the board" before a `STATUS` ping.
- A board already running on someone's machine is not stopped or cleaned up; nothing in the plugin starts one again.
- Known loss: the live cross-home view, per-agent status bars and Jump to panel. A replacement is a new decision.
- `tests/run_suite.py` keeps `--tz`, `--if-changed` and the browser lock, but no file uses them now (no time or browser tests); removing them touches `CLAUDE.md`, `agents/dev.md` and `process.md` and is a separate decision.

**Alternative rejected:** keep the code and hide the tab (the tests, the guide and the pane-status rules would still need upkeep for something no one opens).
