# 04 Promotion: evidence

Note: ADR 0032 amends ADR 0010 and the "Developers only" sentence of ADR 0030; neither is edited. Not merged yet.

## Review

AC trace (details in `## Checks`):
- AC1 | `ls docs/adr | grep -c 0032` | prints 1 (base 0)
- AC2 | `grep -n "spawns and retires only Developers\|spawns and retires the Developers\|spawns Developers," CONTEXT.md` | no hit (base 3); Pod entry checked, left alone
- AC3 | `git diff --stat <03 evidence sha>..HEAD` | only ADR 0032, CONTEXT.md, this folder
- AC4 | `grep -n "squad-respawn" docs/adr/0032-team-lead-spawns-the-pod.md` | 1 hit; Consequences name name-vs-row check and pin 0.10.4
- AC5 | `cd tests; python3 -m unittest test_old_language_inventory` | 2 tests OK; `grep -rl "CONTEXT.md\|docs/adr" tests/` hits only tests/fixtures/board/t28/04.md (a fixture, not a test)
- AC6 | read ADR Known-limit lines | the two limits of promote.md, verbatim

## Behaviour

ADR text is promote.md section 1 verbatim; the three CONTEXT.md entries (Manager, Team Lead, Coordinator) carry section 2 wording. SQ-10 needs no run (no bin/, printed text or role text edited).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | count 1 | | |
| AC2 | no hit | | |
| AC3 | diff stat lists 3 paths | | |
| AC4 | grep 1 hit | | |
| AC5 | inventory 2 OK | | |
| AC6 | verbatim | | |
