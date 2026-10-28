Status: ready-for-agent
Type: task
Task ID: 30
Touches: `tests/test_designer_handoff.py` (pin LC-11 to L, added 2026-10-22), `tests/fixtures/qab/golden.json`, `tests/test_suite_rules_process.py`, `templates/squad/process/core.md` (CORE-3), `templates/squad/process/{cost,messages,files,iterations,notes,goal,closing,safety}.md`, `bin/squad-log-message` (size routing: S and M to the Manager, L to the Team Lead), `tests/test_squad_ledger.py`, `test_squad_log_message.py`, `test_manager_m_l.py`, `test_pod_rules_process.py`, `test_dev_rules_size.py`, `test_squadcompose.py` (size matrix)
Does not touch: files of 17, 29, 31; `LIMIT` in `test_dev_rules_size.py` stays 5120
Harness: `squad-process lint`; `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <each edited test file> test_sizes test_dev_rules_size`
Blocked by: 29, 18 (shares `cost.md`, `squad-log-message`; base must contain passed 18, which already edited NOTE-1 `roles:` in `notes.md` and `test_dev_rules_size.py`: start from that, no clash)

# 30: New sizes, slice 3: cost, messages, files, iterations, notes, goal, closing, safety

**Done when every rule in these eight files and the log-message routing name an owner present at the size, and the composed Developer rules still fit 5120 B at every size, design and goal.**

Owner table: `scopes/sizes-and-models/tasks/tech-ac.md` decision 3; never renumber, no `(S:` clauses.

## Technical AC
1. `squad-log-message` routes by size: S and M messages and notices go to the Manager, L to the Team Lead; test per size.
2. Files table (`files.md`): at S and M no `tasks/<id>.md` owner is the Tech Lead; `promote.md`, iteration summary and plan owners follow the table (S, M: Manager plans; Developer task file holds design notes).
3. Cost, safety, closing, goal and notes rules name no absent role as actor at S or M (allow-list: move-up rules, by ID).
4. `test_dev_rules_size.py`: composed dev rules ≤ 5120 B at all 12 combinations; if over, move a rule out of dev's compose (still one `squad-process rule <ID>` away), never raise LIMIT.
5. Pinned tests edited in the same commit; lint clean; `test_windows_safe` passes.
6. Every ID listed for 30 in `tech-ac.md` "Follow-up rule IDs" is retargeted or reasoned; the true orphans among them (MSG-4a at S, COST-4a, GOAL-2/3a, CLOSE-3a) are fixed. The test lists any `who`-orphan left in these eight files.
7. Added 2026-10-22 (QAb on 29, updated after 29 @626bdce): COST-5/5a and MSG-11a/11b were retargeted in 29 (re-check only, do not undo; START-6/START-10 trims stay). Left for 30: CORE-3 (`core.md`) at S and M, and MSG-4b at M (Team Lead absent at M: Manager variant). Test: composed dev and QAs at S and M name no Tech Lead, Team Lead or BA as actor; dev rules stay ≤ 5120 B.
9. MSG-3 (Task ID line, `messages.md`) lost "never paste them" in 29's byte-saving rewording: restore that meaning (a shorter wording is fine), keep dev ≤ 5120 B, and add a test that MSG-3 in composed dev says it.
10. `test_designer_handoff` passes: 29 made LC-11 L-only (pin broke; not a pre-existing failure). Pin the tech-lead assertions to L; the M design check goes through LC-11b.
11. At S the 3-returns notice (`bin/squad-log-message`, LC-7 text) must not tell the Manager to send `BLOCKED` to itself: at S and M the notice goes to the Manager and says to record the budget line and consult the advisor [LC-25]; only at L does it say `BLOCKED <task>: 3 returns` to the Team Lead. Test per size.
