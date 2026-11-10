# Evidence: 09 One check table per ticket

## Behaviour
- `squad-evidence checks --template` prints a comment line, the header, the separator and an empty AC1 row; with a filled Dev cell it passes `checks`, empty it exits 1.
- `squad-evidence checks <file>`: exit 0 ok, 1 problems (`file:line: AC2: empty Dev cell`), 2 usage.
- `squad-evidence check <folder>` with a `## Checks` section also wants every QA cell filled (`-` allowed); no section: unchanged. `squad-evidence check` on the evidence of tickets 01, 02, 03 exits 0 (04, 05, 07 are not on this branch).
- Rules: EVID-9 (Developer), EVID-9b (QAs, `## Review` points at `## Checks`), EVID-9d (Manager, no QA), EVID-9c/9e (`tech-ac = dev and qa-black = yes`: Developer assembles, Manager accepts); lint exit 0.

## Review
The check table is `## Checks` (`$SCOPE_DIR/evidence/09/checks.md`). Developer rule bytes: sweep max 5358 B before, 5433 B after; LIMIT 5400 -> 5440 (Tech Lead ANSWER 09, ceiling 5480).

## Hand-off for the Manager
After merge and re-pin: remove SQ-2 from `process.local.md` and add the `process-log.md` row (WHO-6).
