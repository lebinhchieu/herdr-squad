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

## Checks

<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | Homes.test_list_for_a_lone_scope_and_for_a_goal: ok | test_squadupgrade Homes list test ok; scratch run: goal check lists goal+s1, not _done/other goals, exit 3 | live: homes --check lone/goal, exit 3/2/0, md5 before/after: ok |
| AC2 | recipe step 8: exit 2 names plugin.pin | scratch run: no plugin.pin -> exit 2 naming plugin.pin | live: no/garbage plugin.pin exit 2 names file: ok |
| AC3 | code path in _read; no test | scratch run: no-pin and old-format scopes listed, files byte-identical after --apply --yes (diff -r) | live: no-pin, old-format listed, files byte-identical after apply: ok |
| AC4 | Homes stale+refused tests: ok | scratch run: stale replace -> moves + stranded warning; NOPE-9 op -> refused, exit 2, diff -r unchanged | live: B-only hash moves + stranded warning; NOPE-9 refused exit 2, nothing written: ok |
| AC5 | Homes crlf test: ok | scratch run: no --yes exit 3 NOT APPLIED, unchanged; --yes one-line diff, 2 log rows; 2nd run nothing to move; Homes crlf test ok | live: no --yes exit 3; --yes one-line diff, CRLF kept, log rows, pin/overlay same, 2nd run nothing to move: ok |
| AC6 | Homes only test: ok | scratch run: --only zzz exit 2 listing offered; Homes only test ok | live: --only s2; --only nope/solo exit 2: ok |
| AC7 | test_squadruntime+test_squadupgrade: ok | read diff: iter_homes sole glob, _holders uses it; stdlib; docstring+README list homes; 235 tests ok | - (whitebox) |
| AC8 | windows_safe/utf8/instructions: ok | unittest test_windows_safe test_utf8_helpers test_instructions test_squad_close test_team_cli ok (in 235) | - (whitebox) |
| AC9 | 5 Homes tests: ok | unittest test_squadupgrade.Homes ok | - (whitebox) |
| AC10 | recipe run, outputs in evidence.md | recipe re-run by me: exits and key lines match evidence.md | live: recipe steps 1-8 match: ok |

## QA whitebox review

### QA whitebox, ticket 01, sha 902f85f

Verdict: PASS. No finding breaks an AC or a test.

Run by me: `test_squadupgrade test_squadruntime test_windows_safe test_utf8_helpers test_instructions test_squad_close test_team_cli`, 235 tests OK (no suite receipt for this sha). Scratch squad from the evidence recipe (two plugin copies, stale `replace` op): exits and key lines match `evidence.md`. Extra scratch checks: no-pin, old-format and `_done` homes are not written (`diff -r`, AC3), refused compose and `--only zzz` leave the squad unchanged, missing `plugin.pin` exits 2 naming it.

#### Follow-ups (not blocking)
- bin/squadhomes.py `run` (movers/chosen): a home refused at read time (malformed `plugin:` line) is never in `movers`, so `--apply` skips it silently; `--check` exits 2, `--apply` can print `nothing to move` exit 0. Surface its note on `--apply` (code reading, not run).
- AC3 has no test (Dev's choice, test economy); verified by hand above.
- `stranded`: `or other.pin is None` is dead after the `state` test (`no-pin` state is None only when pin set... harmless).

## QA blackbox review

### 01 QA blackbox: `squad-process homes` on 902f85f
Method: live. Scratch squad built from the Developer's recipe (`evidence.md` `## Behaviour`): plugin copies A (0.10.1) and B (0.10.2, CORE-1 text edited), overlay `replace CORE-1 @563abba4` (hash of B only), homes solo / s1 / s2 / g1 pinned at A. File state compared by md5 before/after (excluding `_runtime/`). No code read.

| AC | Mode | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 lone scope | live | `homes --check --home scopes/solo` | one row `scope solo ... moves`, exit 3 | pass |
| AC1 goal | live | `--check --home goals/g1` with extra scopes: `_done/old1` (goal g1), `o4` (goal other) | rows g1, s1, s2 only; `_done` and `o4` not listed; kind, name, pin now, target, state shown | pass |
| AC1 exit codes, read-only | live | check at A pins (3), refused overlay (2), all at target (0); md5 of every file outside `_runtime/` before/after | 3 / 2 / 0; no file changed; `_runtime/0.10.2-8970b58c2479` created | pass |
| AC2 | live | `rm plugin.pin`, then `plugin.pin` = `garbage` | exit 2 `.../plugin.pin: missing; no target pin ...`; exit 2 `.../plugin.pin: expected one line ..., got 'garbage'` | pass |
| AC3 | live | s2 without `plugin:` line, s3 with `size: M`; check, then `--apply --yes` | `no-pin` and `old-format` (with reason line); after apply both files byte-identical | pass |
| AC4 stale op | live | overlay with B-only hash | g1/s1/s2/solo compose at B so `moves`; `will refuse spawn and respawn: scope solo: CORE-1: overlay written for @563abba4, plugin now @26ef0fc5` for the un-offered home | pass |
| AC4 refused | live | add `replace NOPE-9 @deadbeef`; `--apply --yes` for solo, and for g1 (all refused) | row `refused` + `manager: NOPE-9: replace of an ID the plugin does not have`; exit 2; md5 of all files incl. no `process-log.md` created: unchanged | pass |
| AC5 no yes | live | `--apply` | `NOT APPLIED (add --yes after Chieu confirms)`, exit 3, md5 unchanged | pass |
| AC5 yes | live | `--apply --yes` for g1; CRLF copy of s1 | `diff` shows one changed `plugin:` line per file; goal edits `goal.md`; CRLF file keeps `^M`; one log row per home; `plugin.pin` and `process.local.md` cmp-identical; second run `nothing to move`, exit 0 | pass |
| AC6 | live | `--only s2`, `--only nope`, `--only solo` | only s2 changed; `--only nope`/`solo`: exit 2 `not an offered home (offered: g1, s1, s2)` | pass |
| env default home | live | `SCOPE_DIR=` / `GOAL_DIR=` set; neither set | scope: one row; goal: g1+s1+s2; neither: exit 2 `no home: run inside a scope or goal session or pass --home` | pass |
| AC7, AC8, AC9 | - | not observable from outside; whitebox owns | - | n/a |
| AC10 | live | recipe steps 1-8 | all exit codes and key lines match the Developer's table | pass |

Not checked (outside 01): respawn (02), skill dialog (03).
Follow-ups (not AC): after `--apply --yes` the printed table still shows the old pin and `moves` for moved homes (a pre-move snapshot); the `moved ...` lines carry the result.
