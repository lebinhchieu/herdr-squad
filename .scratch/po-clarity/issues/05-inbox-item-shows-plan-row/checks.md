| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `test_squadboard_panels.Panels12.test_T05_AC1_AC2_plan_line_...`, `test_po_inbox_contract.PlanFieldTest.test_T05_3_...` (goal: scope 2 of 3 · aim · next: PI-08); shot `board-goal.png` | - | - |
| AC1b | `test_squadplan.InboxPlanTest.test_AC1b_...` (task 2 of 3 · step 2 · aim · next: t11); shot `board-scope.png` | - | - |
| AC2 | `PlanFieldTest.test_T05_2_...` (unknown, nothing, none, no table, unreadable: null); shot `board-goal.png` E4 has no line | - | - |
| AC3 | pane `item.test.ts` "05 plan line" and `core.test.ts` planLine, both in `claude plugin test` (652 pass); board `Panels12` test | - | - |
| LC-11 design states | board: `board-goal.png`, `board-scope.png`, `board-narrow.png`; pane: `pane-states.txt` (80 cols, 40 cols, no plan, done item) | - | - |
| T05-1 | `grep -rn "plan_line_parts" bin/` shows one builder; both surfaces read the `plan` field only | - | - |
| T05-2 | `PlanFieldTest.test_T05_2_...` | - | - |
| T05-3 | `PlanFieldTest.test_T05_3_...` (escalations.md bytes equal, no inbox.jsonl written, `plan` key on every item); contract byte test OK | - | - |
| T05-4 | `plugin.json` 0.11.0 = changelog v31 "Plugin 0.11.0"; `grep -rn '0\.10\.10' .claude-plugin skills`: only v28 history lines | - | - |
| T05-5 | `item.test.ts` "05 plan line" (one row more, dim, narrow cut) and `core.test.ts` cut order | - | - |
| T05-6 | SQ-10 trio and `test_po_inbox_mod` OK (see evidence.md) | - | - |
