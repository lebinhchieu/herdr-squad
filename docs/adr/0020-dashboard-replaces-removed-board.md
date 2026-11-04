# A read-only dashboard replaces the removed board

Status: accepted (dashboard, PO accepted the architecture 2026-11-04)

Supersedes only the "Known loss" line of 0009 (the live cross-home view, per-agent status bars and Jump to panel are lost and a replacement is a new decision: this is that decision, in a smaller form). It also contradicts one more 0009 line, plainly: "nothing reads `escalations.md` as a Needs-you list" (see Consequences). Every other line of 0009 still holds. Amends 0007 in one line. Does not revive 0001, 0002 or 0003.

**Decision:** the plugin gets a new `squad-board`: one local page for **one goal or one scope at a time**, started by the PO from a terminal (`squad-board [--squad NAME|PATH] [--goal G | --scope S] [--port N] [--no-open]`). It is a different thing from the board 0009 removed: it has no recorder, no `activity.jsonl`, no `board` tab, no pane-status rules, no cross-squad view. It only reads what the squad already writes (messages, escalations, the inbox through `squad-inbox list --json --no-write`, roster, tickets, git, `herdr agent list`, transcripts) and writes one file, `board-ui.json`. `squad-start` still opens the Manager tab only and prints the board command.

**Why:** the PO wants to see what waits on him, how each task stands and where the time went, without asking the Manager. 0009 removed the old board because its recorder and layout adapter cost every change; this one adds no new stream and needs no change to any role's routine.

**Consequences:**
- 0009's rule "nothing reads `escalations.md` as a Needs-you list" no longer holds for the board; the board reads the inbox through the CLI (the version-1 contract), not the file. 0007's "no cross-home view" still holds: the board shows one goal or scope, and never all of them at once.
- New files the squad keeps: `board-ui.json` (UI state, the board writes it), `open-questions.md` (parked questions, written only by `squad-inbox park|unpark|resolve`), and an optional `tickets: <feature-slug>` line in `scope.md` (the Manager writes it at plan; the board falls back to a guess). `process.md` gets a version bump for the line and the Manager's rule to read `open-questions.md` (ADR 0005).
- New code: `bin/squad-board`, `bin/squadboard*.py` (one reader per source), `bin/squadtickets.py` (moved from `squadreport_tasks.py`), `templates/board/` (static page: no build, no CDN, light theme only). Python stdlib only. It runs on Windows (0011): `git` and `herdr` by subprocess name, no `fcntl`.
- It binds 127.0.0.1, rejects a `Host` header that is not local, needs a token for the one write (`PUT /api/ui`), serves files only under the squad folder and `.scratch`, and sends HTML with a sandbox Content-Security-Policy.
- Work time comes from transcripts only (0014); there is no new hook. Per-task time is approx and says so. Not built, by PO decision: exact per-task time, artifact-to-slice, derived goal status, tokens, cost, idle share, parallelism, PO working time, ADR list, worktree list panel, scan of other repos, median review wait.
- `tests/run_suite.py` and its browser lock are used again by the page tests; the note in 0009 about unused flags no longer applies.

**Alternatives rejected:** restore the old board (its recorder and adapter); a framework or CDN library (a dependency to keep alive); a hook that logs the task on every tool call (every agent pays on every call, and 0009 removed that stream); a cache file in the squad (one more thing to invalidate).
