# T2a Windows-safe `squadinbox.py` (no fcntl/select), UTF-8 + LF there

Status: needs-triage (draft)
Type: task
Source: issue.md Bug 2; PO inbox traceback
Touches: `bin/squadinbox.py`, `bin/squad-inbox`, their tests under `tests/`. (squadprocess/squadlabel/squad-process/processlint moved to T2c, `06-utf8-lf-process-label.md`.)
New scope (QAW + BA, verified `import fcntl` at squadinbox.py:8, flock at l.214, `select.select` on stdin at l.638): the likely cause of the PO's inbox traceback. Needs a Windows-safe write lock with the same no-lost-row guarantee (tested with fcntl hidden on Linux) and a non-select stdin check; plus explicit UTF-8 and `newline="\n"` on writes.
Blocked by: 07 (T0, `squadio.py`)

## What
The PO's inbox crash is `import fcntl` (Windows has no `fcntl`); fix the lock, the `select` call, binary-mode fds, then explicit UTF-8 and LF in `squadinbox.py` and its CLI. Design: `design.md` D1-D4.

## Business AC (BA; spec.md stories 6-9)
- B0. All three causes (F0) are covered, each alone and all at once: no `fcntl`, printing non-ASCII to stdout/stderr, reading files. Printing `→`/emoji under `LC_ALL=C PYTHONUTF8=0` exits 0 with empty stderr for `list`, `list --json`, `list --open`, `read`; an `encoding=` grep alone does not pass this. (story 7)
- B1. Given an `inbox.jsonl` and `escalations.md` with emoji, accents and `<`/`|` characters, When `squad-inbox list --json` runs on Windows or in a simulated Windows run, Then it exits 0 and lists every item; the mod shows no `squad-inbox list failed` line. (story 7)
- B2. **`import fcntl` must not run on Windows** (`bin/squadinbox.py:8`; likely the cause of the PO's traceback, see spec F1). The write lock (`:195-214`) uses an OS-appropriate lock (Tech Lead picks; `msvcrt.locking` or a lock-file). Check on Linux: with `fcntl` hidden (`sys.modules['fcntl']=None`) the CLI imports and runs. (stories 7, 9; this is not a UTF-8 item, so the ticket title and the Developer must cover it)
- B3. Given two writers at once (`squad-inbox add` and `answer`), When both finish, Then every row from both is present exactly once and no line is half-written; same guarantee as on Linux. Linux proof: 2 writers x 50 rows with `fcntl` hidden = 100 rows, none doubled, every line valid JSON; this proves the fallback logic only, the real Windows lock is checklist W9. (story 9)
- B4. `answer` with a text or note holding emoji: the `escalations.md` row and the `inbox.jsonl` answer event hold it byte-identical. (story 8)
- B-LF. Files `squadinbox.py` writes (`inbox.jsonl`, `escalations.md`; the label and process files are T2c, ticket 06) use `\n` only and UTF-8: no `\r\n` from text-mode writes. **Windows-only proof** (CR counts on the PO checklist); a Linux test of the write call is a technical check, not business proof. (story 6)

## Technical AC (Tech Lead; design.md D1-D4)
Depends on T0 (`squadio.py`).
1. `squadinbox.py` imports with `sys.modules['fcntl'] = None` (no `ModuleNotFoundError`); `squad-inbox` calls `squadio.utf8_stdio()` first in `main`.
2. Lock per D3: Windows branch `msvcrt.locking` byte 0, seek 0, unlock before close, timeout raises `Refused(..., 1)`; Linux `flock` path untouched. The branch is chosen by `fcntl is None`, not `os.name`. Test: fcntl hidden, fake `msvcrt` backed by `fcntl.flock` (as a `sitecustomize`/`PYTHONPATH` module, real processes), 8 concurrent `squad-inbox add` processes: all 8 rows present once, no half line. The fake counts calls to a file; the test asserts `LK_LOCK` and `LK_UNLCK` counts are at least 8 each, so it cannot pass without the Windows branch. A second test: the fake `locking` raises `OSError` and the CLI exits 1 with the Refused text.
3. Both `os.open` calls (`append_events`, `locked`) pass `getattr(os, "O_BINARY", 0)`; test sets `os.O_BINARY` to a sentinel (monkeypatch, `raising=False`) and asserts the flag reaches `os.open`.
4. The nt branch keys off a module constant `IS_WINDOWS = os.name == "nt"` that tests patch. `stdin_text(only_if_ready=True)` returns `""` without calling `select` when it is true; POSIX behaviour and its existing tests unchanged. Second test (design D4): with `IS_WINDOWS` forced true, `answer E1 --source pane` with the text on stdin and no `--note` (`only_if_ready` false) records that text; and `answer E1 --note x` with an open empty stdin pipe returns, never hangs.
5. Every text open in these files names `encoding="utf-8"` (D2), writes `newline="\n"` through `open(...)`, not `Path.write_text` (design D2). (`read_text`, `atomic_write`, `set_answer_cell` and any `print` path.)
6. Under `PYTHONUTF8=0 LC_ALL=C PYTHONIOENCODING=cp1252`: `list --json`, `add`, `answer --note` on an item with `→ 🦀 é < |`: exit 0; the `inbox.jsonl` line and the `escalations.md` row compared as **bytes** to the expected UTF-8; no `\r` anywhere in either file.
7. Existing `test_squadinbox*.py`, `test_po_inbox_contract.py` pass unchanged on Linux.

## Comments
