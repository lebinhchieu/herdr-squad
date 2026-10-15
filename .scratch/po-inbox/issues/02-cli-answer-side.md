Status: ready-for-agent
Blocked by: 01 (same `squadinbox.py` and `test_squadinbox*.py`; same Developer, no respawn)
Task ID: PI-02
Files touched: `bin/squad-inbox`, `bin/squadinbox.py`, `tests/test_squadinbox_answer.py` (new), `tests/fixtures/inbox/`

# PI-02: `squad-inbox` answer, withdraw, delivered, and the Answer-cell writer

**Done when a PO answer is recorded once, written into the row's Answer cell without breaking the table or the board, refused when it is the second, empty, or lost to a withdraw, and a delivery is recorded.** Design: `design.md` → Writing an answer into the row, CLI, Store (State and first writer wins). Business AC: B-12..B-18, B-23, B-26, B-32, B-34.

## What to build
- `answer E<n> [--option K] [--note N | --text T | stdin] --source pane|chat`, `withdraw E<n>|R<n> --reason R`, `delivered E<n> --session S`.
- The Answer-cell writer: locate the row by `key`, replace only that cell (`|` → `\|`, newline → `<br>`), write a temp file in the same folder, `os.replace`, all under the lock; re-read the file immediately before replacing.
- Answer text for a picked option: the stored `text` is the option key and its text then the note, in the format `(a) <option text>` + `\n` + note when a note exists; `option` and `note` are also stored separately. The prompt text for the Manager is built by the mod from the stored `text`.
- `--source chat` marks done at once (no `answered-waiting`) and sets `delivered_ts` to the answer time.

## Technical AC
1. `answer` on an open `E` item with options and `--option b --note "x"`: event has `option b`, `note x`, `text` as above; Answer cell filled; state `answered-waiting`; `list --json` returns the exact text back.
2. Free-text answer on an item without options works (B-13); `--option` on an item without options exits 2; an unknown option key exits 2; nothing written in either case.
3. Empty or whitespace-only answer, and `--option` absent with an empty note, exit 2; item stays open (B-32).
4. **Text round-trip (B-14, B-23):** answers containing several lines, `|`, `\|`, backticks, `**`, quotes, tabs, `<br>`, CRLF, emoji and non-ASCII are stored in the event byte for byte (`json.loads` equals the input) and shown unchanged in `list --json`; the escalations table still parses with the same number of rows and cells (board reader), and every other line of the file is byte-identical.
5. Second `answer` on the same item exits 3 and names the first answer and its time; the first stays (B-17). `answer` after `withdraw` and `withdraw` after `answer` both exit 3 naming the winner (B-34).
6. **Race:** 10 concurrent `answer` processes for one item: exactly one exit 0, nine exit 3, one `answer` event, one filled cell. A `withdraw` racing an `answer` likewise.
7. `answer` for an item whose row was deleted (state from `seen` snapshot): the event is recorded, no cell can be written, the exit is 0 with a warning line on stderr, state `answered-waiting`; the answer is not lost.
8. `withdraw E<n> --reason R` fills the cell with `withdrawn: R` (board treats it as answered); `withdraw R<n>` only appends the event; an empty reason exits 2; state `done` kind `withdrawn` with the reason (B-26).
9. `delivered E<n> --session S`: state `done` kind `answered` with `delivered_ts`; calling it for an item without an answer exits 3; calling it twice exits 3 and keeps the first time.
10. `answer --source chat` → `done` kind `answered`, `answer.source: chat`, never `answered-waiting`; same refusals as pane (B-18 partner).
11. Role guard: `answer`, `withdraw`, `delivered` with `SQUAD_ROLE` unset exit 2, nothing written. `answer` with a failing write (read-only folder, simulated) exits 1, no event appended (event only after the cell write; if the cell write fails the answer is not recorded).
12. The temp file is never left behind (success or failure); file permissions of `escalations.md` are kept.
13. A `delivered` for an item with no answer exits 3 (a state conflict, like twice-delivered; matches AC9); an `answer` for `R<n>`, or `delivered` for an `R<n>` or a malformed id, exits 2 (usage). Rule: 2 = wrong input, 3 = right input, wrong state.
14. Suite green with a receipt; Python 3.9-safe.

