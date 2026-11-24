# Evidence: 08 watchdog herdr gap

## Behaviour

Method: `cd tests && python3 -m unittest test_squad_watchdog` (no screen involved).

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | the new test; then deleted the new line in `bin/squad-watchdog` and re-ran | with the line: pass. Without it: `FAILED (failures=1)`, a suspend at the first quiet check after the outage |
| AC2 | the new test timeline: quiet at 0 and 4 min, herdr down at 10, back at 11, ticks at 15 and 16 | no suspend at 11 or 15; one suspend at 16 (5 min after 11) |
| AC3 | `python3 -m unittest test_squad_watchdog`; `grep -rl 'quiet_since\|squad-watchdog' tests/` | `Ran 15 tests ... OK`; only `tests/test_squad_watchdog.py` matches |
