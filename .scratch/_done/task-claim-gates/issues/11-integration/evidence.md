# 11 Integration: evidence

## Behaviour

Two merge commits on `squad/plugin/task-claim-gates/plugin-dev-tcg-6`, no conflict, no behaviour change (AC1):

```
9a67d30 11: merge 06 merge record (tcg-5)   second parent 1e79ce5
a5c2eb3 11: merge 02 hooks record (tcg-3)   second parent 7529110
855c2a7 05: assemble QA evidence            (start)
```
(`git log --oneline --first-parent`). `grep -rn "0\.7\.5"` over tests bin hooks skills agents docs templates README.md CLAUDE.md finds nothing.

**AC2, targeted tests**, each file once with `cd tests; python3 -m unittest <file>`:
all OK except the known failures that also fail on main (fixed fixture dates): panels T12 and T14, list T04, demo T37, and `test_squad_spawn` `test_a_failed_agent_start_leaves_the_old_overrides_file`. No other failure.

| File | Result |
|---|---|
| test_squadtask 15, test_squad_log_message 25, test_squad_merge_record 3, test_squad_ledger 17 | OK |
| test_squadboard_tasks 26, _active 9, _inbox 12, test_board_fixtures 4 | OK |
| test_rules_wording 18, test_dev_rules_size 9, test_squadrules 43, test_processlint 31 | OK |
| test_squad_spawn 100 | 1 known failure |
| test_squadboard_list 13 | 1 known failure (T04) |
| test_squadboard_panels 58 | 2 known failures (T12, T14) |
| test_squadboard_demo 13 | 1 known failure (T37) |

**AC3, end to end in a temp squad** (`mktemp -d`; temp git repo, `SQUAD_DIR` and `SCOPE_DIR` in it; scope.md has `tickets: feat`; roster: dev-1, qa-w, qa-b, mgr). Branch `squad/sq/sc1/dev-1` has one commit.
Each message goes to `bin/squad-log-message` as a PostToolUse SendMessage payload (`SQUAD_NAME` = sender):

1. `HANDIN 01: branch squad/sq/sc1/dev-1, commit 6ec59cc` from dev-1. Hook answers `W3 handed in without a claim; owner taken from sender` (a warning only, no claim was sent).
2. `PASS 01: ok` from qa-w, then from qa-b.
3. `squadboard_tasks.read(...)` (what `/api/tasks` serves) gives `exact [('01', 'passed', 'dev-1')]`.
4. `git merge --no-ff squad/sq/sc1/dev-1` in the temp repo, then the `bin/squad-merge-record` hook with a Bash payload (`SQUAD_ROLE=manager`): exit 0, no warning.
5. `read(...)` again gives `exact [('01', 'merged', 'dev-1')]`.

Events written (`task-events/feat.jsonl`, 4 lines): `handin` (dev-1, sha 6ec59cc, warn W3), `pass` qa-w, `pass` qa-b, `merged` (mgr, sha 804eab8…, branch squad/sq/sc1/dev-1).

**AC4, real store untouched:** `sha256sum .claude/squads/plugin/task-events/task-claim-gates.jsonl` was `6384250bc7340ef3708c5ed8c6b3c043c182404077b4c03c8530c40b9355108f` before and after.