## Added after QA whitebox review (round 1); these bind and replace where they conflict
- **AC11 replaced (W5): order is event first, then cell.** (Its role-guard half stays binding: with `SQUAD_ROLE` unset, `answer`, `withdraw` and `delivered` exit 2 and write nothing.) Under the lock: append the `answer` event, then write the cell. A failing cell write (read-only folder, symlink, no `answer` header, duplicate key, short row) exits **0 with a warning on stderr** (cell not written), like AC7: the answer is recorded, state `answered-waiting`, never lost. Fault-injection test: patch the cell write to raise (and a second test: kill between the two) and assert the item ends `answered-waiting` and a following `list` fills the cell; never `answered-file`. The same order for `withdraw`.
15. **Writer matrix (W1-W4):** the cell writer works in bytes. Cases, each comparing the whole file byte for byte except the one cell: LF and CRLF files; no final newline; invalid UTF-8 bytes elsewhere in the file (preserved, not U+FFFD); Answer column not last and found by header; row shorter than the header; no `answer` header (no cell written; exit 0 + warning, answer recorded, per AC11); two rows with the same `key` (no cell written, warning names both rows); symlinked `escalations.md` (not replaced, warning says so). Text cases: every line break `splitlines()` splits on (as PI-01 AC16), text ending in `\`, `\\`, `\|`, `|`; the board reader returns the same row and cell counts each time.
16. **AC4 clarified (W2):** "shown unchanged" is compared against the `answer` event text, not the cell; the table check is structural (rows and cells).
17. **Races (R1, R2):** the 10 racers and the answer-vs-withdraw pair start on a barrier; the round runs at least 20 times, also on a home with no `inbox.jsonl`; after each round: one `answer` (or `withdraw`) event, one filled cell, and the cell equals the winner's text.
18. **Hand answer (W6):** `answer` on a row whose Answer cell was filled by hand (state `answered-file`) exits 3 and names it; `answer` on a `removed` open item records the event (AC7).
19. **Stdin (R5):** `answer` reading stdin with `stdin=DEVNULL`, an empty pipe and a pty exits 2 and never hangs.
20. **Stdin meaning (PI-03 contract; AC19's exit 2 on empty stdin applies only without `--option`):** with `--option K` and stdin, the stdin text is the note (empty stdin = no note, still a valid answer); without `--option`, stdin is the free text. `--note`/`--text` together with a non-empty stdin exits 2. A test pins the PI-03 call `answer E<n> --option K --source pane` with the note on stdin, and the same without `--option`.
21. **`options_raw` (PI-04 ask, TL ruling):** every item in `list --json` has `options_raw`: the raw Options cell text (as read, `\|` unescaped, trimmed) when the cell is non-empty and could not be parsed into `options` (`options` is `null`); otherwise `null`. Test with a fixture row whose Options cell is free prose, one in the option format (`options_raw` null), one empty (both null), and a read item (null). Files: `bin/squadinbox.py` and the `list --json` contract fixtures; design.md has the line.


## Added after QA blackbox FAIL F1 (round 1, at 05fa3b0); binds and replaces where it conflicts
- **AC15 replaced for a short row (QAB F1, BA upheld):** a row with fewer cells than the header is a valid open item (PI-01 lists it, as the board reads it). The cell writer **pads that row with empty cells up to the header width**, then writes the Answer cell; every other cell and line of the file stays byte-identical. A row with more cells than the header, no `answer` header, two rows with the same `key`, a symlinked file or a row that cannot be written as bytes keep the refusal. `design.md` → "Writing an answer into the row" says the same.
- **Never silent (QAB O1, BA):** whenever the cell is not written (every refusal above, also invalid UTF-8 inside the row's own text), the exit stays 0 and the stderr warning stays, and the item in `list --json` carries the flag `cell-not-written` (next to `answer-by-hand` / `row-removed`; `design.md` flags line updated). The flag clears when a later `list` repairs the cell. Tests: short row (padded, board `needs_you` drops it, other bytes identical, with a 3-cell row under a 7-column header and the Answer column in the middle and last); one refusal case per reason shows the flag.
- **Clean refusal (QAB O2):** `answer`/`withdraw`/`delivered` in a folder that cannot be written (e.g. `inbox.jsonl.lock` PermissionError) exit 1 with one stderr line naming the file, no traceback, nothing recorded. Test with a read-only folder.
- Not changed: the `inbox.jsonl.lock` file stays next to `inbox.jsonl` (O3); the stdin rule of AC20 stays (O4).
