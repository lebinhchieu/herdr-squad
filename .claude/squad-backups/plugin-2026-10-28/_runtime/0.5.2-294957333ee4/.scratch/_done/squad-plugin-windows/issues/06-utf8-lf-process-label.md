# T2c UTF-8 and LF in squadprocess, squadlabel, squad-process, processlint

Status: needs-triage (draft)
Type: task
Source: issue.md Bug 2; BA F2 (text-mode `\n` becomes `\r\n` on Windows)
Touches: `bin/squadprocess.py`, `bin/squadlabel.py`, `bin/squad-process`, `bin/processlint.py`, their tests under `tests/`
Blocked by: 07 (T0, `squadio.py`)

## What
Split out of T2a. Every file read/write names `encoding="utf-8"`, writes keep LF (`newline="\n"`), no text-mode write turns `\n` into `\r\n`. Business AC: stories 4, 6, 10 in `spec.md` (below). Stories 7-9 are inbox behaviour and live only in T2a (02).

## Business AC (BA; spec.md stories 4, 6, 10)
- B1. Files these modules write (`process.md` via `squad-process apply`, `process-log.md`, the label JSON of `squadlabel.py`) are UTF-8 with `\n` only: no `\r\n` from a text-mode write, emoji and accents intact, and nothing else in the file changes byte for byte. UTF-8 round trip is proved on Linux; LF is **Windows-only proof** (CR counts on the PO checklist); a Linux test of the write call is a technical check, not business proof. (story 6)
- B2. Given a label with an emoji (`🦀 Manager`), When `squadlabel.py` stores and reads it back under `PYTHONUTF8=0 LC_ALL=C`, Then the text comes back identical, no `UnicodeDecodeError`. (story 4)
- B3. `squad-process show/apply/check` and `processlint.py` on a process file with non-ASCII text exit 0 with empty stderr, also when they print non-ASCII under `LC_ALL=C PYTHONUTF8=0` (printing counts, not only reading; F0). (stories 7, 10)

## Technical AC (Tech Lead; design.md D1, D2)
Depends on T0 (`squadio.py`).
1. `squad-process` and `processlint.py` call `squadio.utf8_stdio()` first in `main`; every text open in the four files names `encoding="utf-8"`; every write adds `newline="\n"` through `open(...)`, not `Path.write_text` (design D2) (`squadprocess` `out.write_text`, `os.fdopen(fd, "w")`, `log.read_text`; `squadlabel` `read_text`, `write_text`). `process.md` is a read-modify-write file: strict decoding.
2. Under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`: `squad-process show`, `check`, `apply` and `processlint.py` on a process file with `→ 🦀 é` exit 0; the written `process.md` and `process-log.md` are compared as bytes (UTF-8, no `\r`, nothing else changed); `squadlabel` stores and returns `🦀 Manager` identically.
3. Existing `test_squadprocess*.py`, `test_squadlabel.py`, `test_processlint.py` pass unchanged on Linux.

## Comments
