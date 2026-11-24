## Behaviour

Run: `cd tests && python3 -m unittest test_squad_watchdog` -> `Ran 18 tests ... OK`.

- AC1: `test_the_pc_sleeps_after_5_quiet_minutes_with_open_tickets...` and the `passed` test: suspend count 1 after 5 quiet min.
- AC2/AC3: log tail asserted: `sleep pc: all tickets passed; nobody on this machine has worked for 5 min` and `sleep pc: team idle with open tickets; ...`. Switch is off after (one shot, tick(40) no second suspend). Log-before-switch order kept by the existing env-command test (passes).
- AC4: `test_a_working_agent_resets_the_quiet_timer...`, `test_the_pc_never_sleeps_with_the_switch_off...`, existing herdr-outage tests.
- AC5: `sleep on` output and docstring changed; existing CLI test passes.
