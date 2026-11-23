<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_spawn` 115 OK (working_at_once) |  |  |
| AC2 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC3 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC4 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
| AC5 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) |  |  |
