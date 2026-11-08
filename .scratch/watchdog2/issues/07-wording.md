# Task 07: three wording fixes in the promoted docs

Duties: design notes: Developer (here); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (the goal's was committed in task 06; this task only corrects wording in those files). Full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag or doubt: `BLOCKED 07`.

Status: ready
Source: Chieu's answer E4 (a) (chat, 2026-11-08); QA whitebox follow-ups in `scopes/wd2-pane/evidence/06-qa-w.md` and the Developer's note on 06. Read only those, the three files below.
Files: `README.md` (row `bin/squad-watchdog`, line ~46), `docs/adr/0022-sleep-when-idle-and-away-mode.md`, `.scratch/watchdog2/issues/06-promotion.md`, `CONTEXT.md` only if a term repeats the wrong claim (grep first).
Ticket: commit this file's content as `.scratch/watchdog2/issues/07-wording.md` in your first commit.
Base: the task 06 passed sha 249bcad (branch `squad/plugin/wd2-pane/plugin-dev-wd2-pane-1`); reuse its worktree (no parallel task). Repo: /home/chieule/workspace/squad.

## AC
- AC1 ADR 0022 `## Context`: delete the clause "and the watchdog ran as a hidden detached process the PO could not see or stop" (it is not a decided fact). The sentence keeps its other facts and still reads correctly.
- AC2 README row and ADR Decision: say the detached process is the fallback only "when the tab cannot be opened" (a warning goes to stderr). Remove "Outside herdr" as a case: `squad-start` refuses to run outside herdr (check with `grep -n "not inside a herdr pane" bin/squad-start`). Same fix in `CONTEXT.md` if its Watchdog term says "elsewhere it is a detached process" (grep `CONTEXT.md` for "detached").
- AC3 Ticket `06-promotion.md` AC1: "one per workspace" (if present) becomes "one per home (scope or goal)".
- AC4 Nothing else changes: `git diff 249bcad --stat` shows only these files plus the 07 ticket and its evidence. No code, no tests, no version bump.

## Technical AC (QA whitebox)
- T1 `grep -rn "hidden detached\|Outside herdr\|outside herdr" README.md CONTEXT.md docs/adr/0022*` finds no hit (quote the output).
- T2 README line 46 still has the same number of `|` as before (one table row).
- T3 Targeted tests: every hit of `grep -rl 'README' tests/`; none skipped. No full suite without Chieu's yes.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace.
- Both QAs must PASS (Done rule). QA blackbox checks only that the corrected text matches behaviour it saw in 05 (fallback only when the tab cannot be opened); no new live runs.

## Review

AC trace:
- AC1 | `grep -n "hidden detached" docs/adr/0022*` (no hit) | grep
- AC2 | `grep -rn "Outside herdr\|outside herdr" README.md CONTEXT.md docs/adr/0022*` (no hit); README row, CONTEXT Watchdog term and ADR Decision say "when the tab cannot be opened" | grep
- AC3 | `grep -n "one per" .scratch/watchdog2/issues/06-promotion.md` shows "one per home (scope or goal)" | grep
- AC4 | `git diff 249bcad --stat`: README, CONTEXT, ADR 0022, 06 ticket, 07 ticket | git
- T2 | README line 46 has 3 `|` before and after | `sed -n 46p README.md`
- T3 | tests/test_squad_close, test_squad_path_guard, test_promotion_0_6_0: 103 OK | `cd tests && python3 -m unittest <names>`

Note: the "not inside a herdr pane" refusal is in `bin/squad-spawn` (which `squad-start` calls), not `squad-start` itself.
