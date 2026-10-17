# B `--body-file` stores LF only

Status: ready-for-agent
Type: task
Source: `issue-po-inbox.md` section 3
Touches: `bin/squadinbox.py`, `tests/test_squadinbox_body_crlf.py` (new; do NOT edit `tests/test_squadinbox*.py`, task 13 owns them)
Blocked by: none. Parallel with 09, 11, 12.

## What
When `--body-file` is read, normalise `\r\n` and lone `\r` to `\n` before the `<br>` conversion. Today a CRLF file is stored as `'line one\r\nline two\r\n\r\n- bullet\r'` and the answer row ends in a stray `<br>`.

## Technical AC (Tech Lead)
1. New test: a body file written as bytes with CRLF, and one with lone CR, store the same text as the LF file; the escalation row has no `\r` and no trailing `<br>` from a final CR.
2. An LF-only file stores byte-identical to before.
3. Runs under `PYTHONUTF8=0 LC_ALL=C` too; `tests/test_windows_safe.py` still passes.
4. Stdin bodies are untouched unless the same normalisation is already shared code (state which in the hand-in).

## Comments
