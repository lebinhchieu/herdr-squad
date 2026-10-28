# F squad-spawn never ignores --base; G version 0.3.4

Status: ready-for-agent
Type: task
Source: iteration 3, PO answer E6 (b); the stale-base finding of iteration 2
Touches: `bin/squad-spawn`, `tests/test_squad_spawn.py`, `.claude-plugin/plugin.json`
Blocked by: none. Base `20b53e8`. One Developer (`plugin-dev-win-compat-9`); its passed branch is the integration branch.

## What
**F.** In `bin/squad-spawn` (the `elif [[ -n $repo ]]` block, ~line 130) `git worktree add ... ${base}` runs only when the worktree folder is missing. When the folder already exists, `--base REF` is dropped without a word and the Developer starts on whatever commit that old worktree holds. That cost iteration 2 a round of stale-base work.

**Decision (Tech Lead): refuse, do not verify.** `--base` exists to say "start a NEW branch here". An existing folder is already a branch somewhere, so the request cannot be honoured, and an ancestor check would still leave the Developer on a different commit than the one the caller named. `squad-respawn` passes `--worktree`, never `--base`, so no legitimate flow combines `--base` with an existing folder.

Behaviour, all before any `herdr` call or `git worktree add`, in `--dry-run` too, exit status 2:
1. `--repo` given, `--base` given, the worktree folder exists: print one line to stderr naming the folder and `--base REF`, saying the base would be ignored, and what to do (a new agent name, or drop `--base` to reuse the folder). Nothing is spawned.
2. `--worktree DIR` given together with `--base`: same refusal (today `--base` is ignored there too: `--worktree` wins).
3. Unchanged: no `--base` and the folder exists reuses it; `--base` and no folder makes the branch from REF; `--base` without `--repo` is still `--base needs --repo`.
4. The `--base` line of the usage text says it is refused when the folder exists.

**G.** `.claude-plugin/plugin.json` `"version"` goes `0.3.3` to `0.3.4`. This is the LAST commit of the branch and the only change in it. No other file carries the version (checked: `marketplace.json` has none).

This ticket file is copied into the Developer's branch (read it by absolute path; there is no commit of it on main).

## Technical AC (Tech Lead)
1. Test, `tests/test_squad_spawn.py`, exact assertions: (a) `--repo R --base X` with the folder `.worktrees/<squad>/<scope>/<name>` already created: exit 2, stderr contains the folder path and `--base`, stdout has no `worktree add` and no `herdr`. (b) `--worktree D --base X --repo R`: exit 2, same stderr check. (c) Existing folder without `--base`: exit 0 and `--cwd <folder>` in stdout (reuse still works). (d) Real git, as the existing `test_real_spawn_with_base_...`: make the worktree once with `--base passed`, run again with `--base main`; the second run exits 2 and `rev-parse HEAD` in the worktree is still `passed`'s commit.
2. Each new test fails on `20b53e8` (show the failing run in the evidence) and passes on the tip.
3. Every existing `test_squad_spawn` and `test_squad_respawn` test passes unchanged; the test count rises by the new tests only.
4. The refusal runs before any side effect: no directory created, no `git` call (check with a repo path that is not a git repo in test (a): it still exits 2 with the base message, not a git error).
5. `git diff --stat 20b53e8 HEAD` lists only the four paths in Touches plus this ticket file. `plugin.json` differs by the one version line. No other `bin/`, `agents/`, `templates/` change.
6. Final sha: `git merge-base --is-ancestor 20b53e8 HEAD` printed in the hand-in; the version bump is the last commit; run tests from inside `tests/` with `PYTHONDONTWRITEBYTECODE=1`, in a UTF-8 locale and under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`. The Developer runs `test_squad_spawn`, `test_squad_respawn`, `test_instructions` only. I run the full suite `--tz` on the final sha.
7. Real Windows is not testable here; the change is bash and git only and adds no new Windows-specific path.

## Comments
