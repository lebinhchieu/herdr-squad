# 04: Untrack dev state from the plugin repo

Status: ready-for-agent
Type: task
Blocked by: none
Source: findings.md W7

**What:** the installed plugin cache is 33 MB; 29 MB is the repo's own working state. `git ls-files` shows 4007 tracked files under `.claude/` (`squad-backups/…`, nested `_runtime/<old version>/` copies of whole old plugins) and 88 under `.scratch/`. Every user installs them. On Windows the longest tracked path is 166 chars; under `…\plugins\cache\herdr-squad\squad\0.6.1\` (about 75) it is near the 260-char limit, and a deeper project root or `_runtime` extraction would break it. (`LongPathsEnabled` could not be read on the test machine.)

## Do
- Decide what the release must ship (`bin/ agents/ skills/ hooks/ templates/ docs/ .claude-plugin/ README`) and stop tracking the rest: `.claude/squad-backups`, `.claude/squads`, `.scratch/_done`, nested `_runtime` copies. Keep history in a separate dev repo or release assets; do not rewrite git history without the PO's say.
- If untracking is not wanted, exclude them from the installed package instead (check how the marketplace copies the tree).
- Check that no test reads these folders (`grep -rn "squad-backups\|_done" tests/`).

## AC
- [ ] A fresh install of the next version is under 5 MB and its longest path is under 200 chars.
- [ ] Suite green; the squads in `.claude/squads` of existing projects are unaffected.

## Comments
