# D Windows-only test failures are skipped with a reason

Status: ready-for-agent
Type: task
Source: `issue-po-inbox.md` "Test suite does not pass on Windows"
Touches: `tests/test_squadinbox.py`, `tests/test_squadinbox_win.py`, `tests/test_squadinbox_answer.py`, `tests/test_po_inbox_contract.py`, `tests/test_po_inbox_mod.py`, `tests/po_inbox_fixtures.py` if needed
Blocked by: none. Parallel with 09, 10, 11 (no shared file).

## What
Each Windows-only failure becomes a skip with a reason, never a deleted test: `termios`/`pty` modules, symlink privilege (`WinError 1314`), file modes (`438 != 416`), `os.execv` (`test_concurrent_adds_on_a_barrier`), the `NoFcntl` simulations (need real `fcntl`), `/tmp/home` and `/h/scope` POSIX fixtures, text-mode fixtures (write with `encoding="utf-8"`, `newline="\n"` and fix, where a fix is cheap). Use `@unittest.skipIf(sys.platform == "win32", "reason")` style, reason names the cause.

## Technical AC (Tech Lead)
1. On Linux every test still runs and passes, same counts as at base (`--tz`, nothing skipped).
2. Each added skip has a reason string naming one of the causes above; no skip on Linux.
3. No `bin/` change. Product bugs found are reported, not fixed here.
4. Real Windows is not testable here: a Linux-run test proves the guard condition (e.g. a test patches `sys.platform`) where cheap; otherwise the PO re-runs on Windows.

## Comments

### Tech Lead amendment (2026-10-17) — binding
- **TD1 (replaces AC 4)** do not patch `sys.platform`. Skip on the capability where there is one: `termios`/`pty` import guard; symlink: try `os.symlink`, `self.skipTest("symlinks need a privilege (WinError 1314)")` on `OSError`. Otherwise `skipIf(sys.platform == "win32", "<reason>")`. A file-mode assertion is skipped alone (not the whole test) when the test checks more.
- **TD2** the issue gives causes, not test ids. Map each of the 12 failures to a cause by reading; list them in `dev-evidence.md` (test id, cause, skip form, why it is not a product bug). A suspected product bug: `BLOCKED` to the Tech Lead.
- **TD3** a text-mode fixture is fixed (binary mode or `newline=""`) when the fix is one line; skipped otherwise.
- **TD4** Linux: the five files run the same test count as 59a8d1b with zero skips from your changes (`-v` output diffed, quoted), in the UTF-8 locale and under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`.
- **TD5** every skip reason is non-empty and names Windows or the missing module. No assertion weakened, no test deleted, only decorators and fixture modes edited.
- **TD6** the PO runs `cd tests; python3 -m unittest test_squadinbox test_squadinbox_win test_po_inbox_contract test_po_inbox_mod test_squadinbox_answer` on Windows: 0 failures. Evidence says this is the only proof.

- BA AC (spec.md story 17): (F4) `tests/run_suite.py` imports `fcntl`, so also add `tests/RUNNING-ON-WINDOWS.md` (new): the command to run the test files on Windows, what is skipped and why. Add it to Touches. QAB adds the checklist line once the command is named.
- Skips are conditional on Windows or the missing module (Linux: same test count, no skips). A Windows failure outside the listed causes is NOT skipped; report it to the Team Lead as a possible product bug.
- **TD7 (QAW)** `import pty` / `termios` at the top of `tests/test_squadinbox_answer.py` breaks the whole module on Windows, and a decorator cannot fix an ImportError: guard those imports (try/except ImportError) and skip the dependent tests/classes on the guard. One shared guard constant per module. The `NoFcntl` simulations keep running on Linux (they are the only proof of the msvcrt branch); skip them only when `sys.platform == "win32"`.
- **TD8 (QAW)** Linux proof the guard fires: a one-off command (not a committed test) that blocks `pty`/`termios` (`sys.modules['pty'] = None`) before importing the test module and shows the constant false; quote it in evidence. Linux `Ran N` and `skipped=0` equal at 59a8d1b and at the tip.
