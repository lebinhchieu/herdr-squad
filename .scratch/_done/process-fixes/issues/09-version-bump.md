# Task 09: Plugin version bump 0.7.3 -> 0.7.4

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`.

Status: ready
Source: goal process-fixes: one version bump, in the last scope. Contents of the goal: lean spawn (lean.json, mcp default []), respawn line, watchdog (sleep opt-in), QA blackbox shots first.
Files: .claude-plugin/plugin.json, any other file that names the version (find with `grep -rn '0\.7\.3' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude`), tests that pin it
Ticket: commit this file's content as `.scratch/process-fixes/issues/09-version-bump.md` in your first commit.
Base: main. Own worktree. No merge.

## AC
- AC1 The version reads 0.7.4 everywhere the old one was named in tracked plugin files (plugin.json, README, changelog if any).
- AC2 Tests that pin the version are updated; touched tests pass.
- AC3 Nothing else changes.

## Design notes
The grep (`grep -rn '0\.7\.3' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude`) finds one file: `.claude-plugin/plugin.json` line 4. No README, changelog or test names 0.7.3. Same shape as the 0.7.3 bump (3ddccd1: plugin.json only).
