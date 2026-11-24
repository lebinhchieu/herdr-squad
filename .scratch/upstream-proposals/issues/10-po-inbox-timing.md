# 10 The po-inbox "under 200 ms" tests fail under a parallel suite

Status: ready-for-review (Developer, 2026-11-24)

Spec: `.scratch/upstream-proposals/spec.md`. Base: the 08 branch after the main merge (4e7d547). Chieu's E3 asked for this.

## Problem

`tests/test_po_inbox_mod.py::PoInboxModTest::test_plugin_test_passes` runs `claude plugin test`, which runs `hooks/po-inbox/markup.test.ts`. Its `linear` tests ("2,000 rows x 20 cells: under 200 ms, words kept" and 29 siblings) and the two "4x the input takes under 12x the time" tests time `parseBody` with wall-clock `Date.now()` (`timed`, `markup.test.ts:275`). In the full `--tz` run on 932420a, 16 test files ran in parallel: the 20-cell case took 208 ms in one run and 319 ms in the next. Alone it passes (648 pass, 0 fail). The test guards against a quadratic parser (V-28), which takes seconds. A wall-clock limit also measures how long the machine kept the process waiting.

## Decision (Tech Lead)

Fix the measurement, keep the limit. Do not raise 200 ms and do not skip the test (a higher limit hides less, a skip hides all).
Change `timed` to report the best of 3 runs of CPU time: for each run take `process.cpuUsage()` before and after (`user + system`, microseconds, converted to ms), return the smallest. CPU time does not grow while the process waits for a core, and the best of 3 drops a one-off pause (garbage collection, a page fault). The result still has `blocks` and `plain` from the last run. The 200 ms limit and the 12x ratio checks stay as they are. If `process.cpuUsage` is not available or is not finer than 1 ms in the Bun that `claude plugin test` uses, fall back to the best of 5 runs of `performance.now()` and say so in the Comments.

## Files (LC-9)

`hooks/po-inbox/markup.test.ts`, the `timed` helper (about 10 lines); and, ruled after Developer 10's stress run, `hooks/po-inbox/item.test.ts`, one `test('hostile bodies mount in under 2 s each, ...')` call, which gets a 30000 ms timeout argument (the 5 s default covers its whole loop; the per-body 2 s check stays). `process` is undefined in the plugin-test runtime, so `timed` uses the documented fallback (best of 9 `performance.now()`). No parser code, no rule, no `bin/`, no `templates/`, no version, no changelog, no `LIMIT`. Harness: `claude plugin test`, run by `tests/test_po_inbox_mod.py`. The Developer greps the other po-inbox and squads hook tests for wall-clock thresholds (`grep -rn "Date.now()\|performance.now()\|toBeLessThan" hooks`) and lists them in the Comments; it changes one only if it fails under the stress check.

## AC

- AC1: `timed` takes the best of 3 CPU-time runs as above (or the documented fallback); no other line of `markup.test.ts` changes except a one-line comment on why.
- AC2: `python3 -m unittest test_po_inbox_mod` (from `tests/`, `SQUAD_REQUIRE_CLAUDE=1`, `SQUAD_*` unset) passes: 3 tests, `claude plugin test` 648 pass, 0 fail, not skipped.
- AC3 (stress, whole file): with the machine loaded, `test_po_inbox_mod` passes 5 times in a row. Load = `nproc` busy loops (`python3 -c "while True: pass"`), each started in the background with its PID kept, plus two concurrent copies of `python3 -m unittest test_po_inbox_mod`; stop the loops by PID afterwards (SAFE-3, never `pkill`). Quote the PID list, the five results and the machine's `nproc`. Both QAs run this check themselves on the final sha; QA whitebox also runs it once on the unfixed base (`git stash` is shared, so use a `/tmp` copy via `git archive` of the base sha) and quotes whether it failed, to show the load reproduces the problem.
- AC4: the test still catches a quadratic parser. The Developer shows once, in a scratch copy under `/tmp` and never committed, that a `parseBody` made quadratic (for example an added nested loop over the input for the 20-cell case) fails "under 200 ms" with the new `timed`; quote the failure line.
- AC5: `git diff <base> HEAD --stat` lists `hooks/po-inbox/markup.test.ts`, `hooks/po-inbox/item.test.ts`, this ticket and its evidence only.
- AC6: SQ-10: this ticket touches no `bin/`, no printed text and no role text, so the three SQ-10 files are not required; `test_po_inbox_mod` and `grep -rl 'po-inbox\|markup' tests/*.py` hits are.

