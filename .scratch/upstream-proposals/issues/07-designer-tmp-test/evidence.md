# Evidence: 07 Designer settings test expects the /tmp allow
sha: (see HANDIN)
## Behaviour
- Change: `tests/test_templates.py::test_designer_may_write_only_ui_design_files` lists four allows (`Edit(/.claude/squads/*/scopes/*/ui-design/**)`, `Edit(//tmp/**)`, `Write(/.claude/squads/*/scopes/*/ui-design/**)`, `Write(//tmp/**)`) with the comment "/tmp is open to every role (bd2563c, SAFE-11)". Sorted order differs from the ticket's list ('.' sorts before '/'); same four entries. Deny checks untouched; `designer.json` untouched.
- AC1: `cd tests && python3 -m unittest test_templates` -> `Ran 8 tests ... OK`.
- AC2: scratch copy under /tmp with `Write(//etc/**)` added to designer.json: `FAIL: test_designer_may_write_only_ui_design_files` ... `AssertionError: Lists differ: [... 'Write(//etc/**)', 'Write(//tmp/**)'] != [... 'Write(//tmp/**)']`, `-  'Write(//etc/**)',`. Scratch removed; nothing committed. (The scratch run also shows an unrelated ERROR from the missing repo docs in the copy.)
- AC3: diff lists `tests/test_templates.py`, the ticket and this evidence; no `templates/` file.
- AC4: test_templates 8 OK, test_squadsettings, test_team_lead_perms OK, test_architect_handoff and every `grep -l designer tests/test_*.py` hit run: 512 tests, 2 failures, both fail identically on base 39039b3 (my diff reverted) and neither imports test_templates: `test_architect_handoff::RulesTest::test_size_text_stays_clean_for_an_absent_role` ('Tech Lead' in a qa-whitebox S text) and `test_qab_optional::QabNo::test_qa_blackbox_rules_absent_in_who` (needs SQUAD_* env unset; the first still fails with it unset). Neither is in `base-failures.md`; sent to the Tech Lead to add (SUITE-7c).
- SQ-10 files (test_windows_safe, test_utf8_helpers): not run (no bin/ or printed text change); test_instructions ran as a `designer` hit, OK.
- AC5: `python3 bin/squad-process lint` exit 0.
- No full suite run (the Tech Lead runs --tz).
