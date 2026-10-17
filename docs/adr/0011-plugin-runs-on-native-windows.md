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

## The decisions (D1-D8)

- **D1 stdio:** `bin/squadio.py` `utf8_stdio()` sets stdin to UTF-8 and stdout/stderr to UTF-8 with `newline="\n"`. A Windows pipe is cp1252 and writes `\r\n`; the `\r` breaks bash `$(...)` parsing.
- **D2 per-site `encoding=`:** each text open names its encoding; no wrapper. Reads replace or are strict as above; writes use `open(..., newline="\n")`.
- **D3 inbox lock:** `squadinbox.py` uses `msvcrt.locking` on byte 0 of `inbox.jsonl.lock` when `fcntl is None`; `flock` stays on Linux. Both `os.open` calls add `O_BINARY` so `os.write` never turns `\n` into `\r\n`.
- **D4 stdin on Windows:** `select` on a pipe raises there, so `stdin_text(only_if_ready=True)` returns `""` when the `IS_WINDOWS` constant is true. The `--note` text is already given; with no note the pane's stdin is still read, and the "both given" refusal is not enforced on Windows.
- **D5 launcher:** `squad-start` always runs `[bash, <squad-spawn as_posix>]`, with `SQUAD_DIR` as `as_posix()`. `pick_bash` rejects the System32 and WindowsApps launchers and falls back to the `bin/bash.exe` next to Git; with no bash it says so in one line before writing anything.
- **D6 inbox mod unchanged:** `hooks/po-inbox/actions.ts` runs `bin/squad-inbox` by argv. The PO's error was a Python traceback, so the shebang script started; a spawn error on the checklist would open a T5 (`['python3', path, ...]` plus an argv test).
- **D7 `python3` stays:** `squad-spawn` and `squad-close` keep calling `python3`; `squad-close`'s inline snippet runs `python3 -X utf8 -c`. A machine with only `python` fails the checklist's `python3 --version` step: a prerequisite, not a code change.
- **D8 `jq` is a prerequisite:** `squad-respawn`, `squad-retire` and `squad-log-message` check `command -v jq` first. The first two stop with one line naming `jq` and how to install it; the hook logs nothing, prints one stderr line and exits 0.

## Also true after this scope

- `squad-usage` and `squad-notify` do nothing, quietly, where the Linux paths (`/proc`, project transcripts) are missing (D9, D12).
- `.gitattributes`: `* text=auto eol=lf` and `bin/* text eol=lf` (D11).

Design details: `.scratch/squad-plugin-windows/design.md` (D1-D12).
