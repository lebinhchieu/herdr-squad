# 07: One `pick_bash` for every bash launch

Status: ready-for-agent
Type: task
Blocked by: 03 (the test helper needs it)
Source: findings.md W6

**What:** `pick_bash` (rejects the System32 WSL launcher and the WindowsApps stub, falls back to the bash next to `git.exe`) exists only in `bin/squad-start`. A bare `bash` launched from Python on Windows resolves to `C:\Windows\System32\bash.exe`. No other `bin/` or `hooks/` code does that today (`grep` found none), but the tests do (ticket 03) and any new code will.

## Do
- Move `pick_bash`/`need_bash` into `bin/squadio.py`, import it from `squad-start`, and use it from the tests' launch helper (ticket 03).
- Add a guard test that fails on a bare `"bash"` in a `subprocess` call under `bin/`, `hooks/`, `tools/`.

## AC
- [ ] `squad-start` behaviour unchanged (its existing `pick_bash` tests pass, unmoved logic).
- [ ] The guard test exists and is green on Linux and Windows.

## Comments
