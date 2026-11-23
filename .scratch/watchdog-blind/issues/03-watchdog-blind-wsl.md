# 03: Watchdog: Manager not counted, blind log, WSL powershell path; plugin 0.10.9

Status: ready-for-agent
Duties: design notes = Developer (this file, ## Design notes); technical AC = QA whitebox with the Developer; business AC = this ticket; code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; suite and promote.md = QA whitebox; no full suite without Chieu's yes
Files: bin/squad-watchdog, tests/test_squad_watchdog.py, docs/adr/0028-watchdog-follows-goals-file.md, .claude-plugin/plugin.json
Test harness: tests/test_squad_watchdog.py (pure decide()/snapshot fixtures, stub herdr)
Ticket path (commit by the first Developer task, FILE-11): `.scratch/watchdog-blind/issues/03-*.md`; evidence next to it.

Blocked by: 02

Seen in the guardian goal: the goal Manager is on the roster and counts as `working`, so the pod is never idle while it works; nothing logs that no ticket has a status, so a blind watchdog looks quiet; WSL sleep logs `suspend failed (powershell.exe)` when `powershell.exe` is not on PATH.

## AC
1. `decide()`: an agent with role `manager` never counts as working for the idle spell (it still counts for `machine_working` / sleep, unchanged). Test: Manager working, rest idle, goal in progress -> `start` event.
2. Blind: when goals are not recorded, the scope has tickets and none has a status, the watchdog logs once per spell `blind: <N> tickets, none with a status` and sends it to the Manager once (same route as nudges). Not repeated each tick; a later spell may log again. Test covers once-only.
3. WSL: `suspend_cmd()` uses `powershell.exe` from PATH if found, else `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` if it exists, else returns the bare name (and the failure log names the missing path). Tests patch `shutil.which` and the path; nothing suspends.
4. ADR 0028 gets one amendment line: the Manager is not counted as working for the idle test; the module docstring line 16 ("Idle = nobody in the roster is `working`") says the same.
5. [SQ-5] `.claude-plugin/plugin.json` version 0.10.9; `grep -rn '0\.10\.8' .claude-plugin/plugin.json` finds nothing; every test that pins the version is updated (grep `0.10.8` in tests/).

## Rules for this ticket
- Proof runs only in a scratch squad (temp dir, stub `claude` and herdr, as `tests/test_squad_start.py` / the named test file). Never run `squad-watchdog tick|run|ensure` or `squad-spawn` against `/home/chieule/workspace/wpw` (live guardian agents get messages).
- [SQ-10] Any `bin/` edit: also run `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py`; quote the result in `## Behaviour`.
- CLAUDE.md: run `grep -rl` over `tests/` for each touched path or changed printed string and run every hit.
- [SQ-2] `## Review` starts with an AC trace; quote `squad-evidence checks` exit code in HANDIN.

## Technical AC (QA whitebox, agree with the Developer here; written before work, 2026-11-23)
T1. `decide()` stays pure and `st` is never mutated (existing deepcopy test style). Manager excluded only from `working` for the idle spell: `machine_working`/sleep/`quiet_since` code path untouched, and `bg_busy` of a Manager does not count either (bg token on a manager name must not keep the spell from starting; test it). Role comes from the snapshot agent row; `grep` shows where `role` is set in snapshot and the value `manager` is matched case-exactly as the roster writes it. `all_blocked` and `stop` use `working` too: Developer states in `## Design notes` which `working` they use and why (idle-spell one, or all-agents one); a test shows the Manager working + goals all blocked/done is not stuck as "working" in a way that breaks `all_blocked`/`stop`.
T2. Blind spell: the once-per-spell flag lives in `st` (persisted in watchdog.state.json, reset when the spell ends), not in a module global; a tick-twice test sends once, a spell-end then a new spell sends again. The message goes through `route()`/`send()` the same way as nudges (to the Manager per the ticket; say if route() would pick the Team Lead and why that is fine). Count `<N>` = tickets in the scope with an empty status; text exactly `blind: <N> tickets, none with a status`. Condition checks all three: goals not recorded, scope has tickets, none has a status; a scope with 0 tickets or with one status does not fire.
T3. Log line goes to the same watchdog.log writer as `start`/`nudge` lines (same format, timestamped). A test reads the log file, not just the returned event. New event name is documented in the `decide()` docstring event list.
T4. `suspend_cmd()` WSL branch: three outcomes tested with `shutil.which` and `os.path.exists`/`Path.exists` patched (nothing suspends: `subprocess.run` patched to raise if called). Return value shape stays `(argv, shell)`; env `SQUAD_WATCHDOG_SLEEP_CMD` still wins first; win32/darwin/Linux branches unchanged. When neither is found the failure reason from `suspend()` names the missing path (a test on `suspend()` with subprocess patched to raise `FileNotFoundError`). REV-4 sample: the Developer pastes the real `ls -l /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe` on this WSL host in `## Design notes`; WSL_PS string reused as is.
T5. Docs: ADR 0028 gets exactly one amendment line; module docstring line 16 rewritten to say the Manager is not counted. `bin/squad-watchdog` line 22 (old-check text) read: if it says the same idle rule for the no-goals path, it is updated too or noted why not. Also any other doc that restates "nobody in the roster is working" (`grep -rn "nobody in the roster" docs templates bin`) is listed with the decision.
T6. Version: `grep -rn '0\.10\.8' .claude-plugin/plugin.json tests/` = no hits; every test that pinned the old version moved; `grep -rn "0\.10\.9"` hits only intended places. Not touched: marketplace file unless it holds the version (grep `0\.10\.8` over the repo excluding .git, .scratch, scopes/_done, and list the hits).
T7. Proof only in scratch (no tick/run/ensure on wpw); `grep -rl squad-watchdog tests/` hits all run green; SQ-10 three files run and quoted; no new skips. Depends on 02: built on 02's passed sha, so the blind test uses real `status_of` with `State:` files, not a stub.
