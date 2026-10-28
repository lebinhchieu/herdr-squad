# T1 Launcher runs `squad-spawn` through bash (and UTF-8 in `bin/squad-start`)

Status: needs-triage (draft: waits for BA business AC + Tech Lead technical AC)
Type: task
Source: issue.md Bug 1; scope win-compat
Touches: `bin/squad-start`, `tests/test_squad_start.py`
Blocked by: 07 (T0, `squadio.py`)

## What
- `squad-start` runs `squad-spawn` as `[bash, <path>, ...]`, with `bash` resolved once (`shutil.which`); a clear error and non-zero exit if bash is missing. Both call sites: resume (~l.141) and new scope/goal (~l.230).
- Because it owns the file, this ticket also adds `encoding="utf-8", errors="replace"` to the 4 subprocess calls in `squad-start` (l.43, 71, 141, 230) so no other ticket touches this file.

## Audit note
Decided (design.md D6): `hooks/po-inbox/actions.ts` needs no change; no T5 unless the PO's checklist shows a spawn error after T2a.

## Business AC (BA; spec.md stories 1-3, 5)
- B1. Given a plain Git Bash prompt (no env vars) on Windows, When `squad-start "<text>" --touches <paths>` runs, Then a scope folder and brief exist and a Manager tab is ready; no `WinError`, no traceback. (story 1)
- B2. Same for `squad-start --resume <name>`: Manager tab with the RESPAWN prompt is ready. (story 2)
- B3. With no `bash` on PATH: exit non-zero, one line that names `bash` and says to install Git for Windows or add its `bin` to PATH; no scope folder, workspace rename or tab left behind (the check runs before anything is written). (story 3)
- B4. A Manager started by B1/B2 spawns the pod (Tech Lead, Dev, QA whitebox, QA blackbox) with no `PYTHONUTF8` exported by the PO: the fix lives in the plugin. Check by running the spawn from a shell whose env has no UTF-8 vars. (story 5)
- B4a. `squad-start` also reads its templates and files under `LC_ALL=C PYTHONUTF8=0` without `UnicodeDecodeError` (QA blackbox measured it on 0.3.2). (stories 1, 2)
- B5. The `touches:` edit of `scope.md` keeps the file UTF-8 with LF only (use `newline="\n"` or bytes); UTF-8 round trip proved on Linux, LF is Windows-only proof (checklist). (story 6)
- Not required: quoted paths in the `would run:` line (cosmetic).

## Technical AC (Tech Lead; design.md D1, D2, D5, D6, D7)
Depends on T0 (`squadio.py`).
1. `squad-start` calls `squadio.utf8_stdio()` first in `main`; all 4 `subprocess` text calls (l.43, 71, 141, 230) pass `encoding="utf-8", errors="replace"`; `scope.md` read-modify-write (l.103-113) uses `encoding="utf-8"` strict and writes `newline="\n"` through `open(...)`, not `Path.write_text`.
2. Both spawn sites run `[bash, <squad-spawn>.as_posix(), ...]` with env `SQUAD_DIR=squad.as_posix()`. One resolver function `pick_bash(which, exists, nt, system_root)`, pure (injected, so testable on Linux), design D5: `which("bash")` first; on nt a hit under `System32` or any `WindowsApps` folder is rejected; fallback walks up at most 3 parents from `which("git")` and takes the first existing `<root>\bin\bash.exe`. Tests: PATH stub `bash` records argv (resume and new scope); System32 and WindowsApps hits rejected; the fallback finds bash from each of `<Git>\cmd\git.exe`, `<Git>\bin\git.exe`, `<Git>\mingw64\bin\git.exe` (fake `exists`); no bash anywhere: no bash gives one line naming Git for Windows, exit non-zero, and no scope folder, workspace rename or tab (check runs before `render`).
3. The `would run:` dry-run line is byte-identical to today; dry-run needs no bash. `tests/test_squad_start.py` existing cases pass unchanged.
4. Under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252` with a stub herdr printing `🦀 Manager`: exit 0, no traceback; the JSON line on stdout is UTF-8 with `\n`.
5. A project dir named `with space 🦀` works for new and resume.
6. Audit result is recorded in this ticket's Comments: `actions.ts` needs no change (D6); hooks.json commands are bash scripts run by the host.

## Comments

- 2026-10-17 T1 audit (AC6, from dev-3, handed in 62a8755): `hooks/po-inbox/actions.ts` needs no change (design D6): it runs `bin/squad-inbox` by argv and the PO's error text is the mod's `failure(r)` of the process output, so Python started and the host resolved the shebang. `hooks/hooks.json` has 4 commands (l.7, 12, 15, 21): squad-log-message, squad-usage-hook, squad-notify (twice), all bash scripts run by the host as `${CLAUDE_PLUGIN_ROOT}/bin/<name>`. No T5 unless the PO checklist shows a spawn error (not a traceback) after T2a.
- 2026-10-17 Tech Lead approved the argv re-decode in `bin/squad-start` (beyond design.md; reviewed 62a8755, tests-only re-hand-in e3288ff OK). A one-line code comment for it may go in with T2b's commit.
