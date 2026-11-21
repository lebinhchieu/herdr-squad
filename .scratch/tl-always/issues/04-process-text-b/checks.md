<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | lint exit 0; grep empty | - | - |
| AC2 | grep hits only tombstones/changelog/fixtures | - | - |
| AC3 | test_rules_contract OK | - | - |
| AC4 | test_rules_contract OK | - | - |
| AC5 | test_squad_usage_hook OK | - | - |
| AC6 | windows_safe, utf8_helpers, instructions OK | - | - |
| AC7 | test_dev_rules_size OK | - | - |
| AC8 | 88 targeted tests OK | - | - |
