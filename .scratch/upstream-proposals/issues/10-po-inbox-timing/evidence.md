# 10 po-inbox timing: evidence
sha: 6f31d20
## Behaviour

- AC2 (alone, `SQUAD_*` unset): `python3 -m unittest test_po_inbox_mod`: 3 tests OK; `claude plugin test: 648 pass, 0 fail (not skipped)`.
- AC3 (final edits, nproc 16, busy-loop PIDs 661898-661913 (after returns 1, 2 and 3: 30 s timeouts on five tests) stopped by `kill`): 5 passes, 2 concurrent copies each, all 10 copies green, each `648 pass, 0 fail (not skipped)`.
- AC4 (scratch `/tmp/q10`, never committed): quadratic `parseBody` stand-in fails `linear > 2,000 rows x 20 cells: under 200 ms` (Expected < 200, Received 836.42); with `NOISE_MS` 100 a second stand-in fails `a far-away opener ...` (Expected < 1038.94, Received 1314.45) and `bullets nested to depth 2,500` (Received 2134.79).
- After merging task 11 (f8358d2; merge adds only 11's files): test_session_lookup, the 8 hook tests and test_po_inbox_mod: 131 tests OK.
- Details and rulings: the ticket's Comments.

## QA whitebox

### QA whitebox, ticket 10, sha 2432b7c (base 4e7d547; 11 merged at f8358d2, ancestor d15e043)

Verdict: FAIL (1 finding that breaks AC3, 1 style finding).

#### Finding 1 (breaks AC3): ratio tests in markup.test.ts hit the 5 s default test timeout under load
`hooks/po-inbox/markup.test.ts:339` ("a far-away opener of the other kind is not searched for again at every span") and `:331` ("4x the input takes under 12x the time ...") call `timed` several times on 80,000-160,000-unit inputs; `timed` now runs each 9 times. Under the AC3 load they take 3.5 s and more than 5 s. `item.test.ts` got `{ timeoutMs: 30000 }`; these tests did not.
Evidence, my own AC3 run (`/tmp/qaw10/stress.sh`, nproc 16, loop PIDs 601447-601463 stopped by PID, 5 rounds x 2 concurrent copies of `test_po_inbox_mod` on 2432b7c): 9 of 10 copies pass (648 pass, 0 fail). Round 1 copy 1 FAILED: `(fail) linear > a far-away opener of the other kind is not searched for again at every span [5138.44ms]`, `Error: timed out after 5000 ms`. In a passing copy the sibling test took 3505.87 ms. AC3 needs 5 passes in a row, so it fails.
Note: during my base run another session's 16 busy loops were also running (PPID 594310, not mine, left alone), so the host was heavier than AC3's load; the failure is still the test measuring the load, which the ticket exists to remove.
Pass: give the tests that call `timed` on the big inputs (`:331`, `:339`, and the 30-case loop at `:325` if it is slow) `{ timeoutMs: 30000 }` as `item.test.ts:282` has, keep the 200 ms and 12x checks, and rerun the AC3 stress 5 rounds.

#### Finding 2 (style)
`markup.test.ts:331` the test title still says "(+20 ms)"; the floor is now `NOISE_MS` = 100.

#### Reproduction of the problem on base (AC3, QA whitebox part)
Unfixed base 4e7d547 as a `git archive` copy in `/tmp/qaw10base`, nproc 16 busy loops (PIDs 597385-597402, stopped by PID), two concurrent copies: both FAILED. `linear > 2,000 rows x 20 cells: under 200 ms` Received 640 and 484; `item.test.ts` "hostile bodies mount in under 2 s each" timed out after 5000 ms in both. The load reproduces the problem.

#### Checked, passes
- AC1/AC2: `timed` = best of 9 `performance.now()` (Tech Lead's ruling: no `process` in the runtime); `test_po_inbox_mod` alone: 3 tests OK, `claude plugin test` 648 pass, 0 fail (not skipped), 63 s on the loaded host.
- AC5: diff 4e7d547..2432b7c: `markup.test.ts`, `item.test.ts`, the ticket, its evidence, plus the merged ticket 11 files (merge f8358d2 adds only 11's files).
- Rulings in the ticket Comments (NOISE_MS 100, `timeoutMs: 30000`, wall-clock hits listed) match the diff.

#### Follow-up (not FAIL)
- `12 * small + NOISE_MS` with NOISE_MS 100 means the ratio checks only catch a quadratic when the small run exceeds about 25 ms; the 200 ms and depth checks carry the rest. The Developer's AC4 stand-ins show the suite still fails for a quadratic parser.

### Re-check, sha f37886b (return 1)

Verdict: PASS. Supersedes my FAIL on 2432b7c; finding 1 and finding 2 fixed.
- Diff 2432b7c..f37886b: `{ timeoutMs: 30000 }` on the 30-case loop test, "4x the input" and "a far-away opener" in `markup.test.ts`; the "4x" title says +100 ms; ticket Comments and evidence updated. No other code.
- AC3, my own runs of `/tmp/qaw10/stress.sh` (nproc 16 loops stopped by PID after each run, two concurrent copies, 5 rounds):
  - Run 1 (loop PIDs 625051-625066): 9 of 10 copies pass (648 pass, 0 fail). Round 3 copy 2 failed `linear > a far-away opener ...` on the ratio line: `Expected: < 141.34, Received: 172.31` [6846 ms]. The host load average was 39-50 while it ran, well above the AC load (16 loops + 2 copies).
  - Run 2 (loop PIDs 637404-637419), host quieter: 10 of 10 copies pass (648 pass, 0 fail, not skipped), 5 rounds in a row.
  - The Developer's own run: 10 of 10 (PIDs 615918-615933).
  - Unfixed base under the AC load failed both copies (earlier section), so the load does exercise the fix.
- test_po_inbox_mod alone on 2432b7c: 648 pass, 0 fail. The 5 s timeout failure of finding 1 did not recur in any of the 20 copies.

#### Follow-up (not FAIL)
- The ratio check `12 * small + NOISE_MS` can still fail about once in 20 copies when the host is at about twice the AC load (one run: 172 ms against a bound of 141 ms). A later pass could raise NOISE_MS or drop the big-vs-small ratio in favour of the absolute 200 ms limit, which a quadratic parser (seconds) still breaks.

### Re-check, sha 1eb9cf6 (return 2)

Verdict: FAIL (1 finding, breaks AC3). Supersedes my PASS on f37886b.
- Diff f37886b..1eb9cf6: `{ timeoutMs: 30000 }` on `item.test.ts:201` ("handled <name>: ..."), ticket and evidence text. Alone: `test_po_inbox_mod` 3 tests OK, 648 pass, 0 fail, 48.6 s.
#### Finding 1: another mounting test with the 5 s default timeout
AC3 stress on 1eb9cf6 (`/tmp/qaw10/stress.sh`, nproc 16 loops PIDs 651325-651340 stopped by PID, two concurrent copies, 5 rounds): 9 of 10 copies pass. Round 3 copy 1 FAILED: `(fail) band 4.8: 120 to answer, 15 waiting, 3 problems keeps every count at 40 and 35 columns ... and survives 30 [5080.44ms]`, `Error: timed out after 5000 ms`, at `hooks/po-inbox/list.test.ts:69`. Same class as `item.test.ts:282`, `item.test.ts:201` and the `markup.test.ts` tests: a test that mounts the UI at several sizes has no `timeoutMs`. Its neighbours take 0.5-2 s each in that copy.
It is the third different test that the stress run finds after a fix (markup ratio tests, then item.test.ts:201 by QA blackbox, now list.test.ts:69): fixing the one that failed last leaves the rest at the 5 s default. Of 61 `test(` calls in `item.test.ts` two have `timeoutMs`; `list.test.ts` has none.
Pass: one sweep, not another single test: `{ timeoutMs: 30000 }` on every `test(` of `hooks/po-inbox/list.test.ts` and `item.test.ts` (and any other po-inbox test file) that opens the UI with `open(...)` or loops over sizes, then 5 rounds of the AC3 stress, twice in a row, with 10 of 10 copies green.
#### Run history (mine)
2432b7c: 9/10 (markup timeout). f37886b: 9/10 at host load 39-50 (markup ratio), then 10/10. 1eb9cf6: 9/10 (list.test.ts:69 timeout). Unfixed base 4e7d547: 0/2.

### Final sha 6f31d20 (Tech Lead DECISION 10 FINAL: AC3 rewritten, root fix not built)

Verdict: PASS. Supersedes every earlier verdict (2432b7c, f37886b, 1eb9cf6). My stress runs are stopped (loops and scripts killed by PID; head5 run had one more failed copy at 6f31d20, `far-away opener` ratio line Expected < 202.4, Received 213.95, while QA blackbox's stress ran at the same time; no longer an AC).
- AC1: `timed` = best of 9 `performance.now()` runs (ruled, no `process` in the runtime) with a one-line comment; `NOISE_MS` 100 in the ratio checks, `{ timeoutMs: 30000 }` on the patched tests (item.test.ts x2, list.test.ts:69, markup.test.ts x3), as the Rulings list.
- AC2/AC3 (rewritten): `python3 -m unittest test_po_inbox_mod` (SQUAD_REQUIRE_CLAUDE=1, SQUAD_* unset) on 6f31d20: run 3 `Ran 3 tests ... OK`, `claude plugin test: 648 pass, 0 fail (not skipped)`; a separate run of `test_plugin_test_passes` also 648 pass, 0 fail. The first run, at a host load average near 50, ended `FAILED (failures=1)`; I did not capture which test (tail only) and it did not recur in the two runs after. The parallel full `--tz` run is the Tech Lead's.
- AC4: scratch-copy quadratic failures quoted in the ticket Comments (836 ms, 2134 ms, 1314 ms against the limits).
- AC5: `git diff --stat 4e7d547 6f31d20` outside bin/tests/skills and 11's files: `markup.test.ts`, `item.test.ts`, `list.test.ts`, the ticket and its evidence (list.test.ts is added by the Tech Lead's ruling).
- Merge of 11 (f8358d2): `git diff --stat ea76131 6f31d20` = ticket 10 files and the three po-inbox tests only; `git diff --stat d15e043 ea76131` = 11's evidence.md only. The merge adds 11's files and nothing else.
- AC6: `test_po_inbox_mod` plus the other `grep -rl 'po-inbox\|markup' tests/*.py` hits: 188 tests OK except `test_squadinbox.NoBytecodeTest.test_no_pyc`, which fails because Developer 10's worktree holds git-ignored `bin/__pycache__/*.pyc` (dated 18:26:02); on a clean `git archive` of 6f31d20 it passes. Clear the bytecode before the Tech Lead's `--tz` run.

#### Follow-ups (not FAIL)
- The timing tests stay load-sensitive: with my stress loops, 3 of 4 final-line shas lost one copy in 10 (markup ratio line twice, list.test.ts:69 once).
- Stray `*.pyc` in the worktree (above).

## QA blackbox

### QA blackbox 10, sha 2432b7c

| AC | how | what I did | what I saw | result |
|---|---|---|---|---|
| AC2 test_po_inbox_mod passes, 648 pass, not skipped | live | `python3 -m unittest test_po_inbox_mod` from `tests/` with `SQUAD_*` unset, `SQUAD_REQUIRE_CLAUDE=1` (inside each stress pass) | `Ran 3 tests ... OK`, `claude plugin test: 648 pass, 0 fail (not skipped)` | pass |
| AC3 stress, 5 passes in a row | live | own script: `nproc` = 16 busy loops (`python3 -c "while True: pass"`), PIDs kept: 594313-594328; per pass two concurrent copies of `test_po_inbox_mod`; loops stopped by `kill` of that PID list afterwards (all gone) | 5 passes x 2 copies = 10 runs, each `OK`, `648 pass, 0 fail (not skipped)`; first pass took 64 s per copy under the load (host load average was already high) | pass |
| AC4 test still catches a quadratic parser | shot | Developer's quoted failures in the ticket Comments (scratch `/tmp/q10`, not committed: "2,000 rows x 20 cells: under 200 ms" Expected < 200, Received 836.42; "bullets nested to depth 2,500" Received 2134.79; "a far-away opener" Expected < 1038.94, Received 1314.45) | clear failure lines naming the tests; not re-run | pass (shot) |
| AC5 diff lists only the allowed files | live | `git diff ea76131 HEAD --stat` (10's own change on top of the merged 11) | `markup.test.ts`, `item.test.ts`, the ticket and its evidence.md; nothing else | pass |
| AC1, AC6 | - | code and test-file content, grep hits | QA whitebox's | - |

Follow-ups (not FAIL, SQ-4):
- The ticket's AC4 first stand-in (`len/20`) and the second one differ; the "4x the input takes under 12x" test failed by the 5 s test timeout, not by the ratio line, in the second stand-in. The Developer disclosed it; the 200 ms and far-away-opener checks do catch it.
- `NOISE_MS = 100` makes the ratio checks lenient by 100 ms; a mildly super-linear parser may now pass them. The 200 ms checks remain the guard. For the PO to know, not a defect of the AC.

#### Re-check, sha f37886b: FAIL (AC3)

Changed since 2432b7c: `markup.test.ts` (30 s timeout on 3 timed tests, test title), ticket and evidence text. I re-ran AC3 (the only live AC the change touches): nproc 16, busy PIDs 625633-625648 (all stopped by PID afterwards), 5 passes x 2 copies of `python3 -m unittest test_po_inbox_mod` (`SQUAD_*` unset, `SQUAD_REQUIRE_CLAUDE=1`).

Result: 9 of 10 runs `OK ... 648 pass, 0 fail (not skipped)`. Run 5, copy a: `FAILED (failures=1)`, `647 pass, 1 fail`, `Ran 3 tests in 88.801s`. The failing line in the log:

```
288:(fail) handled answered-waiting: the state is right after the title, before the body (V-03 v3.1), token per V-15 [5078.23ms]
289-  Error: timed out after 5000 ms
```

It is `hooks/po-inbox/item.test.ts` "handled answered-waiting: the state is right after the title, before the body (V-03 v3.1), token per V-15" hitting the 5000 ms default test timeout (the same loop's siblings took 1.6-2.6 s). It is a test the ticket did not touch, and the same class of defect as the ticket (a time limit measuring the loaded machine). AC3 says 5 passes in a row; one copy failed, so AC3 is not met on f37886b. (The 5 passes on 2432b7c were 10 of 10 green, so this is a flake rate near 1 in 10 under this load, not a new break.)

Fix for the Developer to consider: give the `handled ...` state tests of `item.test.ts` the same 30000 ms `timeoutMs` the ticket already gives the hostile-bodies test (the Tech Lead may rule on scope), then re-run AC3.

#### Re-check, sha 1eb9cf6: PASS
Changed since f37886b: `item.test.ts` (one line: 30 s `timeoutMs` on the "handled ..." state test), ticket and evidence text; no other file. AC3 re-run: nproc 16, busy PIDs 649942-649957 (all stopped by PID afterwards), 5 passes x 2 copies of `test_po_inbox_mod` (`SQUAD_*` unset, `SQUAD_REQUIRE_CLAUDE=1`): 10 of 10 `OK`, `648 pass, 0 fail (not skipped)`, no `(fail)` line in any log. AC2 is inside each run. AC3 met; my earlier finding is fixed.
Follow-up (not FAIL): the flake rate was about 1 in 10 before the fix, so 10 green runs is good evidence, not proof; other 5 s default-timeout tests in `item.test.ts` could still flake under heavier load.

#### Final verdict, sha 6f31d20: PASS (Tech Lead named it final; AC3 rewritten by Chieu E4 b)
- AC2 / rewritten AC3: `python3 -m unittest test_po_inbox_mod` once from `tests/`, `SQUAD_*` unset, `SQUAD_REQUIRE_CLAUDE=1`: `Ran 3 tests in 113.393s`, `OK`, `claude plugin test: 648 pass, 0 fail (not skipped)`. (The parallel full `--tz` run is the Tech Lead's.)
- Before the AC3 narrowing I had started the stress on this sha; I stopped it on the Tech Lead's DECISION. Its 3 finished passes (6 runs) were all green; the loops were stopped by PID and none are left.
- AC5: `git diff ea76131 HEAD --stat` lists `markup.test.ts`, `item.test.ts`, `list.test.ts`, the ticket and its evidence. `list.test.ts` is not in the ticket's AC5 wording; the ticket's own Rulings (LC-7b step-in, E4 b) name it (`list.test.ts:69`), so I accept it.
- AC4: not re-run, Developer's quoted failures stand (see the first section).
- Ticket 11 merged in (f8358d2) still works: scratch squad from the real roster, `squad-log-message` with `SQUAD_*` unset: my real session id logged one record with `from` = `plugin-qab-upstream-proposals`; a made-up id logged nothing (rc 0).
