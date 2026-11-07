# 12 Promotion: evidence

## Behaviour

Docs only. `docs/adr/0021-task-state-events.md` is new; its text equals the fenced block of promote.md section 1 (AC1, checked with `diff`). `CONTEXT.md`: **Done** became **Passed**, new **Merged** and **Task event**, **Ready for review** entry and its relation line removed, the Task line now says **Passed** (AC2).

- `grep -n "Ready for review\|^\*\*Done\*\*" CONTEXT.md` prints nothing.
- `grep -rn "Ready for review" docs README.md CLAUDE.md` prints nothing (AC3).
- `grep -rl "CONTEXT.md\|docs/adr" tests/` hits only `tests/fixtures/board/t28/04.md`, a fixture no test edit touches; no test file reads the changed docs (AC4).
- `CONTEXT.md:189` (Task entry): `checking → done or returned.` became `checking → passed or returned, and a passed task is merged.` (Tech Lead ruling, promote.md section 2).
