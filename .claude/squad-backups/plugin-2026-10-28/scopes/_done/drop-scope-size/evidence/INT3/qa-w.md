# QA whitebox INT3 on 32aa75b
PASS. Merge of 07 (0067a5d) + 08 (e08bb66) onto fed0c95.
- Run from `git archive 32aa75b`: test_squad_migrate 20, test_instructions 30, test_sizes 34 (2 skip), test_dev_rules_size 9 (3 skip), test_process_conversion 14, test_pod_contact_routes 7, test_qab_optional 11, test_architect_handoff + test_manager_m_l + test_pod_rules_process + test_suite_rules_process + test_team_lead_role 61: all OK. `squad-process lint` exit 0, empty. No conflict markers.
- Tree: 08-only process files (cost, messages, safety, spawning, suites) byte-identical to 08; 07-only files identical to 07. Changelog: every line 07/08 added is present except 2 shorter TEAM-7/SIZE-13 lines, which base's extended versions (with `runs squad-team ...`, lines 11, 32) supersede.
- Stale-test fixes (7a66ae4) match the MSG-11b wording and the `qa-black = no/yes` who lines.
- Skips: 3 in test_dev_rules_size + 1 in test_sizes are 07's "5 KiB trim is ticket 11"; with skips removed they fail (S 5196 B, M-arch 5124 B > 5120; pins 5438/5437/5147/5146 vs real 5522/5521/5226/5225). Not an INT3 defect: ticket 11 owns the trim, un-skip and re-pin. 08's un-skipped run state is gone only because 07 skips them; both stay open for 11.
- Forward note for 11: un-skip all 4 and re-pin PINNED to the post-trim sizes; the pins in the file are stale now.
- Full suite `--if-changed fed0c95` is the Tech Lead's; final sha not named by the Tech Lead before my verdict, so this verdict is on 32aa75b (re-check on any later sha).

## Re-check on 027f238 (LC-3b)
PASS. Only change vs 32aa75b: tests/fixtures/rules/compose/.../review.md +13 lines (REV-14a, REV-19b stubs, roles/topic/when well-formed). test_squad_migrate, test_instructions, test_sizes, test_dev_rules_size, test_process_conversion: 107 OK (5 skip, same as before); lint exit 0. Valid as the verdict if the Tech Lead names 027f238 final.

## Re-check on 90be196 (LC-3b)
PASS. Diff vs 32aa75b: tests/test_squadruntime.py +5 (make_plugin appends REV-14a/REV-19b stubs to its copy of the fixture review.md; stubs well-formed, same shape as 027f238's fixture stubs which this sha drops) and the evidence note. test_squadruntime + test_squad_migrate, test_instructions, test_sizes, test_dev_rules_size, test_process_conversion: 171 OK (5 skip, unchanged); lint exit 0. make_plugin only used in test_squadruntime.
