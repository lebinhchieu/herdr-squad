# 03: Windows launch helper for the tests

Status: ready-for-agent
Type: task
Blocked by: 01 (so the first real failures are product ones)
Source: findings.md W2

**What:** the suite cannot say whether the shell scripts work on Windows. `python -m unittest discover -p "test_*.py"` from `tests/` ran 1574 tests with, after a throwaway workaround, `failures=410 errors=32 skipped=202`. `tests/run_suite.py` also needs `fcntl`. Nothing in the failures I saw was shown to be a product bug; the harness hides them.

**Causes (all in `tests/`):**
1. Tests run extensionless scripts directly (`subprocess.run([".../bin/squad-spawn", …])`): `WinError 193`.
2. Tests that call a bare `["bash", script]` get `C:\Windows\System32\bash.exe` (the WSL launcher; CreateProcess searches System32 before PATH): `/bin/bash: C:/…/squad-spawn: No such file or directory`, exit 127. `bin/squad-start` already has `pick_bash`.
3. `test_squad_start.py` `run_child` and `test_utf8_helpers.py` pass `bytes` argv/env (`enc = lambda x: str(x).encode("utf-8", "surrogateescape")`); Windows rejects them: `TypeError: bad argument type for built-in operation` (about 70 tests).
4. `os.openpty` (`test_squad_notify`), `os.symlink` privilege (`WinError 1314`: `test_ca_install`, `test_utf8_helpers.JqTest`), `termios`, and POSIX-path fixtures (`test_templates` compares `/` paths). `tests/RUNNING-ON-WINDOWS.md` lists only some of these.

## Do
- One helper, e.g. `tests/winlaunch.py`: `run_script(path, args, env)` resolving the interpreter from the script's shebang with `pick_bash` (Git bash by absolute path, never the System32 or WindowsApps hit), `python3` for python scripts, `str` argv/env on `nt`, `bytes` kept on POSIX. Use it in every test that launches `bin/` or `tools/` scripts or calls `bash` by name.
- Fix the Windows-only test bugs in cause 4 or skip them with a reason that names the cause (the ADR 0011 convention: nothing skipped on Linux).
- Update `tests/RUNNING-ON-WINDOWS.md`, and make `tests/run_suite.py` run on Windows or document the `unittest` command for the whole suite.
- Then triage what still fails: each remaining failure is either fixed here or becomes a new ticket in `.scratch/windows-native/issues/`.

## AC
- [ ] The full suite runs on Windows to completion; the skip list in `RUNNING-ON-WINDOWS.md` matches reality.
- [ ] Every remaining Windows failure has a ticket or a named skip reason.
- [ ] A test fails if `tests/` launches a bare `"bash"` through `subprocess` (grep-style guard).
- [ ] Linux: same pass count as before, zero new skips.

## Comments
