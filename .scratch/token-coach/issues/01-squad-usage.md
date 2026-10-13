# 01 squad-usage report

Status: resolved
Blocked by: none

Python script `bin/squad-usage`, tested in `tests/`. It reads the transcripts of the session ids listed in `roster.md` and prints a one-screen table per agent: model and effort, turns, peak and last context size (input + cache read + cache write), output tokens, cache expiries (a gap of more than 1h followed by a large cache write), and compactions.

## AC
- Given a fixture transcript, the table shows the correct totals.
- A cache expiry is detected from a gap of more than 1h.
- `--check <session>` returns the rule that fired, or nothing (used by 04).

## Comments

- Added `bin/squad-usage` (Python stdlib) and `tests/test_squad_usage.py` (9 tests, fixture transcripts built in code).
- Table: model/effort, turns, peak and last context (with % of window), output tokens, cache expiries, compactions. Reads `roster.md` rows that have a `Session` column; finds transcripts at `${CLAUDE_CONFIG_DIR:-~/.claude}/projects/*/<sid>.jsonl`.
- Also has `--set-session NAME SID` (upserts the roster row, adds the column) so 03 and 05 reuse the roster parsing.
- `--check SID [--transcript F]` prints `fresh` (context >60% or any compaction), `idle` (last turn >1h ago and context >100k), or nothing. Step-up is judgment, not checked.
- Assumptions: messages are deduped by `message.id` (last line wins); sidechain and `<synthetic>` lines skipped; window 200k, 1M if the model id contains `1m`; expiry = gap >1h and cache write >=10k; compaction = `system/compact_boundary` or `isCompactSummary` line (not seen in local transcripts, so unverified against real data).
- Test: `python3 -B -m unittest tests.test_squad_usage` → 9 tests OK.
