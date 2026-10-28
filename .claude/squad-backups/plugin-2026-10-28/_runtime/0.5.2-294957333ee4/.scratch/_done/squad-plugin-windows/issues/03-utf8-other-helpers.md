# T2b UTF-8 in the remaining helpers

Status: needs-triage (draft)
Type: task
Source: issue.md Bug 2 (squad-label:31, squad-notify:80, squad-migrate:46)
Touches: `bin/squad-label`, `bin/squad-notify`, `bin/squad-migrate`, `bin/squad-usage`, `bin/squad-close` (the `python3 -c` block), `bin/squad-log-message`, `bin/squad-respawn`, `bin/squad-retire` (jq check), plus tests
Blocked by: 07 (T0, `squadio.py`)

## What
`encoding="utf-8", errors="replace"` on every subprocess text call and every file read/write in these files. Bash scripts that invoke python (squad-close l.85) get `PYTHONUTF8=1` / `encoding` inside the snippet. Tech Lead to check whether `squad-spawn`/`respawn`/`retire` call python and add the same.

## Business AC (BA; spec.md stories 4, 5, 6, 10)
- B1. Given a herdr stub that prints a tab label `🦀 Manager` (byte 0x90 present), When `squad-label` and `squad-spawn` run under `PYTHONUTF8=0 LC_ALL=C`, Then both exit 0 and the label reads back intact; no `UnicodeDecodeError`. (story 4; the issue's crash)
- B2. `squad-spawn` for each of the 9 roles (manager, ba, team-lead, tech-lead, qa-whitebox, qa-blackbox, dev, designer, token-coach) with a project path that contains spaces and an emoji label: dry-run and the stubbed real run succeed. (story 4)
- B3. `squad-label`, `squad-usage`, `squad-process`, `squad-notify`, `squad-log-message`, `squad-usage-hook`, `squad-respawn`, `squad-retire`, `squad-close` each end (a) exit 0 with empty stderr, or (b) one stderr line naming the cause and a non-zero exit; never a traceback. Printing non-ASCII under `LC_ALL=C PYTHONUTF8=0` counts. `squad-notify`: toasts unsupported on Windows (PO, E3), so path (a). Hooks (`squad-usage-hook`, `squad-log-message`) are checked with a sample payload; real firing on Windows is not verified in this scope. (story 10; O1 closed)
- B4. `squad-respawn` and `squad-retire` use `jq`, not shipped with Git for Windows: either no `jq` use, or path (b) of B3 with a line that names `jq` and what to install. Tech Lead picks (spec O2). (story 10)
- B-LF. `write_text`/text-mode writes in `squad-usage` (`roster.md`) and `squad-migrate` keep `\n` only and UTF-8. **Windows-only proof** (CR counts on the PO checklist). (story 6)

## Technical AC (Tech Lead; design.md D1, D2, D7-D9)
Depends on T0 (`squadio.py`).
1. Each Python CLI here (`squad-label`, `squad-notify`, `squad-migrate`, `squad-usage`) calls `squadio.utf8_stdio()` first in `main`; all subprocess text calls (`squad-label:31`, `squad-notify:80`, `squad-migrate:46`) pass `encoding="utf-8", errors="replace"`; every text read/write names `encoding="utf-8"` (including the transcript read at `squad-usage:42`, `errors="replace"`), writes add `newline="\n"` through `open(...)`, not `Path.write_text` (design D2) (`squad-usage` `roster.md`, `squad-migrate` `tmp.write_text`; read-modify-write files strict).
2. `squad-notify:111` reads stdin as UTF-8 (done by `utf8_stdio`); with `/proc` missing it exits 0, no output, no traceback (D9; test with `proc_root` pointing at nothing).
3. `squad-close` inline snippet is `python3 -X utf8 -c`. `squad-spawn` needs no change (D7); its `squad-label` and `squad-usage` children fix themselves.
4. D8: with `jq` off PATH, `squad-respawn` and `squad-retire` exit non-zero with one line naming `jq`, before touching herdr; `squad-log-message` exits 0, writes nothing, one stderr line.
5. Under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`, stub herdr printing `🦀 Manager` (byte 0x90): `squad-label` and `squad-spawn --dry-run` exit 0, label intact (bytes compared). `squad-usage --get` output has no `\r` (stdout wrapped as in design.md test method).
6. `squad-spawn --dry-run` for each of the 9 roles with a project path `with space 🦀`: exit 0.
7. Design D12: `squad-usage --check <session>` with no transcript found (`projects_glob` matches nothing; HOME pointing at an empty dir) exits 0, prints nothing, no traceback. `squad-usage-hook` then exits 0.
8. Existing tests for these helpers pass unchanged on Linux; golden bytes for `squad-label`, `squad-usage --roster`, `squad-migrate` fixtures identical before and after (QAW E6).

## Comments
