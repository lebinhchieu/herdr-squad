Status: ready-for-agent
Type: task
Task ID: 31
Touches: `templates/squad/process/spawning.md` (SPAWN-4 phrase only, added 2026-10-22), `tests/test_sizes.py` (whole-template checks), `skills/squad-process-update/changelog.md` (one entry), snapshot tests that pin the template if any
Does not touch: rule files (fix a finding by returning to the owning ticket 17, 29 or 30)
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_sizes test_process_history test_squadupgrade test_squadruntime`
Blocked by: 30

# 31: New sizes, slice 4: whole-template checks and changelog

**Done when tests prove the whole template has no orphan duty and no pointer to an absent role at S and M, every duty has an owner per size, and the changelog lists every retargeted rule ID.**

## Technical AC
1. Role sets per size (S: manager, dev; M: + qa-whitebox, qa-blackbox; L: all; designer only with `design: yes`): for each present role at each size, the composed rules `act` on no absent role.
2. No orphan duty: for each size, every rule whose `when` matches acts on at least one present role; failing IDs listed in the message.
3. No pointer to an absent role: at S and M the composed text of manager, dev and the QAs does not name Tech Lead, Team Lead or BA as an actor; allow-list (by ID) only move-up and L-only rules.
4. `who` shows an owner per size for: plan and spawning, technical AC, business AC, code check, behaviour check, full suite, `promote.md`, migrations (moves to L), irreversible choice, hand-in target; the test fails when any has none.
5. Risk flags force L and a business doubt moves S or M to L (rule text test).
6. Changelog entry: every retargeted rule ID and why (test compares it to the diff of IDs against base 2e81e5e).
7. Evidence: list `size:` and `plugin:` of every `scopes/*/scope.md` and `goals/*/goal.md`; open legacy scopes noted; deploy order quoted from decision 9 of `tasks/tech-ac.md`.
8. The orphan and absent-role checks (AC2, AC3) enforce the full follow-up list in `tech-ac.md`: no allow-list entry beyond SIZE-17a-e and the move-up rules, each by ID with a reason.
9. QAw's orphan list from ticket 30 (`evidence/30/qa-w.md`): START-8 (qa-blackbox at S, goal), START-11 (ba), START-13 (qa-blackbox), START-14 (qa-whitebox), START-15 (team-lead), START-16 (tech-lead). Each is one role's own start card: composed only when that role exists, never at a size without it. Decision: list them in the allow-list by ID with the reason "role start card; role absent at this size, rule never composed", no `when` edit (starting.md is outside 31's Touches). Any other orphan found by the test fails the ticket and goes back to its owner.
10. SPAWN-4 (`spawning.md`, design yes, composed for the Manager at S and M) says "after the Tech Lead's plan names the UI tasks": reword to "the plan" (phrase only), no allow-list. SIZE-18 ("Add a second BA, Tech Lead or QA") may be allow-listed only if its `when` is `size = L` (never composed at S or M); if it is composed at S or M, fix its `when` in 31 instead (sizes.md added to Touches for that line only).
