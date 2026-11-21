<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | test_squadrules TeamLeadImplicitTest OK | - | - |
| AC2 | test_squadrules TeamLeadImplicitTest, test_team_duties OK | - | - |
| AC3 | test_squadrules old-key test (plan-owner, team-lead rows) OK | - | - |
| AC4 | test_squadupgrade test_removed_team_lead_conditions... OK | - | - |
| AC5 | test_squad_team test_team_lead_is_always_on_the_team OK | - | - |
| AC6 | grep over bin/ templates/ agents/ hooks/ skills/ empty but pointers; lint exit 0 | - | - |
| AC6b | grep `handin-target = manager` templates/ empty; lint exit 0 | - | - |
| AC7 | `squad-process who MSG-5 / WHO-1e`: 0 hits | - | - |
| AC8 | test_dev_rules_size, test_squadcompose, test_sizes OK | - | - |
| AC9 | windows_safe, utf8_helpers, instructions OK | - | - |
| AC10 | 284 targeted tests OK | - | - |
