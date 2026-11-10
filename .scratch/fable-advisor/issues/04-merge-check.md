# 04: `squad-merge-check`, one command for the pre-merge checks
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: A (after: none; then 05)
Files: new `bin/squad-merge-check` (+ helper module if `bin/` convention needs one), new test file under `tests/`
Source: idea 3. First check what `bin/squad-merge-record` and `squad-evidence` already do; reuse, do not duplicate.

## Business AC
1. `squad-merge-check <branch-or-sha> [--base REF]` prints, one line each: ancestor of base (yes/no, GOAL-7 `git merge-base --is-ancestor`), the `git log --oneline base..sha`, both checkers' PASS shas from the ticket evidence / task state and whether they match (MRG-2, evidence-only commit allowed via `squad-evidence check --base`), untracked files outside `.claude/squads/` (MRG-5), main-moved result: files changed on each side and shared test hits (SQ-7), sibling relation for passed branches (SQ-6).
2. Ends with one `VERDICT:` line: ok, or the reasons it refuses (dirty project root, sha not passed, related changes need a Developer merge).
3. It never merges, never changes branches, never writes. Exit 0 ok, 1 refuse, 2 usage.
4. A test per verdict path (ok, dirty root, sha not passed, main moved with related files).

## Technical AC (QA whitebox; agreed with dev-a in design notes, amend there)
T1. Read-only proof: the tool only runs `git` read commands (`rev-parse`, `merge-base`, `log`, `diff --name-only`, `status --porcelain`, `grep`) and reads files. A test runs it on a fixture repo and asserts `git status`, HEAD, branch and the squad dir are byte-identical before and after (hash of `.git` refs plus file list). No `git merge/checkout/commit/add/reset`, no file write in the source (`grep` shows none).
T2. Exit codes: 0 ok, 1 refuse, 2 usage (no args, unknown flag, unknown ref). A bad ref is exit 2 with a one-line message, never a traceback.
T3. Reuse: PASS shas and states come from `squadtask` / `squadledger` / `squadevidence` (imports or calls), not a second parser of `task-events` or evidence files. The Developer names the functions reused in `evidence.md`. Layout follows `bin/` convention (thin script + `squad*.py` module, `squadio.utf8_stdio()`, `sys.dont_write_bytecode`).
T4. Real samples (REV-4): the parser of the ledger / task-events runs against a real scope's `task-events/*.jsonl` and `messages` (copy of one under `mktemp -d`, never the live one for write), including a ticket with a return and a ticket never passed. I also run it once read-only on this live scope.
T5. One test per verdict path in AC4 (ok, dirty root, sha not passed, main moved with related files), plus: one "main moved, no shared file" path yields ok with the "N files, none related" note. Fixtures are temp git repos; no network; no real squad dir touched. Extend an existing test helper (`tests/squadtest.py`) where it fits.
T6. Output contract: each check is one line with a stable label; last line starts `VERDICT:`; when refusing it names every reason. Asserted on labels, not on full strings of git output.
T7. Untracked-file check ignores `.claude/squads/` only (MRG-5) and does not ignore other `.claude/` paths. Shared-test-hit check uses `grep -rl` semantics over `tests/` (SQ-7), fixed-string, no shell injection from a branch name (args passed as a list, no `shell=True`; a branch named `x;touch y` creates nothing).
T8. Run: the new test file, `tests/test_squad_merge_record.py`, `tests/test_squad_evidence.py`, plus `grep -rl squad-merge-check tests/` hits. `tests/test_no_bare_bash.py` and `tests/test_hooks_json.py` still pass (new `bin/` file may be scanned).
T9. Docs: the rule files that tell the Manager to run these checks (`merge.md`) are NOT edited here (ticket 10 owns that); the tool's `--help` prints usage.
