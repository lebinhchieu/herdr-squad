## Behaviour
Rule text and docs no longer describe `touches` or the overlap stop: START-3 has two steps, GOAL-1 has no `--touches` or `--yes` line, FILE-6's `scope.md` row has no `touches:`, START-19 keeps "what each depends on", SKILL.md and README.md lose the option, the exit-3 bullet and the "ask what the work touches" sentence.

`python3 bin/squad-process lint`: exit 0 before (clean copy of bd83778) and after.

Left on purpose (other senses of the word, not the removed feature):
- CONTEXT.md:209, 227: "touches" as a verb about the evidence commit.
- starting.md:17, 19, 201, lifecycle.md, sizes.md, merge.md, suites.md: "touched files" in Developers' design notes and test rules.
- cost.md: respawn-words scope's file, not edited here.
- README.md:55 `--yes`: it is `squad-process upgrade --yes`.

Tests (from `tests/`, targeted, no full suite):
- `python3 -m unittest test_templates test_processlint test_instructions test_rules_wording test_sizes test_small_files_equivalence test_squadupgrade test_squadcompose test_windows_safe test_utf8_helpers test_squad_start test_team_models test_dev_rules_size`: 271 tests OK.
- `python3 -m unittest test_templates test_squadrules test_rules_contract test_promotion_0_6_0 test_ca_install test_squadsettings test_team_duties test_squad_path_guard test_squadruntime test_squad_report_query`: 240 tests OK.
- SQ-10 files (test_windows_safe, test_utf8_helpers, test_instructions) are in the first run: pass.
