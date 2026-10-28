# Notes: plugin-dev-add-architecture-1 (ticket 01, done)
- 01 passed both QAs at 67e0d05; evidence sha 30de602 on branch squad/plugin/add-architecture/plugin-dev-add-architecture-1.
- Facts header prints `architecture yes` only when on (absent/no byte-identical; Manager FINAL). Always printing breaks 5 KiB dev budget tests and qab golden.
- Left for task 02: agents/architect.md, templates/squad/settings/architect.json, process rules (`arch` short in starting.md, `when: architecture = yes` rules). `architect` already in ROLES, spawn lists, ROLE_FILES, label.
- Test quirk: tests importing `rulesview` (test_sizes, test_qab_optional, test_dev_rules_size, etc.) run via `cd tests; python3 -m unittest test_x`; others via `python3 -m unittest tests.test_x`. No pytest installed.
