# Evidence 01: squadtask module

## Behaviour

A scratch squad, team with no QA (M = 1), ticket 02 `Blocked by: 01`:

```
$ squad-task claim 02 --owner dev   (ticket 02 is blocked by 01)
recorded claim 02
warning: W1 started while ticket 01 is not yet passed
$ squad-task handin 02 --sha abc1234
recorded handin 02
$ squad-task pass 02 --sha abc1234   (confirmer; no QA on this team, so M=1)
recorded pass 02
$ squad-task show 02
02  passed  owner dev  sha abc1234  returns 0  
```

The claim on a blocked ticket gives W1 and is still recorded (AC8). Events go to `$SQUAD_DIR/task-events/<slug>.jsonl`; `squad-task show` derives the word.

## Review

| AC | Test or capture | How run |
| --- | --- | --- |
| states.md s2 words, s5 label table (needs-triage, needs-info, ready-for-agent, ready-for-human, claimed, done, wontfix) | `CheckersAndWords.test_words_and_label_table` | `cd tests; python3 -m unittest test_squadtask` |
| s4 M never 0, T8 (no QA; Team Lead as confirmer) | `CheckersAndWords.test_checkers_m_never_zero_and_confirmer` | same |
| s6 W1-W8 return text and still write, T6 | `Warnings.test_w1_to_w8_each_returns_text_and_still_writes`, `test_blocker_passed_or_merged_is_not_open` | same |
| AC8 claim while `Blocked by:` open: W1, claim recorded | W1 row of the test above; CLI capture above | same |
| T1 exit 0 on warning, hook never fails, write error never raises | `StoreAndHook.test_hook_entry_warns_and_never_fails`, `test_cli_claim_exit_codes` | same |
| T2 two writers, `mkdir` lock without `fcntl` | `StoreAndHook.test_concurrent_writers_and_mkdir_lock` | same |
| T3 parity with `squadledger.build`; T4 event shape; T5 real samples, ASK and evidence handin write nothing | `StoreAndHook.test_event_shape_and_fold_parity_with_ledger` | same |
| T11 targeted tests | `test_squadtask`, `test_squad_ledger` (unchanged), `test_windows_safe`, `test_no_bare_bash`: 45 OK | `cd tests; python3 -m unittest test_squadtask test_squad_ledger test_windows_safe test_no_bare_bash` |
| T12 stdlib, Windows-safe | `test_windows_safe` (every `bin/*.py`) | same |

Notes: a verdict that names an unknown sha counts for the current sha (same as `squadledger`); W5 still warns. W6 counts QA slots only ("1 of 2 checkers PASS").

## QA whitebox review

### QA whitebox, task 01: technical AC (proposal to the Tech Lead, REV-7)

Base: design.md s8 T1-T6, T8, T11, T12 stand as written. I add 6 lines (T13-T18) for risks T1-T12 do not pin. Each is one test or one grep, no matrix (test economy). Task 01 only.

| # | AC | How I check it |
|---|---|---|
| T13 | `squadledger.py` change is additive: `parse_handin(text) -> {sha, branch, evidence}` is public, `build` calls it, `tests/test_squad_ledger.py` passes with no edit to that file (`git diff base -- tests/test_squad_ledger.py` empty). | diff + run that file |
| T14 | D1 holds: after any `record(...)`, the only new or changed file under the repo and the scope is `$SQUAD_DIR/task-events/<slug>.jsonl` (+ its lock). No ticket file, `roster.md` or `messages.jsonl` is written. | one test: snapshot a temp tree before and after a claim, compare |
| T15 | `from_message` never raises and exits 0 on bad stdin (empty, non-JSON, JSON with no `type` or `task`) and prints nothing. T1 covers write errors; this covers input errors. | one test, 3 inputs |
| T16 | Task key: `squad-task claim 5` and `claim 05` land on the same state (`squadledger.key`); `why` is first line, cut at 200 chars. | one test each, or one combined |
| T17 | `blocked_by` (s4.2): reads a `Blocked by: 02, 03` line, `none` and empty give `[]`, a line past line 30 is ignored, the draft naming `ticket-NN-<slug>.md` is found. Not found = `[]`, no warning. AC8: a claim with an open blocker returns W1 and the event is in the file with `warn` set. | one table test + AC8 test |
| T18 | `squad-task` CLI: usage error exits 2 (unknown command, missing NN); goal context with no `--scope-home` exits 2; `show --json` output parses. Warning exit is 0 (T1). | one CLI test with subprocess |

