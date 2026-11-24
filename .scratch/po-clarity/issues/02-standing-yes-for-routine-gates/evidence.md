# 02 evidence

## Behaviour
Rule text only; no UI. New rule `ITER-19 Routine gates` (roles: manager) holds the 5-row gate table, the `[info] <scope> closed|started; say undo` `read` notice, the non-blocking full-suite ask (`--blocks ""`), and "with `away` set nothing here changes ([ITER-17])".

Changed to match: `ITER-11`, `ITER-5` (check-in item), `CLOSE-1`, `CLOSE-3b`, `GOAL-1`, `GOAL-6b`, `SUITE-1`, `SUITE-1b`, `SUITE-2d`, `SUITE-3`, `SUITE-3b`, repo `CLAUDE.md` "Running tests". `ITER-17` has no hunk. `grep -rn "PO confirms the close\|PO said yes\|and the PO's yes" templates agents CLAUDE.md` finds nothing left. `agents/` had no hit.

Not changed: `ITER-4` (already allows `--blocks ""`). Version not bumped (rides 05); changelog bullets added under a new `## v29` heading, no version line (05 writes it).

Tests (SQUAD_* unset, targeted): `bin/squad-process lint` exit 0; `test_rules_wording` (31, incl. the new `RoutineGatesTest`), `test_instructions`, `test_rules_contract`, `test_processlint`, `test_windows_safe`, `test_utf8_helpers`, `test_small_files_equivalence`, `test_sizes`: OK.
Known failing on base: `test_dev_rules_size::test_every_team_set_fits_the_limit` (5692 B > 5580 on 5c0d5cd; with this change 5689 B, no growth).
