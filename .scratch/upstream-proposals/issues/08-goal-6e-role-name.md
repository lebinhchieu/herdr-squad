# 08 GOAL-6e names a role the team may not have

Status: in progress (Developer, 2026-11-24; return 1)

Spec: `.scratch/upstream-proposals/spec.md`. Base: 07's final sha. This is a return of ticket 04 (a defect found after 04 passed).

## Problem

`tests/test_architect_handoff.py::RulesTest::test_size_text_stays_clean_for_an_absent_role` fails on the 06/07 branch and passes on c853707. GOAL-6e (`templates/squad/process/goal.md`, ticket 04) says "(the Tech Lead's table)". Through `aware: tech-lead, qa-whitebox` the rule reaches QA whitebox on a team with no Tech Lead, and the test forbids the name "Tech Lead" there. The phrase came from the plugin SQ-6 overlay op, and neither ticket 04's QA nor the Tech Lead's review ran this test.

## Change

In GOAL-6e only, replace "(the Tech Lead's table)" with "(the touched-files table in `tasks/`)". No other word, no change to `roles:`, `aware:` or `topic:`. The body stays under 60 words.

## Files (LC-9)

`templates/squad/process/goal.md` (GOAL-6e); `templates/squad/process/suites.md` (SUITE-7 split by suite owner, below); `skills/squad-process-update/changelog.md` (the v29 SUITE line); `tests/test_dev_rules_size.py` (`LIMIT` only if the sweep needs it). Why SUITE-7: it names "Tech Lead, else QA whitebox" and reaches QA whitebox on a team with no Tech Lead, but `duties:` exists only in the Manager, Team Lead and Tech Lead headers, so no role-neutral pointer works. Form (as SUITE-1/1b/2d): SUITE-7 `roles: tech-lead`, `when: suite-owner = tech-lead`; SUITE-7e `roles: qa-whitebox`, `when: suite-owner = qa-white`; both with the same body "You keep `$SQUAD_DIR/base-failures.md`, one row per test name, append only. Columns: test name, sha it fails on, one-line cause, first scope that saw it, fix ticket or the PO's keep. Create it on the first row."; SUITE-7f `roles: dev`, `when: suite-owner = dev`, body "You keep `$SQUAD_DIR/base-failures.md` as [SUITE-7] says; read it with `squad-process rule SUITE-7`." SUITE-7b gets the lead-in "If you keep the base-failures file ([SUITE-7]), " so QA whitebox does not run it when a Tech Lead owns the file. Ticket 02's AC1 is not rewritten: each owner's rules name the file, its columns and that it owns it; no role is named. The FILE-6 row keeps the chain. No test, no `bin/`, no version, no changelog (the v29 GOAL-6e line stays true), no `LIMIT` change (GOAL-6e does not reach the Developer).

## AC

- AC1: `python3 -m unittest test_architect_handoff` (from `tests/`) passes in full.
- AC2: `grep -rn "Tech Lead's table" templates` is empty.
- AC3: `test_rules_contract`, `test_rules_wording`, `test_squadcompose`, `test_sizes`, `test_dev_rules_size`, `test_promotion_0_6_0` pass; `python3 bin/squad-process lint` exits 0.
- AC4 (defect class, LC-8): no rule that reaches a team may name a role by its title unless that role is in the rule's `roles:` or its `when:` guarantees it. The Developer greps the rules added or edited by 01-06 (`git diff c853707 HEAD -- templates | grep '^+' | grep -n "Tech Lead\|QA whitebox\|QA blackbox\|BA\b\|Designer\|Architect"`) and quotes each hit with its `roles:`/`aware:` line; any hit that can reach a team without that role goes back to the Tech Lead before handin.
- AC5: `git diff <base> HEAD --stat` lists `goal.md`, `suites.md` and this ticket's evidence only.

## Comments

- Dev 2026-11-24, first try (ee9ef83): GOAL-6e edited; SUITE-7 pointed at the `duties:` line. QA whitebox followed up and QA blackbox FAILed: QA whitebox and a Developer owner have no `duties:` line.
- Tech Lead, DECISION 08 FINAL (return 1): SUITE-7 split by suite owner (SUITE-7, 7e, 7f); SUITE-7b gets the lead-in. Ticket 02's AC1 is untouched. My earlier note changing it is dropped.
- Dev: SUITE-7e's columns sentence is reworded ("Each row holds the test name, the sha it fails on, a one-line cause, the first scope that saw it, and the fix ticket or the PO's keep."), because `squad-process lint` rejects a sentence of 12+ words repeated across two rules. Same content, no role name.
- Dev: `LIMIT` in test_dev_rules_size 6950 -> 7050. Measured worst case 7002 B (team-lead+qa-black+designer+architect, goal yes, qa light), +48 B (SUITE-7f adds Developer bytes).
- Dev: changelog v29 SUITE line now "SUITE-7, 7b, 7c, 7d, 7e, 7f". It never mentioned "Tech Lead's table", so no GOAL-6e wording change.
- Dev checks, SQUAD_* unset: lint 0; test_architect_handoff, test_rules_contract, test_rules_wording, test_squadcompose, test_sizes, test_dev_rules_size, test_promotion_0_6_0, test_squadrules, test_instructions: 185 tests OK. `who` for SUITE-7 / 7e / 7f lists one `suite-owner` condition and one role each (tech-lead / qa-whitebox / dev).
- Dev AC4: `files.md:72` is in FILE-6 (`roles: manager`), unchanged. `evidence.md` EVID-2b has `roles: dev`, `when: tech-ac = tech-lead`, fine. The GOAL-6e hit is fixed.