#### What I check beyond tests (no test needed from the Developer)
- REV-4/REV-5b: I run `from_message` once on live records. Samples: a `PASS` with no sha, a `HANDIN` with `..<sha>`, one with `commit <sha>`, a `FAIL` naming a sha, plus an idle case (`ASK`, an `evidence sha` handin) from real `messages.jsonl`. I run it in a temp `SQUAD_DIR`, so the real store is not written. The Developer's fixtures must quote real lines (T5).
- T12 by grep: no top-level `import fcntl` without try/except; `open(..., encoding="utf-8")`; no `os.path`-built separators for store paths.
- T11 targeted run: `tests/test_squadtask.py`, `tests/test_squad_ledger.py`, plus `grep -rl 'squadledger' tests/`. No full suite without Chieu's yes.
- Diff touches only: `bin/squadtask.py`, `bin/squad-task`, `bin/squadledger.py`, `tests/test_squadtask.py` (ticket Files line).

#### Not required (so it is not a return reason)
Matrix tests of fold; a test per W-number beyond the one T6 table; process or board text.

#### Agreed with the Tech Lead (2026-11-07)
T13-T18 agreed as written, with T1-T6, T8, T11, T12. Rulings that bind my check:
- T14: `show` and `from-message` with no valid event are read-only; the snapshot covers that.
- T12 `os.path` rule applies to store paths and the new module only. `squadledger.py` keeps its old `os.path` code: not a return reason.
- T15: exit 0 and no output also for a record with a missing task id.
- REV-5b: live check only in a temp SQUAD_DIR; never write the real `task-events/`.

### Review of HANDIN 01, sha f087c25 (branch squad/plugin/task-claim-gates/plugin-dev-tcg-1)

Run by me: `cd tests; python3 -m unittest test_squadtask test_squad_ledger test_windows_safe test_no_bare_bash` = 45 OK. Diff touches only the ticket's Files line (plus the ticket drafts under `.scratch/task-claim-gates/issues/`). `test_squad_ledger.py` not edited (T13 ok).
Own checks in temp dirs (scripts in /tmp/chk.py-style, no write to the real store): T14 snapshot, T15 inputs, T16 key `5`/`05`, `why` cut, T17 parse, T18 exit codes, REV-5b replay of all 13 real `messages.jsonl` of this project through `from_message` (35 tasks, 0 exceptions; returns, sha and blocked_open equal to `squadledger.build`, except the two known diffs below).

| AC | Result |
|---|---|
| T1, T2, T3, T4, T6, T8, T11, T12 | ok (tests + my run) |
| T5 | ok; replay on real data ok (see F2 for tech-lead FAIL) |
| T13, T16, T18 | ok |
| T14 | ok for events; see follow-up 3 |
| T15 | ok for the listed inputs; see follow-up 2 |
| T17 | ok on my cases; see follow-up 4 |
| s6 W5 | **FAIL, F1** |

#### F1 (returns the task) W5 never fires from the hook for a sha that was never handed in
`bin/squadtask.py:332` `_named_sha` returns a sha only when it matches a known HANDIN sha. A `PASS` that names any other sha gets `sha=None`, so `check()` (`:216`) sees "current" and gives no W5, and `fold` counts the verdict for the current sha.
Repro (temp dir): HANDIN `abcdef1`; then `PASS 01: sha 1234567 ok` from a QA: `from_message` returns `[]` and `verdicts == {'qaw': 'PASS'}`. A typo or stale-in-another-clone sha passes the gate silently. States.md s6 W5 says: "PASS ... on a sha that is not the current HANDIN sha" warns. The test for W5 (`test_w1_to_w8...`) calls `record(sha="zzzzzzz")` directly, so the hook path is not covered. The evidence note ("W5 still warns") is true only for the CLI.
Would pass: when the text names a hex sha (6-40, with at least one digit) that matches no hand-in, pass it as `sha` so `check()` returns W5. Keep `fold` as it is (unknown sha still counts for the current one: T3 parity with `squadledger`). Add one row to the existing W-test through `from_message`.

