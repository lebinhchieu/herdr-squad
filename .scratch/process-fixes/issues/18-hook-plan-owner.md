# Task 18: merge the two bases; the Developer hook text names the plan owner

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Also run tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py (SQ-10) and quote the result in `## Behaviour`. Source: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task.

Status: building
Source: finding 6 (Chieu E17 a).
Files: bin/squad-usage-hook, tests/ (extend the existing hook test; grep `tests/` for other hits)
Ticket: commit this file's content as `.scratch/process-fixes/issues/18-hook-plan-owner.md` in your first commit after the merge.
Base: squad/plugin/line-visible/plugin-dev-line-visible-1 (172a373). Step 1: `git merge squad/plugin/respawn-guard/plugin-dev-respawn-guard-1` (cae8966); check both are in (`git merge-base --is-ancestor`), run the targeted tests of both sides (tests/test_squad_usage.py, tests/test_squad_respawn.py, tests/test_squadruntime.py). No merge into main.

## AC
- AC1 Merge: both branch heads are ancestors of the task's branch; the targeted tests of both sides pass.
- AC2 Hook text: the Developer text of `bin/squad-usage-hook` (line ~35) no longer says "tell the Team Lead" always. It says "tell your plan owner": the Team Lead when `scope.md` of the agent's scope has a `team:` line naming `team-lead`, else the Manager. The rule pointer stays [COST-5] / [COST-5a] as fits. No scope.md or no team line: the Manager.
- AC3 Other roles' text is unchanged.
- AC4 One test per AC 2-3 (extend the existing hook test) with a small scope.md fixture.

## Design notes
Touched files: bin/squad-usage-hook, tests/test_squad_usage_hook.py (grep hits in other tests: only test_squad_manager_guard, test_utf8_helpers, test_squad_respawn mention the hook name; none assert the Developer text).
- In the `dev` branch of the hook, read the `team:` line of `$home/scope.md` with sed (trailing `(note)` cut off, so `team-lead` in a note does not count). `team-lead` as a whole comma-separated token gives the Team Lead and pointer [COST-5]; everything else gives the Manager and [COST-5a]. No new tool; `set -u` safe; the hook still exits 2.
- Agree with QA whitebox TA1-TA5 as written. The `fresh` fixture of the existing test has no scope.md, so its two asserts now expect the Manager ([COST-5a]).

## Technical AC (QA whitebox, coarse on purpose; Developer may propose changes in the design notes, 2 exchanges max)
- TA1 Merge: `git merge-base --is-ancestor 172a373 HEAD` and `... cae8966 HEAD` both true; no conflict markers left (`grep -rn '^<<<<<<<' bin templates tests`); the three merge tests (test_squad_usage.py, test_squad_respawn.py, test_squadruntime.py) pass. Merge commit is first, the ticket file commit after.
- TA2 Plan owner is read from `$home/scope.md` (the same `home` the hook already uses for the log). It is the Team Lead only when the `team:` line names `team-lead` as a word; anything else (no file, no `team:` line, `team: none ...`, unreadable) gives the Manager. The hook never fails on this: still exit 2 with the message, `set -u` safe.
- TA3 Developer text: says "plan owner" and names who it is; pointer is [COST-5] for the Team Lead, [COST-5a] for the Manager (these match the `when: plan-owner` split in cost.md). The `mid-ticket, run once: squad-respawn <name>` part stays. The `action` field in `usage-events.jsonl` carries the same text.
- TA4 Non-dev roles: the message and the `action` are byte-identical to before (exact-string assert for one non-dev role).
- TA5 Tests (extend tests/test_squad_usage_hook.py): the two assertions at lines 59 and 63 now expect the Manager (that fixture has no scope.md); add one test with a `team-lead` scope.md (Team Lead, [COST-5]) and one non-dev exact-string test. Run: the hook test file, `grep -rl 'tell the Team Lead' tests/` hits, and the three SQ-10 files. No other test newly skipped.
