# 06 Small edits: rm, UI AC, notes pointers

Status: ready-for-agent

Spec: `.scratch/upstream-proposals/spec.md`

## Change

| Source | Target | Edit |
|---|---|---|
| guardian SQ-35 | SAFE-11, all roles | Replace "`cd` out before `rm`" with: `rm` under /tmp takes only a literal absolute path (`rm -f /tmp/<dir>/<file>`, or `rm -rf "$D"` after `D=$(mktemp -d)`). Run `rm` alone: no `cd`, `&&` or `;` in that command; no glob, relative path or `$(...)` target. Why: Claude Code's dangerous-rm check fires on these, and no permission rule can allow it |
| board SQ-8 | REV-8 | A UI business AC names the size it is checked at and the value or rule it must show, with one example for "shortest", "fits" or a count limit. A relative time names the fixture's fixed clock. Leave out the "retire the BA" sentence (START-5 owns that) |
| board SQ-9 | NOTE-1 | `Pointers` holds at most 5 paths, each with a line range or section. After a respawn, read only these before your first reply (COST-7) |

This is the last ticket that touches plugin files: bump the plugin version, add a changelog entry in `skills/squad-process-update/changelog.md` covering 01-06, and grep for the old version.

## AC

- AC1: SAFE-11 attaches to all roles and no longer says "cd out before rm".
- AC2 (as reworded by the Tech Lead, tl-design section 6): `.claude-plugin/plugin.json` says 0.10.11, and the only hits of `0.10.10` under `.claude-plugin templates skills` are inside changelog entries older than v29.
- AC3: `python3 bin/squad-process lint` exits 0.
- AC4: run the targeted tests: `grep -rl` over `tests/` for each changed rule ID and string (CLAUDE.md, Running tests).

## Comments

- Guardian SQ-35 (scratch `rm`) is replaced by plugin rules SAFE-11 (what `rm` takes) and SAFE-11b (run it alone); both attach to all roles. Example is `rm /tmp/<dir>/<file>` (no `-f`), because the settings allow `rm`, `rm -r`, `rm -rf` and `rmdir` under `/tmp/*` only.
- Board SQ-8 (UI business AC) is replaced by new plugin rule REV-8b (the UI clause; REV-8 keeps its base body; no "retire the BA" sentence, START-5 owns it).
- Board SQ-9 (notes pointers) is replaced by plugin rule NOTE-1 (`Pointers`, at most 5 paths, read after a respawn, [COST-7]).
- The squads drop these three ops by hand after re-pin (`upgrade --check` shows them kept or `stale`).
- AC2 as fixed by the Tech Lead (tl-design section 6): the only `0.10.10` hits under `.claude-plugin templates skills` are inside changelog entries older than v29.
