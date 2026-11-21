# 01 `squad-process homes`: evidence

## Review
AC trace (tests run from `tests/`: `python3 -m unittest test_squadupgrade.Homes`):
- AC1 | `Homes.test_list_for_a_lone_scope_and_for_a_goal`, recipe steps 1-2 | unittest; recipe
- AC2 | `bin/squadhomes.py` `run`: `read_pin_file` None -> exit 2 naming `plugin.pin`; unparseable pin raises in `rt.read_pin_file` (existing path, exit 2 naming the file) | recipe step 8 (no `plugin.pin`)
- AC3 | `_read` in `bin/squadhomes.py`: `no-pin` and `old-format` states are never in `movers` (code path; not a separate test, per test economy) | read the code
- AC4 | `Homes.test_a_stale_overlay_op_moves_at_the_target_and_warns_about_the_stranded_home`, `Homes.test_a_refused_compose_writes_nothing` (snapshot before/after incl. `process-log.md`) | unittest; recipe steps 1, 7
- AC5 | `Homes.test_apply_needs_yes_then_changes_one_line_and_keeps_crlf` | unittest; recipe steps 3-6
- AC6 | `Homes.test_only_limits_the_move_and_a_name_not_offered_exits_2` | unittest; recipe step 4
- AC7 | `iter_homes` in `bin/squadruntime.py` used by `_holders` and `squadhomes`; docstring of `bin/squad-process` and `README.md` list `homes`; `grep -n "glob" bin/squadhomes.py` empty | `test_squadruntime` + `test_squadupgrade` pass unchanged (below)
- AC8 | the three whole-repo tests, quoted in `## Behaviour` | unittest
- AC9 | the five `Homes` tests | unittest
- AC10 | recipe in `## Behaviour` | run once by Dev in a scratch squad, output quoted

`squad-evidence check --base 5aadae0` exit code: quoted in the HANDIN.

## Behaviour
Tests (run from `tests/`):
- `python3 -m unittest test_squadupgrade test_squadruntime test_windows_safe test_utf8_helpers test_instructions`: 148 tests, OK (SQ-10 files included).
- `python3 -m unittest test_squad_close test_team_cli` (hits of `grep -rl 'squadruntime\|_holders\|squad-process' tests/` the diff reaches): 87 tests, OK.

Recipe for QA blackbox (commands only; `SP` = `python3 <worktree>/bin/squad-process`). Two plugin copies at two versions: a clone of the repo, one commit that edits the CORE-1 text and bumps the version.
```
W=$(mktemp -d); git clone -q <worktree> $W/plug; cd $W/plug; git checkout -q -b w
A=$(git rev-parse HEAD)
sed -i 's/^`ready → building/`ready → building (B)/' templates/squad/process/core.md
sed -i 's/"version": "0.10.1"/"version": "0.10.2"/' .claude-plugin/plugin.json
git -c user.name=t -c user.email=t@t commit -qam B; B=$(git rev-parse HEAD)
$SP lint --hashes --plugin-root $W/plug | grep '^CORE-1 '   # B's hash, 563abba4 here
SQ=$W/proj/.claude/squads/x; mkdir -p $SQ/scopes/solo $SQ/scopes/s1 $SQ/scopes/s2 $SQ/goals/g1
echo "0.10.2 $B" > $SQ/plugin.pin
printf '# Local process\n\n## replace CORE-1 @563abba4\nwhy: local\nupstream: local-only\nLocal wording.\n' > $SQ/process.local.md
```
The replace op carries the hash of the NEW plugin B only (`@563abba4`; A's CORE-1 hash is `26ef0fc5`): homes at B compose, homes at A are stale. Use the hash that `lint --hashes` prints for B.
Homes (each pinned old = `0.10.1 $A`): scopes `solo` (`goal: none`), `s1`, `s2` (`goal: g1`) with `team: tech-lead`, `qa: full`; goal `g1` with `goal.md` `plugin:` line. The old runtime: `mkdir -p $SQ/_runtime/0.10.1-${A:0:12}; git archive $A | tar -x -C $SQ/_runtime/0.10.1-${A:0:12}`.

Dev run (commands and results):

| # | Command (all with `--squad-dir $SQ --plugin-root $W/plug`) | Exit | Key output line |
|---|---|---|---|
| 1 | `$SP homes --check --home $SQ/goals/g1` | 3 | rows `goal g1`, `scope s1`, `scope s2` each `moves`; `will refuse spawn and respawn: scope solo: CORE-1: overlay written for @563abba4, plugin now @26ef0fc5` |
| 2 | `$SP homes --check --home $SQ/scopes/solo` | 3 | one row `scope solo ... moves`; warnings for s1, s2, g1 |
| 3 | `$SP homes --apply --home $SQ/goals/g1` | 3 | `NOT APPLIED (add --yes after Chieu confirms)`; files unchanged |
| 4 | `$SP homes --apply --yes --only s2 --home $SQ/goals/g1` | 0 | `moved scope s2: 0.10.1 <A> -> 0.10.2 <B>`; only `scopes/s2/scope.md` changed |
| 5 | `$SP homes --apply --yes --home $SQ/goals/g1` | 0 | `moved goal g1: ...`, `moved scope s1: ...`; s2 row `at-target` |
| 6 | same as 5 | 0 | `nothing to move` |
| 7 | add `## replace NOPE-9 @deadbeef` op to `process.local.md`, then `$SP homes --check --home $SQ/scopes/solo`, then `--apply --yes` | 2, 2 | row `scope solo ... refused` + `manager: NOPE-9: replace of an ID the plugin does not have`; `scopes/solo/scope.md` still `plugin: 0.10.1 <A>` |
| 8 | `rm $SQ/plugin.pin; $SP homes --check --home $SQ/scopes/solo` | 2 | stderr names `.../plugin.pin: missing` |

`process-log.md` after step 5 holds one `Home <kind> <name> plugin <old> -> <new> | squad-process homes --apply` row per moved home; `plugin.pin` and `process.local.md` are unchanged by steps 3-6.
