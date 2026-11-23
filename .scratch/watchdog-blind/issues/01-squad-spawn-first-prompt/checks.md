<!-- Save as $SCOPE_DIR/evidence/<NN>/checks.md. One row per AC; fill your own column with a command and its result (`-` if no such role). `## Review` points at `## Checks`. After every PASS: squad-evidence add <ticket> --heading Checks --from checks.md -->
| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_spawn` 115 OK (working_at_once) | cd tests; python3 -m unittest -q test_squad_spawn test_squad_respawn test_squad_start test_windows_safe test_utf8_helpers test_instructions (fc1babf: 241 OK; aa63f53: test_squad_spawn + SQ-10 files OK); read the agent_started diff |  |
| AC2 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; Enter only for idle/done (aa63f53), one send-keys asserted in the log |  |
| AC3 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; warning on stderr, exit 0, JSON status ready asserted |  |
| AC4 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; wait sits inside `if [[ -n $prompt ]]`; test_no_prompt_means_no_status_wait; blocked test added |  |
| AC5 | `python3 -m unittest test_squad_spawn` 115 OK (see Review trace) | same; tests (a)(b)(c) + blocked test read |  |
