Status: ready-for-agent
Blocked by: none
Task ID: PI-01
Files touched: `bin/squad-inbox` (new), `bin/squadinbox.py` (new), `tests/test_squadinbox.py` (new), `tests/fixtures/inbox/` (new)

# PI-01: `squad-inbox` store: add, list, read, sync, escalation projection

**Done when `squad-inbox add` writes read items and well-formed escalation rows, and `squad-inbox list --json` returns the version-1 contract of `design.md` for a home that mixes `inbox.jsonl` and `escalations.md`.** Design: `design.md` → Store, Options cell format, The contract, CLI (grep those headings). Business AC: B-03, B-04, B-06, B-07, B-09..B-11, B-22, B-24, B-25, B-27, B-33, B-35.

## What to build
- `bin/squad-inbox`: thin argparse script (the `bin/squad-process` pattern: `sys.path.insert` to its own folder, `import squadinbox`); logic in `bin/squadinbox.py`.
- Commands of this ticket: `add`, `list`, `read`. (`answer`, `withdraw`, `delivered` are PI-02; leave the argparse sub-commands out.)
- `list` syncs `seen` events into `inbox.jsonl` (under the `flock` lock) unless `--no-write`; folds the log; returns items in the contract's order; `errors` for a malformed file or row.
- A local copy of the board's table reader (`read_first_table` + `clean_cell`) in `squadinbox.py`; a test runs both on the same fixture (load `bin/squad-board` with `importlib.machinery.SourceFileLoader`, read-only) and asserts equal rows.
- Options parser per the design; ids per the design (`E<n>`, `R<n>`, row `key`).
- Every item field is passed through unchanged in the JSON; control-character stripping is the mod's job, not the CLI's.
- `SQUAD_INBOX_NOW` replaces the clock; home resolution `--home`, `$SCOPE_DIR`, `$GOAL_DIR`.

## Technical AC
1. **Real samples first.** `tests/fixtures/inbox/home/escalations.md` includes a verbatim copy of the three rows in `.claude/squads/plugin/scopes/po-inbox/escalations.md` (real Options cells with `:` and `;` inside), plus: an empty-Answer row, a hand-answered row, a blank row, a row with `\|` in a cell, a row with no `#`, a duplicate `#`, a malformed (missing cells) row. Also an empty-file case and a file with no table.
2. `add --kind read` appends one `add` line; the file is valid JSONL; ids `R1`, `R2` in order; two concurrent `add` processes (spawn 8) produce 8 distinct ids and 8 valid lines.
3. `add --kind answer` appends one row at the **top** of the table body (newest first, as the file header says), next free `#`, today's date (`SQUAD_INBOX_NOW`), `|` escaped, newline as `<br>`; the rest of the file is byte-identical; the board's reader parses it back to the same text.
4. `add` refuses, exit 2, message names the problem, **file bytes unchanged**: no title, empty/whitespace body, kind `approve` (and any other), `SQUAD_ROLE` unset or not `manager` (B-03, B-04).
5. `add` prints exactly one line `1 new item in the inbox: <title>` on success (B-02 partner), nothing of the body.
6. `list --json`: every item has every key of the contract (a test checks key sets per item and `null` for absent); `counts` right; order right (blocking first, then oldest first; done newest first by handled time); item with `blocks` empty has `blocks: ""` and sorts as not blocking.
7. Options: `(a) x; (b) y` → two choices; `(a) only one` → `options: null`; `(b) x; (a) y` → `options: null`; a cell with `(a)` inside prose (`see (a) above`) → `options: null`; letters beyond `c` work in order.
8. Sync keeps a deleted row: run `list`, delete the row from the file, run `list` again: the item is still listed, `done.kind: removed`, with title/body/options from the `seen` snapshot (B-27). A row whose `#` is reused by a different row later gets a different id and the old item is unchanged (B-33).
9. `read R1`: item becomes `done` kind `read` with the time; opening (`list`) never clears (B-11); `read` on an `E` id or a missing id exits 2; `read` twice exits 3, first stays.
10. A hand-answered row (Answer cell, no event) → `done.kind: answered-file`, `flags` contains `answer-by-hand`.
11. Malformed row / malformed JSONL line: `errors` has `{file, row, message}` naming the file and the row/line; other items still listed; exit 0 (B-35).
12. `list` with no `inbox.jsonl` and no `escalations.md`: zero items, no error, files not created by `--no-write`.
13. `--no-write` writes no byte (compare file hashes and mtimes).
14. Ids validated `^[ER][0-9]{1,6}$`; `read ../../x` exits 2 (no path use).
15. Python 3.9-safe, stdlib only, no `.pyc`; `python3 tests/run_suite.py --receipt <dir> --if-changed <base>` green.

