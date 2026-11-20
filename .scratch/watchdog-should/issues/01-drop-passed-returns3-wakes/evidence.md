## Behaviour

`squad-watchdog tick` on a scratch scope (stub herdr json, `--now` 08:00 then 08:01): ticket 03 goes `building` -> `passed`, with 3 FAIL records in `messages.jsonl`. Real `send` was in use, so any wake would have called `herdr agent prompt`.

```
$ squad-watchdog tick ... --now 2027-01-15T08:00:00Z     # building
$ squad-watchdog tick ... --now 2027-01-15T08:01:00Z     # passed, 3 returns
$ cat watchdog.log
cat: .../watchdog.log: No such file or directory          # no wake line, no line at all
$ cat watchdog.state.json
{"quiet_since": null, "wake_blocked": {}, "wake_sent": [], "beat": 1800000060.0, "pid": ...}
```

`grep -n -i "passed\|3rd return\|returns3" bin/squad-watchdog README.md`: the only hits left are the unrelated sleep reason `all tickets passed`, the `passed_keys` docstring and the snapshot `passed` field.

Tests (targeted): `test_squad_watchdog` 44 OK (46 - 3 + 1); `test_squad_log_message` 25 OK; `test_squadtask` 15 OK; `test_squad_start` 49 OK; `test_ca_autoswitch` 58 OK; `test_windows_safe` 14 OK; `test_utf8_helpers` 14 OK; `test_instructions` 16 OK. `test_ca_launchers` 86: 1 error in `test_scripts_are_syntactically_valid_bash` (reads an external `SRC/bin` file, not touched by this diff; 3 skips as before).

## Review

AC trace: see `## Checks`.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 -m unittest test_squad_watchdog.WakeTest.test_a_ticket_that_passes_or_returns_three_times_sends_and_logs_nothing`: OK |  |  |
| AC2 | `python3 -m unittest test_squad_watchdog.WakeTest` (blocked, held and retry tests): OK |  |  |
| AC3 | `grep -n -e RETURNS_WAKE -e ledger_rows -e sha_text -e wake_status bin/squad-watchdog`: only the `pop` of `wake_status`; old-state test OK |  |  |
| AC4 | `grep -n -i -e passed -e "3rd return" -e returns3 bin/squad-watchdog README.md`: only unrelated hits (see Behaviour) |  |  |
| AC5 | `python3 -m unittest test_squad_watchdog`: 44 OK, no skip |  |  |
| AC6 | tick capture in `## Behaviour`: no log, nothing sent |  |  |
