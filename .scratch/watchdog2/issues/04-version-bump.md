# Task 04: plugin patch version bump

Duties: design notes: Developer (here); technical AC: Developer; business AC: the ticket as written; `promote.md`: none; full suite: none (a version string; the merge sha gets `--tz` when Chieu asks). Code check: the Developer's `## Review` confirmed by the Manager. A risk flag or doubt: `BLOCKED 04`.

Status: ready
Files: `.claude-plugin/plugin.json` only.
Ticket: commit this file's content as `.scratch/watchdog2/issues/04-version-bump.md` in your first commit.
Base: main (it already holds wd2-trigger and wd2-away).

## AC
- AC1 `.claude-plugin/plugin.json` `version` goes from `0.7.6` to `0.7.7`. No other file changes except the ticket and its evidence.
- AC2 `grep -rn "0\.7\.6" tests bin hooks skills agents docs templates README.md CLAUDE.md .claude-plugin` finds no pin besides plugin.json before the change, and no `0.7.6` after it (quote both outputs in the evidence).
- AC3 Touched tests: run every test file that `grep -rl "plugin.json\|version" tests/` shows for the plugin version (targeted, no full suite); they pass.

## Evidence
`evidence.md` next to the ticket, with `## Behaviour` (the AC2 greps and the AC3 run, copied output) and `## Review` starting with an AC trace (SQ-2): `AC<n> | capture | how run`. `squad-evidence check` on its folder must pass. HANDIN to the Manager (plugin-mgr-watchdog2) with branch and sha.
