# I The five test files run green on Windows: fix the harness, not the product

Status: ready-for-agent
Type: task
Source: `windows-checklist-results.md` Finding 1 (PO's Windows run on c195474: 5 failures + 5 errors)
Touches: `tests/test_squadinbox.py`, `tests/test_squadinbox_answer.py`, `hooks/po-inbox/mod.test.ts`, this ticket file, and `.scratch/squad-plugin-windows/windows-checklist-results.md` (commit it as given; the root copy is untracked)
Does not touch: `bin/`, `agents/`, `windows-checklist.md`, `tests/RUNNING-ON-WINDOWS.md`, any other test file. Ticket 17 owns the rest; no file is shared with it.
Harness: Python `unittest` run from inside `tests/` (`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadinbox test_squadinbox_win test_po_inbox_contract test_po_inbox_mod test_squadinbox_answer`), plus `claude plugin test` on the repo (through `test_po_inbox_mod`). Base: main `c195474`, branch `--base c195474`, fresh Developer name.
Blocked by: none. Parallel with 17.

## What
Real Windows is the only proof, so each fix is chosen by its cause (Finding 1), and the Developer proves on Linux that nothing else changed.

| Failing test | Cause | Fix |
|---|---|---|
| `test_squadinbox.AddReadTest.test_add_answer_row_on_top`, `RowWriterTest.test_each_break_becomes_one_br` | `run()` in `test_squadinbox.py` (line ~47) passes `input=<str>` with `text=True`; on Windows the pipe writer turns each `\n` into `\r\n`, so `\r\n` arrives as `\r\r\n` and a blank line yields `<br><br>` | `run()` sends the stdin as UTF-8 bytes (`input=stdin.encode("utf-8")`, no `text=True`) and decodes stdout and stderr itself as UTF-8; it still returns an object with `.returncode`, `.stdout` and `.stderr` as `str`, so no caller changes |
| `test_squadinbox_answer.AnswerTest.test_round_trip`, `test_stdin_meaning` | same `run()` (imported from `test_squadinbox`) | covered by the same fix |
| `test_squadinbox_answer.InvalidUtf8Test.test_refused_and_nothing_written` (5 subtests) | Windows cannot put invalid UTF-8 in argv; `subprocess.list2cmdline` raises before the CLI starts | skip **only those 5 subtests** (the argv cases `--title`, `--options`, `--text`, `--note`, `--reason`) on `sys.platform == "win32"` with a reason; the 3 body-file/stdin cases keep running on Windows, and all 8 run on Linux |
| `test_po_inbox_mod.PoInboxModTest.test_plugin_test_passes` (2 failures in `mod.test.ts`: `active: manager with SCOPE_DIR`, `active: manager with only GOAL_DIR`) | the host's `fs.stat` event carries `C:\h\scope\inbox.jsonl` on Windows; the test compares `${home}/inbox.jsonl`. The code (`actions.ts` `signature()`) builds `${run.home}/${name}` and is fine | in the harness `world()` `fs.stat` handler record a normalised path (`\` to `/`, leading `C:` dropped); the expectation stays `${home}/inbox.jsonl`. No change to `actions.ts` |

Other `text=True` stdin writes in the five files (`test_squadinbox.py` Popen at ~291 and ~560 send `"body"` with no newline, `test_squadinbox_win.py` ~65): leave them. If a grep shows one that sends a `\n`, treat it as the same cause and fix it the same way; name it in the hand-in.

## Technical AC (Tech Lead, with QAW)
1. **I1 green.** On Linux the five files give the same `Ran N` as at `c195474` (quote both), `skipped=0` (`--tz` semantics: nothing skipped on Linux), in the UTF-8 locale and under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`. Windows: the PO's rerun of the same command reports 0 failures and 0 errors; the evidence says that is the only proof.
2. **I2 only the argv subtests skip, only on Windows.** The skip is conditional on `sys.platform == "win32"` (a `subTest` guard or a `skipIf`-style helper); the reason string names Windows and "invalid UTF-8 cannot be passed in argv". No skip on Linux. No assertion is weakened and no test is deleted; the argv cases are not removed from the tuple, so Linux still runs all 8.
3. **I3 the doubled-CR cause is gone, shown on Linux.** `run()` is shown to pass CRLF through unchanged even when a text-mode pipe would translate it: a one-off command (not committed) that calls `run()` with `stdin="a\r\nb"` and a stub CLI echoing `sys.stdin.buffer.read()` as `repr`, quoted in `dev-evidence.md`, prints `b'a\r\nb'`; the same call with the old `text=True` form, run with `-c` and Python's `newline` translation forced (QAB: `sitecustomize` wrapper of `open`/`io.TextIOWrapper` newline=CRLF), is the failing contrast. The 4 text-mode tests keep their expected values byte for byte.
4. **Body-file fixtures.** Every fixture that writes a body file in text mode with `\n` content uses `newline="\n"` (`open(..., newline="\n")`; `Path.write_text(newline=)` needs 3.10 and is forbidden by ADR 0011). A grep result for `write_text(` with `\r` or body content in the two files is quoted.
5. **I4 mod test.** `claude plugin test` passes on Linux (the `test_po_inbox_mod` run, `SQUAD_REQUIRE_CLAUDE=1` if `claude` is on PATH). The normaliser is one small function in `mod.test.ts`; `/h/scope`, `/h/goal` and the `endsWith('/bin/squad-inbox')` checks stay. Linux proof the normaliser fires: a one-off (not committed) that makes the `fs.stat` handler see `\h\scope\inbox.jsonl` and shows the two tests still pass; quoted.
6. **Diff scope.** `git diff --stat c195474 HEAD` lists only the five paths in Touches. `git merge-base --is-ancestor c195474 HEAD` printed in the hand-in.
7. Run test files from inside `tests/`, `PYTHONDONTWRITEBYTECODE=1`. The Developer runs only the five files; the Tech Lead runs `--tz` on the integration sha.

## Comments
- Tech Lead design note: `run()` returns `subprocess.CompletedProcess` built from the bytes result (`args`, `returncode`, decoded `stdout`/`stderr`) so every caller (they read `r.stdout`, `r.stderr`, `r.returncode`) stays as is. Decode with `encoding="utf-8"` (errors strict is fine for the CLI's own output; invalid output should fail the test).