#### Follow-ups (not returns; for the PASS or for later tickets)
1. **FAIL from role `tech-lead` (or any non-QA, non-confirmer role) is dropped with no warning** (`from_message`, `:352`). Real data: `scopes/_done/cleanup` task 04 and 05 have a `tl` FAIL; ledger counts 1 return, store counts 0. Design 4.1 says QA or confirmer only, so this is as designed; the PASS side has W4 and FAIL has nothing. Tech Lead to rule: warn, or map tech-lead.
2. `from-message` with a non-string `text` on a HANDIN (`{"type":"HANDIN","task":"01","text":5}`) raises TypeError in `parse_handin` and the CLI exits 1 with a traceback; `task` as a number logs "not recorded". Real records always have string fields, and `squad-log-message` ends the call with `|| true`; guard in `from_message` anyway (`isinstance` check).
3. `from-message` with a W4 PASS writes no event but creates `task-events/` and an empty `.lock` (`_locked` runs before the W4 return, `:274`). T14 allows the lock, so no return; the Tech Lead's note says "read-only". Move the W4 return before the lock to match.
4. `parse_blocked_by` takes every digit run on the line: `Blocked by: 02 (see 2026-11-07)` gives `['02','2026','11','07']` (false W1, false `blocked`). Also `squad_dir_of` returns the scope home itself for `scopes/_done/<scope>` (parent name `_done`), so a write for a retired scope would go to the wrong folder.
5. The Developer's tests do not cover T14, T16, T17, T15 beyond "not json". The ticket the Developer got lists T1-T6, T8, T11, T12 only; T13-T18 were agreed after the ticket was copied. I checked them myself (table above); not a return reason. Suggest adding T15/T17 rows when F1 is fixed (small).
6. **Not the Developer's:** the real `$SQUAD_DIR/task-events/task-claim-gates.jsonl` holds fake events (tasks 08, 09; `by` real agent names, `role: qa-blackbox`, branch `b`, ts 09:10-09:20 in the future). They come from a manual run against the real scope (QA blackbox, role env `qa-blackbox`). Clean it before task 03 reads it, or the board will show fake rows.

### Re-check of HANDIN 01, sha 7bf6439 (LC-3b: f087c25..7bf6439, squadtask.py and its test)
Run: `cd tests; python3 -m unittest test_squadtask test_squad_ledger test_windows_safe test_no_bare_bash` = 45 OK. F1 fixed: my repro (unknown sha 1234567) now returns W5, `fold` still counts it for the current sha; old-sha case still W5. Replay of all 13 real messages.jsonl: same result as before (0 exceptions, only the known diffs). Follow-ups 2 and 3 fixed (W4 returns before the lock; non-string guard). Verdict: PASS.
Open follow-ups: 1 (tech-lead FAIL dropped), 4 (Blocked-by digits, `_done` squad_dir_of), 5 (T14-T17 tests), 6 (fake events in the real store).
New, minor: the unknown-sha rule takes any 6+ digit run with a digit (`20261107`, `1000000`) as a sha, so such a number in a PASS text gives a false W5 warning (warning only, the verdict still counts).

#### Re-check 7bf6439..64b0785 (64b0785): PASS
Changed: bin/squadtask.py, tests/test_squadtask.py. Targeted `python3 -m unittest test_squadtask`: 9 tests OK.
Live (temp SQUAD_DIR, real roster, running pane = qa-blackbox): stranger PASS -> W4 fires; qaw/qab PASS counted with own roles (checking, 2 of 3); Manager PASS fills confirmer (passed); stored role = sender's roster role. `claim abc` and `claim "1; x"` -> usage, rc 2.
QAb findings 1 (W4), 2 (sender role / confirmer), 3 (non-digit id) are fixed. Temp dir removed. Earlier Follow-ups stay open.

## QA blackbox review

### QA blackbox verdict, task 01, sha f087c25

