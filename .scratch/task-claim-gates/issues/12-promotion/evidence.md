# 12 Promotion: evidence

## Behaviour

Docs only. `docs/adr/0021-task-state-events.md` is new; its text equals the fenced block of promote.md section 1 (AC1, checked with `diff`). `CONTEXT.md`: **Done** became **Passed**, new **Merged** and **Task event**, **Ready for review** entry and its relation line removed, the Task line now says **Passed** (AC2).

- `grep -n "Ready for review\|^\*\*Done\*\*" CONTEXT.md` prints nothing.
- `grep -rn "Ready for review" docs README.md CLAUDE.md` prints nothing (AC3).
- `grep -rl "CONTEXT.md\|docs/adr" tests/` hits only `tests/fixtures/board/t28/04.md`, a fixture no test edit touches; no test file reads the changed docs (AC4).
- `CONTEXT.md:189` (Task entry): `checking → done or returned.` became `checking → passed or returned, and a passed task is merged.` (Tech Lead ruling, promote.md section 2).

## QA blackbox

### QA blackbox 12 (sha 87e10b8), docs only. Method: live (read the two docs; ran the ticket's greps)

| Check | What I saw | Result |
|---|---|---|
| `grep -n "Ready for review\|^\*\*Done\*\*" CONTEXT.md` | nothing | pass |
| New entries | **Passed**, **Merged**, **Task event** present; they match the board words (passed = every QA PASS on current sha, or evidence check exit 0 with no QA; merged = branch in `main`) and the states.md decisions (no confirmer, warn gates) | pass |
| `grep -rn "Ready for review" docs README.md CLAUDE.md` | nothing | pass |
| ADR 0021 | reads as promote.md s1 (spot check); states no confirmer, derived words, `squad-task`, warn-only | pass |
| Reader check vs states.md s9 / R3 | CONTEXT.md line 189 (Task entry) still reads `checking → done or returned` | follow-up |

Follow-ups (not fails; promote.md did not ask for line 189, and R3 names the process text, board, Inbox, `squad-task` output, hook warnings):
- CONTEXT.md:189 Task entry: change `done` to `passed` (as CORE-1 now says). Line 89 "before it is done" and 181 are plain prose.

Verdict: PASS.

## QA whitebox

### QA whitebox 12 (final sha 715d183): PASS
- AC1: first fenced block of promote.md vs docs/adr/0021-task-state-events.md (script compare): equal. Unchanged since 87e10b8 (715d183 touches only CONTEXT.md:189 and evidence.md).
- AC2: `git diff d906cff 87e10b8 -- CONTEXT.md`: Done->Passed, new Merged and Task event, Ready for review entry and its relation line removed, Task relation line fixed; wording equals promote.md s2. `grep -n "Ready for review\|^\*\*Done\*\*" CONTEXT.md`: empty. One extra line, CONTEXT.md:189 (Task entry "checking -> passed or returned, and a passed task is merged"), is the Tech Lead's DECISION, not a finding.
- AC3: `grep -rn "Ready for review" docs README.md CLAUDE.md`: empty.
- AC4: `grep -rl "CONTEXT.md\|docs/adr" tests/` -> tests/fixtures/board/t28/04.md only (fixture; no test reads the docs). No test to run.
- AC5: `squad-evidence check .scratch/task-claim-gates/issues/12-promotion`: ok, rc 0 on 715d183.
- Diff outside CONTEXT.md, docs/adr, .scratch: empty. PROMO-8: edits match promote.md, nothing undecided added.
Follow-ups (not blocking): CONTEXT.md:89 Checker still says "the code-check owner confirms the Developer's evidence" (conflicts with "No role confirms it" in Passed); CONTEXT.md:266 "tasks done" in the dashboard home entry.

## Tech Lead review

### 12 Tech Lead review (HANDIN 715d183)
- AC1 OK: docs/adr/0021-task-state-events.md equals the fenced block of promote.md section 1 (script compare, True).
- AC2 OK: greps clean; Passed (196), Merged (200), Task event (203) present. CONTEXT.md diff 87e10b8->715d183 = line 189 only (ruled in scope, ASK 12).
- AC3 OK for docs, README, CLAUDE. Words "ready for review" remain only inside two test comments/asserts (tests/test_squadboard_tasks.py:74-76, test_squadboard_panels.py:533) that say the key is gone: fine.
- AC4 OK: only tests/fixtures/board/t28/04.md names CONTEXT.md; no test reads the changed docs.
- AC5 OK: evidence check exit 0 with --base 715d183. QAs passed 87e10b8 earlier, so a verdict on 715d183 is still owed.
- Line 379 in the Dev message = the relation line I called 377 (shifted by the deleted entry): correct.
