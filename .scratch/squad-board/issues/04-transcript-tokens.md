Status: ready-for-agent
State: done
Task ID: BRD-04
Blocked by: 01
Files touched: `bin/squad-board` (only the `tokens` section), `tests/test_board_tokens.py` (new)

# BRD-04: transcript token reader

**Done when each column's `context_tokens`, `tokens_in`, `tokens_out` and `model` come from the agent's transcript in the fixture, and are null when the transcript is missing or bad.**

Read first: design.md "Tokens"; spec stories 33–40 and "Transcript token reader". Replace the body of `read_tokens` only. Look at one real transcript (read only) to confirm field names before writing fixture lines; fixtures contain synthetic data only.

## Technical AC (BRD-04)

1. **Totals:** two assistant replies with known usage → `tokens_in` = sum of (input + cache_creation + cache_read), `tokens_out` = sum of output, `context_tokens` = in of the last reply, `model` = last reply's model. Exact numbers.
2. **Duplicate `message.id` lines count once**, last line wins.
3. **`<synthetic>` model** is skipped for `model`; non-assistant lines and lines without usage are ignored.
4. **Missing transcript, session id not in `herdr.json`, bad session id** (`../x`, spaces), unreadable or all-garbage file, a file with no usage lines → four nulls, `/state` 200, empty stderr. Other agents' tokens unaffected.
5. **Roots:** transcripts found under any `replay/claude*` folder; the same file reachable through two roots (symlink made in the test) is counted once.
6. **Incremental:** append a reply to the transcript between two `/state` calls → totals grow by exactly that reply (no double count); append a line without its trailing newline → not counted yet; add the newline → counted once. Verified by the second call's numbers, not by inspecting internals.
7. **Thread safety:** the offset cache is behind a `threading.Lock`; two concurrent `/state` requests give the same numbers (test with a few parallel requests).
8. **No file outside `replay/`** is read; session id is never used unvalidated in a path.
9. **Baseline AC 1 to 5, 7, 9, 10** from design.md "Technical AC".

### QA whitebox additions (qaw-board)
Q1. **Duplicate id across reads:** the first line of message id X is read, then a second line with the same id X is appended with different usage → totals reflect only the last, counted once (not just within one read). Also `context_tokens` follows the last reply by file position.
Q2. **Truncation or replacement:** the file shrinks or is replaced by shorter content between two `/state` calls → recomputed from scratch, no negative or stale numbers, no crash.
Q3. **Encoding and size:** invalid UTF-8 bytes in a line are skipped (`errors="replace"` or per-line try); a 1 MB single line does not hang; a usage field that is a string, negative, float or null counts as 0 or skips the reply (state which), never raises.
Q4. **Containment:** a symlink inside `replay/claude*/projects/` that resolves outside `replay/` is not read (realpath must start with the replay root). A session id of `a.jsonl`, an absolute path and a NUL byte are rejected by the regex.
Q5. **Fixtures synthetic:** grep of the added fixture files finds no `/home/`, no real session UUID from `~/.claude*`, no real text.
Q6. **Lock scope:** the lock covers the offset cache only, not file reads for other agents (QA reads the code); no global state besides the cache.

## Comments
- 2026-10-12 tech-board: PASS by qaw-board at c54d945 (squad/dev-board-5), after round 1 FAIL 465abf7. Decision: synthetic replies ignored entirely. Mid-file imports left for BRD-09 (AC 13a).