Method: `live` (Developer's evidence.md has command text, no shots). Scratch squad (temp dir, own SQUAD_DIR), `bin/squad-task` of the branch worktree. Business AC: tasks/states.md s9 + AC1-AC9. Task 01 shows no board (task 03), so I judged command output, exit codes, hook text.

| AC | live: what I did | what I saw | result |
|---|---|---|---|
| AC8 / W1 | claim 02 (Blocked by 01) | `recorded claim 02` + `warning: W1 started while ticket 01 is not yet passed`, rc 0, row `in progress` | pass |
| AC13 W2 | claim 02 by 2nd owner | `warning: W2 already owned by dev1` rc 0 | pass |
| AC13 W3 | handin with no claim | W3 text, rc 0; via `from-message` hook JSON `additionalContext` "task state warning: W3 ..." | pass |
| AC13 W5 | pass on other sha / before handin | W5 text, rc 0 | pass |
| AC13 W6 | confirmer pass before QAs | `W6 confirmed early; 0 of 2 checkers PASS` | pass |
| AC13 W7 | merged without PASS | W7 text, rc 0 | pass |
| AC13 W8 | claim on wontfix | `W8 ticket is wontfix` | pass |
| AC13 W4 | PASS from BA, from `stranger-agent` (message path) | recorded, **no warning**, not counted. W4 text never appears | **FAIL** |
| AC3/AC5 record side, R1 | both QA PASS by message, then Manager PASS, then Team Lead PASS (same sha, roster lists both) | stays `checking, 2 of 3 PASS`; Manager/TL PASS never fills the confirmer slot, so `passed` cannot be reached by messages. Manual `pass` with no `--slot` filled it (`passed`) whoever ran it | **FAIL** |
| AC15 | `claim abc --owner x` | `squad-task: not recorded: invalid literal for int() with base 10: 'abc'`, rc **1** (needs clear usage message, rc 2) | **FAIL** |
| AC15 | unknown verb; claim with no --owner; merged with no branch/sha | clear message + usage, rc 2, nothing recorded | pass |
| AC11 | BLOCKED msg, then DECISION | `blocked`, then back to `in progress` | pass |
| AC10 | HANDIN, FAIL, FAIL again | `returned`, returns 1 (second identical FAIL not double counted); first FAIL line not shown by `show` (board is task 03) | pass (see follow-ups) |
| AC14 | every W case | always rc 0, record written | pass |
| AC2/AC4/AC6/AC9/AC12/AC16-AC19 | board or hooks | not in task 01 | n/a here |

#### Findings (all in this sha)
1. W4 never fires (AC13). PASS by BA and by an unknown agent: no warning anywhere.
2. Manager or Team Lead PASS sent as a message does not count as the confirmer (states.md R1, AC5). Events also store `role: qa-blackbox` for every sender (the role of whoever runs the command, not the message sender), see `task-events/*.jsonl` field `role`. Manual `pass` counts as confirmer for anyone, with no W4.
3. Non-numeric ticket id: Python error text, exit 1 (AC15: clear message, exit 2).

#### Follow-ups (not blocking)
- `claim 99` for a ticket that is not in the folder is recorded (no error).
- `merged NN` with no branch on record exits 2; the manual fallback needs `--sha` or `--branch`.
- `pass --slot <unknown>` records silently and counts nothing (same root as finding 1).
- `show` prints no first FAIL line; board (task 03) needs it for AC10.

#### My own mistake (disclosed)
Some of my manual runs wrote 13 fake events (tickets 08, 09) into the REAL `$SQUAD_DIR/task-events/task-claim-gates.jsonl` (an `export` line used the real SQUAD_DIR). The delete was refused by the permission check, so the file and its `.lock` are still there. Chieu decides; all 13 lines are mine (tickets 08, 09, ts 09:10-09:20 and 08:52).

#### Final: re-check on 64b0785 (diff 7bf6439..64b0785). VERDICT: PASS
Isolated temp SQUAD_DIR (live run).
| Finding | What I did | What I saw | Result |
|---|---|---|---|
| 1 W4 | PASS by BA and by `stranger-agent` (message path) | hook text `task state warning: W4 not a checker; not counted`, rc 0, not counted | pass |
| 2 confirmer | Manager PASS, then both QA PASS | W6 early warning, then `checking, 2 of 3`, then `passed`; events now carry the sender's role (`manager`, `qa-whitebox`, `qa-blackbox`) | pass |
| 3 AC15 | `claim abc`, `claim 12x` | `claim needs one ticket number (digits), got 'abc'` + usage, rc 2, nothing recorded | pass |
| Regression | W1 not raised when blocker is passed (correct); W2, W7, W8; BLOCKED then DECISION | texts correct, rc 0, blocked then back to `in progress` | pass |

Follow-ups (not blocking, no AC broken):
1. `claim 99` for a ticket not in the folder is recorded with no error.
2. `merged NN` with no branch on record exits 2; the manual fallback needs `--sha` or `--branch`.
3. `show` prints no first FAIL line; task 03 needs it for AC10.
4. `pass --slot <unknown>` records silently and counts nothing.
5. My earlier runs left 13 fake events (tickets 08, 09) in the REAL `$SQUAD_DIR/task-events/task-claim-gates.jsonl` and its `.lock`. Removal was refused by the permission check; Chieu must delete both before task 03 reads that folder. My temp dirs /tmp/tmp.V3cBiSkyjY and /tmp/tmp.NGQ5IVltYi also remain (rm refused).

## QA blackbox AC check

### QA blackbox: proposed sharpening of business AC (before first HANDIN)

From: plugin-qab-task-claim-gates. To: BA (owner of tasks/states.md). Base: states.md AC1-AC9.
I can only judge what a person sees: board Tasks panel rows, `squad-task` output and exit code, hook warning text. Each AC below says WHERE it is seen.

#### A. Questions that block a test (need a BA ruling)

| # | Gap | Why I cannot test it | My proposal |
|---|---|---|---|
| Q1 | Confirmer when the team has BOTH Manager and Team Lead (this scope does). s2 says "Manager, or the Team Lead when the team has one", and "either one's PASS counts". | M and the "waits on" name differ by reading. 2 QAs + TL + Mgr = 3 or 4? | M = QAs + 1. Either Manager or Team Lead PASS fills the one confirmer slot. Waits on shows `Manager or Team Lead`. |
| Q2 | "Last active" for `todo`: s2 says "shows no time". What is on screen: empty, a dash, or text? The bug report said "no activity recorded". | AC1 cannot pass or fail on "no time". | Board shows the existing empty-state wording; BA names it. |
| Q3 | AC5 "the word `done` appears nowhere". Where? `tasks_done`, "Done means", scope text also contain it. | Unbounded. | Scope it: no `done` as a stage word in board rows, Inbox text, `squad-task` output, hook warnings. Internal names are out. |
| Q4 | AC2 "last active now". | "now" is not observable. | Within 1 minute of the claim. |
| Q5 | How does a warning look to the sender? s6 says hook additionalContext or command output. | I need exact text to compare. | Warning text = the s6 table text; command prints it on its own line prefixed `warning:`; exit code stays 0. |

#### B. Extra business AC I propose (each observable)

- AC10 FAIL: Given a checker sends FAIL on the current sha, the row shows `returned`, "N returns" and the first FAIL line, waits on the Developer. The Developer's next HANDIN returns it to `checking`.
- AC11 BLOCKED message: row shows `blocked`, waits on who it went to; a later DECISION or the sender's HANDIN clears it.
- AC12 sha changed: Given `passed`, then the branch tip moves, row shows `sha changed after PASS`, waits on checkers.
- AC13 Warnings W2-W8: each condition in s6 gives its short text at the sender AND in the row's detail note; the record is still written (never refused, exit code 0). One check per W.
- AC14 Never blocks: no command or hook in this scope refuses, errors out, or exits non-zero on a gate breach.
- AC15 Manual command: `squad-task <claim|handin|returned|blocked|passed|merged> NN` gives the same row as the hook path. Bad ticket number or unknown verb: clear error message, non-zero exit, nothing recorded.
- AC16 Old tickets, no events: row shows what ledger and git give (`merged` if branch in main; label mapped by s5 table), no crash, no `0 of 0`.
- AC17 Whole scope or goal: the board lists every ticket of the `tickets:` folder, including ones built in other scopes (the original bug: lean-config 01..11 must not all read todo/unassigned).
- AC18 Design unchanged: same layout, columns, Mango Parrot light palette; only words and data change. No new column.
- AC19 One word per row: when facts overlap, the row shows the s2 precedence winner (example: claim on open dependency = `in progress` + warning, not `blocked`; merge with no PASS = `merged` + W7).

#### C. What I can observe per task

| Task | My check |
|---|---|
| 01 `squad-task` | Scratch squad, run each verb; read command output, warnings W1-W8, exit code, the event line. No board yet (task 03 reads). AC8 record side, AC13, AC14, AC15. |
| 02 hooks | AC2, AC3, AC4, AC5 record side, AC8: spawn a Developer, send HANDIN/PASS/FAIL/BLOCKED messages, read command output and hook warning. |
| 06 merge hook | AC6 record side, W7. |
| 03 board | Board in browser (playwright, report folder served on 127.0.0.1): AC1, AC3-AC9, AC10-AC12, AC16-AC19. |
| 04 words | AC5 and Q3 scope on the board and Inbox. |
| 05 process text | Text reads true (no `done` stage word, new states named). |
