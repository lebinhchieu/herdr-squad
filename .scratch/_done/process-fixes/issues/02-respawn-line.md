# Task 02: Fix 2: one respawn line per session = context at first action + 50k, hard cap 180k

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 02`.

Status: ready-for-agent
Source: `git show squad/plugin/process-audit/plugin-dev-process-audit-6:.scratch/process-audit/report.md` (6f500f8, unmerged), section 4 finding 2. Read only that finding.
Files: bin/squad-usage, bin/squad-usage-hook, bin/squad-manager-guard, templates/squad/process/cost.md (+ notes.md, iterations.md text), tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/02-respawn-line.md` in your first commit.
Base: main.

## AC
- AC1 `squad-usage --check` fires `fresh` at (the session's context at its first action) + 50k, never above 180k.
- AC2 Plugin rule text that names a fixed 100k/120k line (cost.md COST-5a, the Manager line, COST-3) points at that signal; no fixed number remains in plugin rules.
- AC3 Final report lists other fixed-line rules found outside the plugin (e.g. this squad's overlay SQ-3, board SQ-1/2/4) without editing them. Touched test files pass.

## Rules to follow
- [REV-15] report deliverable: copy any report into `$SCOPE_DIR/evidence/{n}/` at the handed-in sha.
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run only touched test files plus `grep -rl` hits for touched `templates/` paths or printed strings.
- Do not bump the plugin version; the last scope does it once.

## Design notes
- **Line:** `respawn_line(s)` in `bin/squad-usage` = `min(first_action_ctx + 50_000, 180_000)`; `CAP` (180k) when no first action exists yet. Constants `ROOM`, `CAP`, `ACTION_TOOLS` replace `FRESH_CTX`, `IDLE_CTX`.
- **First action** (audit definition): context of the first main-thread assistant message that has a `tool_use` of Edit, Write, NotebookEdit or SendMessage (message usage = max over its lines, as `read_session`). Subagent lines (`isSidechain`) never count. Read in `squad-usage` from the raw lines (`first_action_ctx`), so the shared `squadtranscript.py` is untouched.
- **Check:** `check(s)` returns `fresh` on a compaction or `last > respawn_line(s)`, else nothing. Manager ruling (FINAL 02): no idle line; an idle session past its line is the same `fresh`. The `idle` hook branch and `IDLE_CTX` are gone; COST-9 stays, pointing at [COST-3].
- **Manager line:** Manager ruling: `bin/squad-manager-guard` calls `usage.respawn_line(s)` instead of `CTX_LIMIT=100k`; notice text `over its <n>k line`.
- **Rule text:** COST-3 holds the definition; COST-1/2/5/5a/6a/6b/8/9, notes.md NOTE-3 and iterations.md point at it or at `fresh`. No 100k/120k left in `bin/`, `templates/`. The 80k (ticket assignment) and 60k (PO wait) values are not respawn lines and stay.
- **Size guard:** composed Manager rules grow 118-132 B, so `test_manager_composed_bytes_did_not_grow_vs_90be196` baselines are raised by exactly that (precedent: ticket 06). Dev rules stay under 5 KiB.
- **Tests:** `test_squad_usage` (line, first-action rule, cap, no-action, subagent, idle), `test_squad_usage_hook`, `test_squad_manager_guard`, `test_dev_rules_size`.
