# 02: Ticket status reader takes `State:`

Status: ready-for-agent
Duties: design notes = Developer (this file, ## Design notes); technical AC = QA whitebox with the Developer; business AC = this ticket; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; suite and promote.md = QA whitebox; no full suite without Chieu's yes
Files: bin/squadtickets.py, tests/test_squadtickets.py
Test harness: tests/test_squadtickets.py (fixture task files)
Ticket path (commit by the first Developer task, FILE-11): `.scratch/watchdog-blind/issues/02-*.md`; evidence next to it.

Seen: Team Leads write task files with `State: ready` (not `Status:`). `squadtickets.status_of` reads only `Status:`, so 52 of 83 tickets of the guardian goal read status '' and the watchdog's ticket-based idle check never fires; the board shows them empty too.

## AC
1. `status_of` returns the `State:` value, normalised exactly like `Status:` (first word, `handed in` / `in progress` phrases, lowercase), when the first 12 lines hold no `Status:` line.
2. A file with both lines: `Status:` wins.
3. Tests in `tests/test_squadtickets.py`: `State: ready (no Developer...)` -> `ready`; `State: handed in (5bc3126); ...` -> `handed in`; both lines -> Status value. Existing tests and every `grep -rl squadtickets tests/` hit stay green.
4. Glossary/ADR: none needed unless `CONTEXT.md` defines the `Status:` line; if it does, note `State:` as an accepted alias there.

## Rules for this ticket
- Proof runs only in a scratch squad (temp dir, stub `claude` and herdr, as `tests/test_squad_start.py` / the named test file). Never run `squad-watchdog tick|run|ensure` or `squad-spawn` against `/home/chieule/workspace/wpw` (live guardian agents get messages).
- [SQ-10] Any `bin/` edit: also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`; quote the result in `## Behaviour`.
- CLAUDE.md: run `grep -rl` over `tests/` for each touched path or changed printed string and run every hit.
- [SQ-2] `## Review` starts with an AC trace; quote `squad-evidence checks` exit code in HANDIN.

## Technical AC (QA whitebox, agree with the Developer here; written before work, 2026-11-23)
T1. One normalising path: `status_of` finds `Status:` first, then `State:`, over the same first 12 lines, and both go through the same phrase/first-word code (no copy of it). `Status:` wins even when `State:` comes on an earlier line.
T2. Anchored: only a line that starts `State:` counts (`^State:`), not `Statement:`, `Estate:`, or an indented/bulleted `- State:`. One test line for a false friend is enough.
T3. Empty `State:` value, `State:` with `Status:` empty: `Status:` line present (even empty) wins, returns ''. State this choice in `## Design notes` and test it in one line.
T4. Callers: `grep -rn "status_of" bin/ tests/` listed in `## Design notes` with a line each saying the new `State:` reading is right there (watchdog, board, ledger, anything that WRITES the status must not start writing `State:`). Every `grep -rl squadtickets tests/` hit runs green.
T5. REV-6 field shape: a fixture run of `squadtickets` over a task file set with mixed `Status:`/`State:` returns a non-empty status for every row (the 52-of-83 symptom), shown by one test over a folder, not only per-string.
T6. AC 4: `CONTEXT.md` line ~220 mentions the ticket `Status:` word; Developer decides in `## Design notes` whether it defines the line; say yes/no with the line number. SQ-10 three files run and quoted; no new skips.

## Design notes
`status_of` scans the first 12 lines for `Status:` first, then for `State:`, with one shared normaliser. So `Status:` wins even when `State:` comes first. `CONTEXT.md` does not define the `Status:` line (line 220 only says passed is never read from it), so no glossary edit.
