# Evidence 02

## Behaviour
- New rules in `templates/squad/process/suites.md`: SUITE-7, SUITE-7b (tech-lead, qa-whitebox; aware team-lead), SUITE-7c (dev, qa-whitebox, qa-blackbox), SUITE-7d (manager). `files.md` FILE-6 row `base-failures.md`, owner: the suite owner (Tech Lead, else QA whitebox, else Developer).
- SUITE-7 names `$SQUAD_DIR/base-failures.md`, its five columns and the owner chain (AC1). `grep -n '_done' suites.md`: empty; SUITE-7d runs no test (AC2).
- `python3 bin/squad-process lint`: exit 0.
- Ticket text fixed: "the PO's keep", AC5 (no Chieu in rule text), Duties line.
- Developer bytes: worst no-designer/no-architect team 5473 -> 5759 B (+286 of 400 B budget); LIMIT 5580 -> 5866.
- Tests (cd tests; python3 -m unittest): test_windows_safe, test_utf8_helpers, test_instructions, test_rules_contract, test_small_files_equivalence, test_sizes: OK. test_dev_rules_size: only `test_every_team_set_fits_the_limit` fails, for design teams (e.g. ('designer',) 5978 B): known failing on base (tl-design §5), no FAIL.
