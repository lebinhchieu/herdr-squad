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

### Tech Lead amendment (2026-10-17) — binding
- **Design:** in `read_body`, after `decode_utf8`, `return text.replace("\r\n", "\n").replace("\r", "\n")`. It is shared code, so a stdin body is normalised too (answers AC 4). `cell_text`/`BREAK_RE`, `rstrip("\n")` and the 64 KiB byte limit stay. The `answer` text is not touched.
- **TB1** input `b"line one\r\nline two\r\n\r\n- bullet\r"` (written with `write_bytes`) stores `"line one\nline two\n\n- bullet"`: no `\r` in `inbox.jsonl` or `list --json`.
- **TB2** same for a stdin body, and for a lone `\r` mid-text.
- **TB3** an `--kind answer` item with a CRLF body: its `escalations.md` row has one `<br>` per line, no trailing `<br>`, no `\r` byte.
- **TB4** an LF-only file is byte-identical to before; existing `test_body_file` and size-limit tests pass (run them, do not edit them). All new tests fail on 59a8d1b.

- BA AC (spec.md "Iteration 2", story 15): an empty or only-CRLF body is still refused as on 0.3.3; answer-note, title, options and rec are out of scope.