## Rulings during the build (Tech Lead, 2026-11-24)

- `process` is undefined in the plugin-test runtime: `timed` is the best of 9 `performance.now()` runs.
- `item.test.ts`: `{ timeoutMs: 30000 }` as the second argument of `test()` (signature `test(name, options, body)`).
- Ratio checks: under 18 busy processes the "a far-away opener" check failed at 70 ms and 91 ms against a bound of 65 and 62 ms, because the big input carries GC and cache noise that more samples do not remove. So `+ 20` becomes `+ NOISE_MS` with `NOISE_MS = 100` in every ratio check of `markup.test.ts`; the 12x factor stays. AC4 also needs a quadratic stand-in that fails the ratio tests with that floor.

## Duties

Evidence: `.scratch/upstream-proposals/issues/10-po-inbox-timing/evidence.md` (Behaviour: AC2, AC3 and AC4 output). Hand in to both QAs. After 10 passes, the Tech Lead sets row 3 of `base-failures.md` to "fixed by 10" and runs one full `--tz` on 10's final sha (`SQUAD_*` unset, stray `bin/*.pyc` cleared, `PYTHONDONTWRITEBYTECODE=1`); that sha is the merge target.

## Comments

- 2026-11-24 Developer: `process.cpuUsage` is not available in the plugin-test runtime: the CPU-time `timed` failed 30 tests with `ReferenceError: process is not defined`. So the documented fallback, best of 9 `performance.now()` runs (Tech Lead's ruling raised 5 to 9).
- `test(name, options, body)` is the signature; a third positional argument fails with "the file did not load: test(name, body) or test(name, options, body)". `{ timeoutMs: 1 }` gives "timed out after 1 ms"; `timeout` and `timeout_ms` are ignored. So `{ timeoutMs: 30000 }`.
- Wall-clock hits (`grep -rn "Date.now()\|performance.now()" hooks`): `markup.test.ts` (`timed`, changed), `item.test.ts:286-290` (2 s per body, kept; the 5 s whole-test default fixed), `core.test.ts:295-302` (200 ms and 12x + 20, did not fail in 5 stress passes, left alone). `toBeLessThan` elsewhere compares widths and indexes, not time.
- Stress failures seen on the way (each a copy of test_po_inbox_mod under the load): item.test.ts "hostile bodies mount..." timeout 5000 ms (3 of 10 copies); markup.test.ts "a far-away opener..." Expected < 65.19 Received 70.02 (best of 5), Expected < 62.15 Received 90.80 (best of 9). Both rulings above.
- AC2 alone: 648 pass, 0 fail (not skipped), 3 tests OK in ~17.9 s (about 15.3 s before the item.test.ts edit and best of 9; the unfixed base was not timed).
- AC3 (final edits): nproc 16, PIDs 570649-570664 (all stopped by `kill` of that list), 5 passes, both concurrent copies green each time: 648 pass, 0 fail (not skipped) x5.
- AC4: scratch copy `/tmp/q10`, never committed, `parseBody` given a nested loop over the input. First stand-in (`len/20`, inputs < 200000): "2,000 rows x 20 cells: under 200 ms" Expected < 200, Received 836.42. Second stand-in (`len/400`, all inputs) with NOISE_MS 100: "bullets nested to depth 2,500: under 200 ms" Received 2134.79; "a far-away opener..." Expected < 1038.94, Received 1314.45; "4x the input takes under 12x..." failed by the 5 s test timeout (the stand-in is slow), not by the ratio line.
