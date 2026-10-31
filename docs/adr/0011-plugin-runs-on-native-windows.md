# The plugin runs on native Windows (Git Bash + `python3`)

Status: accepted (win-compat)

**Decision:** the plugin supports native Windows: Git Bash plus `python3`. Prerequisites: Git's `bash` (not the WSL launcher), `python3`, `jq`, `git`, herdr. WSL and PowerShell are not targets. No new Python floor: the README's floor stays `python3`.

**Why:** 0.3.1 failed on Windows: no `fcntl`, cp1252 decoding, shebang scripts run by `CreateProcess`.

**Not fixed:** `os.replace` onto a file another Python process has open raises `PermissionError` on Windows. It stays on the PO's checklist (design D10).

## Rules for `bin/`

- Every Python text open names `encoding="utf-8"`; writes also `newline="\n"` via `open(...)`; never `Path.write_text(newline=)` (needs Python 3.10).
- A read-modify-write file (`scope.md`, `roster.md`, `process.md`) decodes strictly; a file only parsed or displayed, and subprocess text, use `errors="replace"`.
- Every Python CLI calls `squadio.utf8_stdio()` first in `main`.
- No module-level `import fcntl`; POSIX-only modules are guarded.
- **What `tests/test_windows_safe.py` enforces:** the first, third and fourth rules, and `encoding=` on `subprocess` calls that use text mode. The strict-versus-replace choice is **not** tested: it stays a review item.

## Rules for roles

- A role that edits a squad file (`roster.md`, `scope.md`, notes) by script opens it with `open(path, "w", encoding="utf-8", newline="\n")`: Windows text mode writes CRLF, and a `\r` breaks bash `$(...)` parsing. The Manager and Team Lead instructions say so.
- Readers tolerate CRLF already on disk (`read_text`, stripped cells, `[[:space:]]` in bash); `tests/test_crlf_squad_files.py` pins it.

## The decisions (D1-D8)

- **D1 stdio:** `bin/squadio.py` `utf8_stdio()` sets stdin to UTF-8 and stdout/stderr to UTF-8 with `newline="\n"`. A Windows pipe is cp1252 and writes `\r\n`; the `\r` breaks bash `$(...)` parsing.
- **D2 per-site `encoding=`:** each text open names its encoding; no wrapper. Reads replace or are strict as above; writes use `open(..., newline="\n")`.
- **D3 inbox lock:** `squadinbox.py` uses `msvcrt.locking` on byte 0 of `inbox.jsonl.lock` when `fcntl is None`; `flock` stays on Linux. Both `os.open` calls add `O_BINARY` so `os.write` never turns `\n` into `\r\n`.
- **D3b log append lock:** `squad-log-message` and `squad-usage-hook` append under `flock` where it exists. Git for Windows has no `flock`, so they take a `mkdir "$log.lock"` spin lock (250 tries, 20 ms apart, about 5 s) around the same append. A lock left by a killed writer is removed after the wait; the hook then goes on without owning it and still exits 0. Reason: `O_APPEND` does not promise one intact write for a record over about 4 KiB. Decided by reasoning; no stress test was run (the PO removed it).
- **D4 stdin on Windows:** `select` on a pipe raises there, so `stdin_text(only_if_ready=True)` returns `""` when the `IS_WINDOWS` constant is true. The `--note` text is already given; with no note the pane's stdin is still read, and the "both given" refusal is not enforced on Windows.
- **D5 launcher:** `squad-start` always runs `[bash, <squad-spawn as_posix>]`, with `SQUAD_DIR` as `as_posix()`. `pick_bash` rejects the System32 and WindowsApps launchers and falls back to the `bin/bash.exe` next to Git; with no bash it says so in one line before writing anything. `pick_bash` and `need_bash` live in `bin/squadio.py` and `squad-start` imports them. `tests/test_no_bare_bash.py` fails on a bare `"bash"` or `"sh"` as the first item of a `subprocess` argv in `bin/`, `hooks/`, `tools/` and `tests/`.
- **D6 inbox mod runs `python3`:** `hooks/po-inbox/actions.ts` runs `['python3', <root>/bin/squad-inbox, ...]` for all four calls (`list`, `delivered`, `answer`, `read`). A script with no extension cannot be spawned by argv on Windows (`ENOENT` under Node). An argv test pins the arrays. Whether the Claude Code host resolves `python3` on Windows is checked by the PO's pane check, not by a test.
- **D7 `python3` stays:** `squad-spawn` and `squad-close` keep calling `python3`; `squad-close`'s inline snippet runs `python3 -X utf8 -c`. A machine with only `python` fails the checklist's `python3 --version` step: a prerequisite, not a code change.
- **D8 `jq` is a prerequisite:** `squad-respawn`, `squad-retire` and `squad-log-message` check `command -v jq` first. The first two stop with one line naming `jq` and how to install it; the hook logs nothing, prints one stderr line and exits 0.

## Also true after this scope

- `squad-usage` and `squad-notify` do nothing, quietly, where the Linux paths (`/proc`, project transcripts) are missing (D9, D12).
- `.gitattributes`: `* text=auto eol=lf` and `bin/* text eol=lf` (D11).
- `squad-inbox add` normalises `\r\n` and lone `\r` to `\n` in the body (file and stdin) before storing; `answer` text is not touched.
- `squad-spawn` turns the runtime path into a POSIX path with `cygpath -u` before it builds `--env PATH=<runtime>/bin:$PATH`: a `C:/…` segment inside a colon list makes herdr give the new shell an unusable PATH. Without `cygpath` the value is unchanged.
- `squad-process scaffold` and `upgrade` work from an installed plugin cache (no `.git`): `running_pin()` takes version and sha from the matching `squad@*` entry of `installed_plugins.json` (`SQUAD_INSTALLED_PLUGINS` overrides the path). `--new-pin` and `--old-root` stay as the manual fallback.
- `.claude/squad-backups` (4007 files) is untracked and in `.gitignore`; git history keeps it. Merging that change deletes the folder from a working tree that has it.
- Tests on Windows: `tests/winlaunch.py` launches `bin/` scripts from tests (shebang to Git's bash by absolute path, or `sys.executable`; Linux argv and env are unchanged). `tests/run_suite.py` runs on Windows (its browser lock uses `msvcrt`). `tests/RUNNING-ON-WINDOWS.md` is the how-to.
- A test that only fails on Windows (termios/pty, symlink privilege, file modes, `os.execv`, `NoFcntl` simulation, POSIX path fixtures) is skipped with a reason that names the cause; Linux skips none of them. The Windows suite is not green yet. The test-side failures still open are tickets 11, 12 and 13 in `.scratch/windows-native/issues/`; ticket 08 (Windows items nobody has verified on a live Windows hook) is not done.

Design details: `.scratch/squad-plugin-windows/design.md` (D1-D12); the 0.6.4 work: `.scratch/windows-native/` (spec, findings, tickets 01-13).
