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
