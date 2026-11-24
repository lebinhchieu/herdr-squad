# 08 GOAL-6e names a role the team may not have

Status: in progress (Developer, 2026-11-24)

Spec: `.scratch/upstream-proposals/spec.md`. Base: 07's final sha. This is a return of ticket 04 (a defect found after 04 passed).

## Problem

`tests/test_architect_handoff.py::RulesTest::test_size_text_stays_clean_for_an_absent_role` fails on the 06/07 branch and passes on c853707. GOAL-6e (`templates/squad/process/goal.md`, ticket 04) says "(the Tech Lead's table)". Through `aware: tech-lead, qa-whitebox` the rule reaches QA whitebox on a team with no Tech Lead, and the test forbids the name "Tech Lead" there. The phrase came from the plugin SQ-6 overlay op, and neither ticket 04's QA nor the Tech Lead's review ran this test.

## Change

In GOAL-6e only, replace "(the Tech Lead's table)" with "(the touched-files table in `tasks/`)". No other word, no change to `roles:`, `aware:` or `topic:`. The body stays under 60 words.

## Files (LC-9)

`templates/squad/process/goal.md` only. No test, no `bin/`, no version, no changelog (the v29 GOAL-6e line stays true), no `LIMIT` change (GOAL-6e does not reach the Developer).

## AC

- AC1: `python3 -m unittest test_architect_handoff` (from `tests/`) passes in full.
- AC2: `grep -rn "Tech Lead's table" templates` is empty.
- AC3: `test_rules_contract`, `test_rules_wording`, `test_squadcompose`, `test_sizes`, `test_dev_rules_size`, `test_promotion_0_6_0` pass; `python3 bin/squad-process lint` exits 0.
- AC4 (defect class, LC-8): no rule that reaches a team may name a role by its title unless that role is in the rule's `roles:` or its `when:` guarantees it. The Developer greps the rules added or edited by 01-06 (`git diff c853707 HEAD -- templates | grep '^+' | grep -n "Tech Lead\|QA whitebox\|QA blackbox\|BA\b\|Designer\|Architect"`) and quotes each hit with its `roles:`/`aware:` line; any hit that can reach a team without that role goes back to the Tech Lead before handin.
- AC5: `git diff <base> HEAD --stat` lists `goal.md` and this ticket's evidence only.

## Comments

- Dev 2026-11-24: GOAL-6e edited as specified. Lint 0; test_rules_contract, test_rules_wording, test_squadcompose, test_sizes, test_dev_rules_size, test_promotion_0_6_0 pass. AC2 grep empty.
- Dev: AC1 still fails on `('qa-whitebox','S','Tech Lead')`: SUITE-7 (`suites.md:121`, `roles: tech-lead, qa-whitebox`, no `when:`) names the Tech Lead. AC4 hit; sent to the Tech Lead as ASK 08. Other AC4 hit: `files.md:72`.
- Tech Lead, DECISION 08 FINAL: option (a). Files widened to `suites.md` (SUITE-7 only). SUITE-7's first sentence now points at the `suite-owner` in the `duties:` line; the owner chain stays in the FILE-6 row (`files.md:72`, `roles: manager`). This changes ticket 02's AC1 ("names its owner chain") to "the chain is in the FILE-6 row, the rule points at the `duties:` line".
- Dev: AC1 passes now (11 tests). Also pass: test_rules_contract, test_rules_wording, test_squadcompose, test_sizes, test_dev_rules_size, test_promotion_0_6_0, test_squadrules, test_instructions. Lint 0. AC2 grep empty. SUITE-7 body 57 words.
- Dev AC4 hits: `suites.md` SUITE-7 (`roles: tech-lead, qa-whitebox`, no `when:`) fixed. `files.md:72` is in FILE-6, `roles: manager`: the Manager only, left as the Tech Lead ruled. `evidence.md` EVID-2b (`roles: dev`, `when: tech-ac = tech-lead`): the role is guaranteed, fine. The goal.md GOAL-6e hit is the fix itself.