## Added after QA whitebox review (round 1, `evidence/qa-w-ac-review.md`); these bind
16. **AC3 tightened (W1-W3):** the row writer maps every line break `str.splitlines()` splits on (`\r\n` as one, `\n`, `\r`, `\x0b`, `\x0c`, `\x1c`-`\x1e`, `\x85`, U+2028, U+2029) to `<br>`, escapes `|`, and writes a space before the closing pipe. One test per character, plus text ending in `\`, `\\`, `\|` and `|`; after each, the board's `read_first_table` returns the same number of rows and cells as before plus the one new row. "Parses back" means structure; the item's `body` is the raw cell (not `clean_cell`: `**` and backticks kept).
17. **Row key (W8):** `key` hashes the raw unescaped trimmed cells; a test edits a question's text and asserts the item becomes `removed` and a new id appears. `add --kind answer` takes `#` = above max of the file's `#` cells and every `E<n>` ever logged: delete rows 1..3, add one, its `#` and its id are equal and are 4 or more (W7).
18. **Sync is idempotent (R3):** a second `list` writes zero bytes (file hash and mtime). Run `list` with no `inbox.jsonl`: the lock file may exist, `inbox.jsonl` is created only when there is something to record.
19. **Races (R1):** the 8 concurrent `add` processes of AC2 start on a barrier (shared start file or `multiprocessing.Barrier`) and the round runs at least 20 times; assert distinct ids and valid lines each round.
20. **Stdin (R5):** `add` with `stdin=DEVNULL`, with an empty pipe and with a pty exits 2 (empty body) and never hangs; body over 64 KiB exits 2, file unchanged (M8).
21. **Title (M6):** `add --title` with a newline, `\r` or a control character stores the title collapsed to single spaces; a test asserts no line break in `title` of the JSON.
22. **Contract (C1, C2, C5, C6):** `created` is ISO-8601 always, with `created_precision` `day` for escalation rows and `second` for log items; `flags`, `state`, `kind`, `done.kind`, `answer.source` use only the closed sets of `design.md` → The contract (a test asserts it over the fixture home); `counts` equals the counts derived from `items`. The fixture home produces **every** combination of (kind, state, done.kind, flag) the contract allows, with `SQUAD_INBOX_NOW` pinned so output is stable.
23. **Repair (W5 partner):** a row whose key has an `answer` event and an empty Answer cell: `list` fills the cell (PI-02 writer); `list --no-write` does not and still reports `answered-waiting`. (If PI-02 is not merged yet, this AC moves to PI-02: coordinate in the same Developer.)
24. **Python (K4):** a test runs `ast.parse(src, feature_version=(3, 9))` on every new Python file and rejects `X | None` annotations and `match`.
25. **`--no-write` repairs nothing (AC13 extended):** with a row that has an `answer` event and an empty Answer cell, `list --no-write` writes no byte (hashes and mtimes of both files) and still reports `answered-waiting`; a plain `list` repairs it, and a second `list` then writes 0 bytes (a repair counts as a write for AC18).
26. **Live row wins (QAW round 2 F1):** while an answer item's row still exists, `title`, `body`, `options`, `recommendation` and `blocks` come from the live row on every `list`; the `seen` snapshot is used only after the row is gone (flag `row-removed`). Test: edit options and blocks in the file, the next `list` shows the new values. (The key is date + question, so editing the question is still `removed` + a new id.)
27. **Every log line validated (F2):** in `read_log` each event has `ev` in the known set and `id` a string matching `^[ER][0-9]{1,6}$` (`key` a string for `seen`); otherwise an `errors` entry names `inbox.jsonl` and the line, the other items are listed, exit 0. One test case per event type with a missing or odd id (including an integer id), plus a real item still listed.
28. **Duplicate answer add (F3):** `add --kind answer` with the same date + question key as an existing row exits 3, the message names the existing item id, nothing is written. Test it.
29. **Short rows (QAW question, decided: tolerate):** a row with fewer cells than the header is an item when it reaches the question cell; the missing trailing cells are empty (as `squad-board` does, so the pane and the board agree on the hand-written shape). A row that stops before the question cell, or has more cells than the header, is an `errors` entry. Adjust the malformed-row fixture and the existing test, and add a test with the Answer cell absent (state `open`, no error).


## Added after QA blackbox PI-04 O4 (TL ruling)
- **AC26 (B-04):** an argument or stdin that holds invalid UTF-8 (a lone surrogate from `os.argv`, invalid bytes on stdin) is refused like any other bad input: exit 2, one stderr line naming the option, nothing written, no traceback. Test for `add --title`, `--body-file` and stdin; `answer`/`withdraw` text options get the same check.
