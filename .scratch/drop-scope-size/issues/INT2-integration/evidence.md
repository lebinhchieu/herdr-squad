# Evidence: INT2 integration of 04 + 10 + 06
base 6389642 (INT1); merged in order: 04 (14847ad), 10 (f8af869), 06 (9620c7e). 07 deliberately not merged (INT3).

## Behaviour
- 04 and 10 merged without conflicts.
- 06: one conflict, `skills/squad-process-update/changelog.md` v9 appends. Resolved by keeping both sides: 10's `TEAM-7 ... runs \`squad-team remove\`` (the fuller line replaces 06's shorter TEAM-7) plus 06's WHO-1c, WHO-1d, WHO-1e, WHO-2f. No markers left.
- No code or test edits beyond that resolution; no stale-test fix was needed.
- Tests on merged result: test_squad_migrate 20 OK; tests/test_instructions.py 30 OK; test_squad_team 26 OK; test_squad_spawn 87 OK. `squad-process lint`: exit 0, empty.
- Full suite not run by me (Tech Lead owns it, `--if-changed 6389642`).
