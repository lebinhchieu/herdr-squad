# Deploy plan: plugin 0.6.0 (teams replace sizes)

Written by the Tech Lead (LC-13); never run by it. The PO runs it after the merge. Source: `tasks/tech-design.md` LC-12, ADR 0018.

**Breaking:** an unpinned squad cannot compose or spawn until it is converted. Pinned scopes (<0.6.0) are untouched.

## Order
1. Finish or close open scopes if possible (`squad-close`). Its edits to `templates/squad/process/` can conflict with this branch: rebase first.
2. Merge the scope's integration branch (PO's call; the Manager runs it on request). Version is 0.6.0 in `plugin.json`, changelog v9, README, snapshot.
3. **Before any respawn of an unpinned squad under 0.6.0:** `squad-process adopt --dry-run`, read the proposed `team:` per scope, then `squad-process adopt --yes`. It writes `team:`, removes the four old lines, keeps `scope.md.pre-team.bak`, skips pinned scopes and `_done`. A blank `size:` becomes a blank `team:` (undecided: only the Manager composes).
4. In each squad: `squad-process upgrade`. Overlay ops with `when: size|qa-b|qa-whitebox` are listed with a translation (exit 3); edit them by hand, `--apply` refuses until none is left. Stale ops: `--resolve`.
5. New scopes: `squad-start` proposes the team; the PO confirms.

## Rollback
- Revert the merge commit. Pinned scopes (including any pinned at 0.6.0) run their own `git archive` runtime and do not depend on the tree.
- Converted squads hold `team:` lines the old engine ignores: restore each `scope.md` from `scope.md.pre-team.bak` (byte-identical). Overlays edited after `upgrade` need the same manual revert.

## Checks after deploy
- `squad-process lint` exits 0.
- Scratch squad: `squad-start` proposes a team; `squad-spawn qa-whitebox` works with it on the team; `squad-spawn architect` is refused without it, with text naming who adds it.
- `squad-process compose` works for a decided team (all roles) and for an undecided team (Manager only; others exit 2).
- Compose on an unconverted `size:` scope.md exits 2 with the `squad-process adopt` pointer.
- Converter dry run and apply on a copy of an old squad (`plugin-bk261023`); each converted scope composes for every role.
- A pinned 0.5.2 scope still respawns from the PO shell.
- `squad-report` on a folder with one old and one new scope.
- `python3 tests/run_suite.py --tz` receipt on the merged sha.

## Not done here
- F3: the Manager writes the PO's `team:` reply into `scope.md` by hand; no command (follow-up).
