# Evidence: 16 Integration: merge the passed branches of 09-15

## Behaviour

Merge commit (HEAD before this evidence commit) `3b76f3f` = `8dbcccf` (tickets 12-15, branch `...-18`) plus `bb77826` (tickets 09-11, branch `...-14`). The merge was clean: no conflict in `bin/squad-usage` or `tests/test_squad_usage.py`, so no hunk was dropped. Base `2b535f5` = `git merge-base main HEAD`.

**AC1 every passed sha is an ancestor of HEAD**
```
$ git merge-base --is-ancestor bb77826 HEAD   exit 0   (09 tip)
$ git merge-base --is-ancestor bf69a21 HEAD   exit 0   (10)
$ git merge-base --is-ancestor 6b1b601 HEAD   exit 0   (11)
$ git merge-base --is-ancestor 24c1fc8 HEAD   exit 0   (12)
$ git merge-base --is-ancestor 535077d HEAD   exit 0   (13)
$ git merge-base --is-ancestor dfb2a3d HEAD   exit 0   (14)
$ git merge-base --is-ancestor 8dbcccf HEAD   exit 0   (15, evidence-only tip)
```

**AC2 tests and lint** (foreground, `< /dev/null`, `python3 -m unittest` from `tests/`; pytest is not installed):
```
test_hooks_json test_squad_evidence test_squad_ledger test_squad_log_message test_squad_merge_check
test_squad_review_pack test_squad_spawn test_squad_usage test_squad_usage_hook test_squadtask      (union of 09-15 test files)
test_squad_respawn test_session_lookup test_squad_manager_guard                                  (shared files named by the plan)
test_windows_safe test_utf8_helpers test_instructions                                            (SQ-10 trio)
Ran 443 tests in 65.230s   OK
$ python3 bin/squad-process lint    exit 0
```

**AC3 version** `.claude-plugin/plugin.json` `"version": "0.11.1"`; `skills/squad-process-update/changelog.md` line 1 is `## v32 -- 2026-11-25`, with one bullet each for 09-15 (the merge changed neither file: `git diff --name-only HEAD^1 HEAD` lists none of them).

**AC4 diff scope** `git diff --name-only 2b535f5 HEAD` outside `.scratch/`: `bin/squadevidence.py squadledger.py squad-log-message squadmergecheck.py squad-review-pack squadreviewpack.py squad-spawn squadtaskprompt.py squadtask.py squad-usage squad-usage-hook`, `hooks/hooks.json`, `README.md`, plugin.json, changelog.md, and ten test files; every one is in a Files line of 09-15. `git diff --stat HEAD^1 HEAD` (what 09-11 add): 10 files, 461 insertions, 64 deletions.

## Review

Fresh-context reviewer (sonnet, high) on the merge `3b76f3f` (parents `8dbcccf`, `bb77826`), Standards and Spec axes. Spec: AC1-AC4 met. Standards: none. Findings: none. It diffed the added and removed lines of `git diff 46d2f4b bb77826` against `git diff 46d2f4b HEAD` for `bin/squad-usage`, `bin/squad-usage-hook`, `hooks/hooks.json` and the three usage and hook tests: identical, so no 09-11 hunk was dropped. README squad-usage row appears once (09 wording), rows from 12-15 intact; changelog has one `## v32` with bullets 09-15 in order; plugin.json 0.11.1; `hooks.json` has the usage hook once in Stop and once in PostToolUse. It re-ran `test_hooks_json`, `test_squad_usage`, `test_squad_usage_hook`: 67 OK. Checks: see `## Checks` below.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `git merge-base --is-ancestor <sha> HEAD` exit 0 for 7 shas | - | - |
| AC2 | 443 tests OK (union + shared + SQ-10 trio); `squad-process lint` exit 0 | - | - |
| AC3 | plugin.json 0.11.1; changelog top `## v32` | - | - |
| AC4 | name-only diff vs `2b535f5` lists only 09-15 files | - | - |

## Changelog line

None new: the v32 bullets for 09-15 are already in `skills/squad-process-update/changelog.md`; ticket 16 changes no file outside merges. why: integration only merged passed branches and proved them together.
