# worktime fixtures (ticket 15)
Real Claude Code session records of this scope (shape, timestamps, `origin`, usage numbers kept), with every
text and tool input replaced by a constant (`x`, `ls`, `python3 tests/run_suite.py`) and the agent renamed.
- `normal.jsonl`: the first 24 timestamped records of a session, no gap over 1 h.
- `long-gap.jsonl`: the same kind of records with the real 11.2 h shape of architecture section 4: a `system` record
  ends the gap, so `_classify` calls it `working` + `stalled` (Claude Code night case). The records after the gap are
  copies of later records of the same session, shifted in time.
