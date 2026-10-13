Status: ready-for-agent
State: done
Task ID: BRD-09
Blocked by: 01, 02, 03, 04, 05, 06, 07 (06 already contains 05; 08 is not included, it stacks on this ticket)
Files touched: `bin/squad-board` (merge-conflict resolution only), `tests/test_board_integration.py` (new, only if the coverage check finds a gap), no other new files

# BRD-09: integrate iteration 1

**Done when one branch holds every passed iteration 1 branch, the whole suite is green on it, no stub or dead code is left in `bin/squad-board`, and every iteration 1 rule of the spec is covered by a Seam A test.**

Read first: design.md (all of it), `squad/process.md` → "Stacked branches", spec "Testing Decisions". The PO wants a polished result: this ticket is the bar for that.

## Build

1. **Branch** from the BRD-01 sha (the Manager gives it) as `squad/dev-board-<n>`.
2. **Merge** every passed `squad/dev-board-*` branch for BRD-02, 03, 04, 06 (it contains 05) and 07. Conflicts: keep both sides; change no logic while resolving. A bug you find goes back to the owning Developer through tech-board (`BLOCKED BRD-09: …`), not into your merge.
3. **Run the full suite** (`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`), and start the server once on a fixture and `curl` `/state`, `/events` (first event) and a refused jump.
4. **Clean-up check**, by grep and by reading `bin/squad-board`:
   - no `501`, "not implemented", `pass`-only bodies, `TODO`, or stub return values left from BRD-01's skeleton;
   - no function that nothing calls, no unused import, no unused constant (`FOLD_GAP_S`, `WAKE_WINDOW_S`, `POLL_S` are used);
   - the section markers are intact and in the design.md order;
   - the 14 Seam B tests untouched.
5. **Coverage check:** fill the table below in `dev-evidence.md`, one test name per row (file and test). A row with no test is a gap: write the Seam A test in `tests/test_board_integration.py` (red first if the behaviour is missing, then report it, do not fix it in this ticket).
6. **HANDIN** to qaw-board with the branch and commit id. `git add` named files only.

## Coverage table (spec rules for iteration 1)

| Spec rule | Test |
|---|---|
| Roster, scopes, escalations, iterations parsed | |
| Column order, Manager first, pod grouping, unknown agent at end of pod | |
| Rows in time order, one per event | |
| Folded gap (threshold and row shape) | |
| Bar start from a message, self-start, wake window | |
| Blocked segment | |
| Bar end, duration, open bar to `now` | |
| Working and blocked totals, wakes | |
| Task state per message type, return count, blocked → building | |
| Needs-you: blocked agent, empty escalation, Manager idle | |
| BLOCKED message is not a needs-you item | |
| Tokens from transcript, nulls for missing or bad transcript, incremental read | |
| Iteration tagging and iteration filter | |
| Jump refuses missing/wrong token, non-roster name, wrong method; no herdr run | |
| 127.0.0.1 bind, Host check, port fallback | |
| SSE: initial state, change event, no event without change | |
| Robustness: bad JSONL line, missing logs, empty fixture | |

## Technical AC (BRD-09)

1. **Merge:** every passed branch's commits are in the integration branch's history; `git log --oneline` lists them; no force-push or history rewrite (nothing is pushed at all).
2. **Suite:** full `unittest discover` green on the integration branch, run by the Developer and again by qaw-board.
3. **No leftovers:** the clean-up checks of step 4 pass; the grep output is in `dev-evidence.md`.
4. **Coverage table complete,** every row names an existing test that passes; any added test is Seam A (real server, real HTTP).
5. **Diff hygiene:** `git diff --stat <BRD-01 sha>..HEAD` shows only files the merged tickets list, plus `tests/test_board_integration.py` if added; no `__pycache__`, no conflict markers (`grep -n '^<<<<<<<\|^>>>>>>>'` empty).
6. **Smoke:** `curl` outputs of `/state`, the first `/events` event and a refused jump are in `dev-evidence.md`.
7. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

8. **End-to-end run (qaw-board checks):** the real `bin/squad-board --replay <demo fixture> --now <fixed>` answers `/state`, the first `/events` event and a stub-herdr jump; BRD-08 comes after this ticket, so the run uses a fixture built with `tests/board_fixture.py`. The Developer does the same run and saves the output.
9. **Python 3.9 read of the whole file:** no `match`, no runtime `X | None` or `list[int]` annotations without `from __future__ import annotations`, no `str.removeprefix`/`removesuffix`, no parenthesised `with`, no `zip(strict=)`, `fromisoformat` never fed a trailing `Z`. Checked by reading plus `ast.parse(..., feature_version=(3, 9))`.
10. **Merged-file checks:** sections in design order with their `# --- section:` markers; `build_state` calls each section once; the grep gate from BRD-05 Q10 passes on the merged file.
11. **Stability:** full suite green 3 times in a row and once under `TZ=Asia/Ho_Chi_Minh LC_ALL=C`; no stderr from any server; no leaked `squad-board` or stub-herdr process afterwards (`pgrep`).
12. **Contracts:** merged `/state` has exactly the design.md key list; no token in `/state`, `/`, or stderr.
13b. **SSE on escalations (carried over from BRD-06):** BRD-06 was built before BRD-03 existed, so its test for "editing `escalations.md` produces a new event with the new needs-you item" lands here as a Seam A test in `tests/test_board_integration.py` (red first against a build without the watcher entry, or by reverting the watched-file list in a scratch copy). The coverage table's SSE row names it.
13a. **Imports:** all imports are in the top import block; no mid-file `import` (qaw-board N2 on BRD-04: `import os` and `import threading` in the tokens section move up).
13. **Who builds it:** a Developer who wrote none of the merged tickets (the Manager's call at spawn), on a branch from the BRD-01 sha.

### QA whitebox additions (qaw-board)

Items 8 to 13 above came from qaw-board; it adds any further points here.

## Comments
- 2026-10-12 tech-board: PASS by qaw-board at 5e005ec (squad/dev-board-8). Two defects found on real data go to BRD-18.
