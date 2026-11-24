# Evidence: 07 Designer settings test expects the /tmp allow
sha: 4945bca
## Behaviour
- Change: `tests/test_templates.py::test_designer_may_write_only_ui_design_files` lists four allows (`Edit(/.claude/squads/*/scopes/*/ui-design/**)`, `Edit(//tmp/**)`, `Write(/.claude/squads/*/scopes/*/ui-design/**)`, `Write(//tmp/**)`) with the comment "/tmp is open to every role (bd2563c, SAFE-11)". Sorted order differs from the ticket's list ('.' sorts before '/'); same four entries. Deny checks untouched; `designer.json` untouched.
- AC1: `cd tests && python3 -m unittest test_templates` -> `Ran 8 tests ... OK`.
- AC2: scratch copy under /tmp with `Write(//etc/**)` added to designer.json: `FAIL: test_designer_may_write_only_ui_design_files` ... `AssertionError: Lists differ: [... 'Write(//etc/**)', 'Write(//tmp/**)'] != [... 'Write(//tmp/**)']`, `-  'Write(//etc/**)',`. Scratch removed; nothing committed. (The scratch run also shows an unrelated ERROR from the missing repo docs in the copy.)
- AC3: diff lists `tests/test_templates.py`, the ticket and this evidence; no `templates/` file.
- AC4: test_templates 8 OK, test_squadsettings, test_team_lead_perms OK, test_architect_handoff and every `grep -l designer tests/test_*.py` hit run: 512 tests, 2 failures, both fail identically on base 39039b3 (my diff reverted) and neither imports test_templates: `test_architect_handoff::RulesTest::test_size_text_stays_clean_for_an_absent_role` ('Tech Lead' in a qa-whitebox S text) and `test_qab_optional::QabNo::test_qa_blackbox_rules_absent_in_who` (needs SQUAD_* env unset; the first still fails with it unset). Neither is in `base-failures.md`; sent to the Tech Lead to add (SUITE-7c).
- SQ-10 files (test_windows_safe, test_utf8_helpers): not run (no bin/ or printed text change); test_instructions ran as a `designer` hit, OK.
- AC5: `python3 bin/squad-process lint` exit 0.
- No full suite run (the Tech Lead runs --tz).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1-AC5 | `python3 -m unittest test_templates` OK 8; AC2 scratch copy fails on extra allow; lint 0 | `cd tests; python3 -m unittest test_templates`; scratch copy of 4945bca with `Write(//etc/**)` added to designer.json, rerun test_templates; `git diff --stat 39039b3 4945bca`; `python3 -m unittest test_squadsettings test_architect_handoff test_team_lead_perms` plus the `grep -l designer tests/test_*.py` hits; `python3 bin/squad-process lint` |  `cd tests; python3 -m unittest test_templates` (8 OK); `git diff 39039b3 HEAD --stat` (no `templates/` or `bin/` file); `python3 bin/squad-process lint` (exit 0); AC2 read from the Developer's quoted failure, not re-run |

## Review, QA whitebox

### QA whitebox, ticket 07, sha 4945bca

Verdict: PASS.

#### Checked
- AC1: `test_templates` 8 tests OK, none skipped or deleted (diff adds 4 lines, deletes 1, in `test_designer_may_write_only_ui_design_files` only; deny and respawn assertions kept; comment added).
- AC2 (run by me on a scratch copy of 4945bca under /tmp, removed after): `Write(//etc/**)` added to `designer.json` -> `FAIL: test_designer_may_write_only_ui_design_files`, `Lists differ ... 'Write(//etc/**)'`. The test still guards the allow list.
- AC3: `git diff --stat 39039b3 4945bca`: `tests/test_templates.py`, the ticket, its evidence and checks.md only; no `templates/squad/settings/` file, no rule, no `bin/`.
- AC4: test_templates, test_squadsettings, test_architect_handoff, test_team_lead_perms, and every `grep -l designer tests/test_*.py` hit run (SQUAD_* unset). Only failure: `test_architect_handoff::test_size_text_stays_clean_for_an_absent_role`, which fails identically on base 39039b3 (I ran it there), and the diff does not touch what it reads. The other 18 designer-hit files: 454 tests OK, test_qab_optional included.
- AC5: `squad-process lint` exit 0.

#### Follow-up (not FAIL)
- The Developer wrote that test_qab_optional fails on base; with `SQUAD_*` unset it passes here. It needs that env unset (known from ticket 06).

## Review, QA blackbox

### QA blackbox 07, sha 4945bca

Test-only ticket: the behaviour I can see is what the test run and the diff list show; I did not read the test code.

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 test_templates passes, 8 tests, none skipped | live | `cd tests && python3 -m unittest test_templates` in the worktree | `Ran 8 tests ... OK` | pass |
| AC2 test still fails on an extra designer allow | shot | read the Developer's quoted failure in evidence.md (`Write(//etc/**)` added in a scratch copy: `FAIL: test_designer_may_write_only_ui_design_files`, `-  'Write(//etc/**)',`; scratch removed, nothing committed) | clear failure line naming the extra entry; not re-run | pass (shot) |
| AC3 diff lists only the test and this ticket's files | live | `git diff 39039b3 HEAD --stat` | `tests/test_templates.py` (5 lines), the ticket, its evidence.md and checks.md; no file under `templates/` or `bin/` | pass |
| AC4 targeted tests | shot | Developer's evidence lists test_templates, test_squadsettings, test_team_lead_perms OK and two failures that also fail on base 39039b3 | tests are QA whitebox's | not mine |
| AC5 lint | live | `squad-process lint` | exit 0 | pass |

Follow-up (not FAIL, SQ-4): the two failures the Developer found on base (`test_architect_handoff::RulesTest::test_size_text_stays_clean_for_an_absent_role`, `test_qab_optional::QabNo::test_qa_blackbox_rules_absent_in_who`) are not in `base-failures.md`; the Developer says it sent them to the Tech Lead to add (SUITE-7c). The `--tz` run on 07's final sha must be clean per the ticket's Duties, so these two need a fix ticket or the PO's keep first.
