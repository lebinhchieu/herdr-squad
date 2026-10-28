# Ticket 11 AC amendment (Tech, from QAW INT3 note)

Add under "Added (Tech DECISION)" in `.scratch/drop-scope-size/issues/11-dev-cap-sweep-and-trim.md`:

Added (QAW INT3 note): four skipped tests carry "5 KiB trim is ticket 11" (`test_dev_rules_size` x3, `test_sizes` x1). Un-skip all four; today they fail (S 5196 B, M+arch 5124 B > 5120). The PINNED values are stale (real 5522/5521/5226/5225): re-pin or delete them per design 09. `grep -rn "ticket 11" tests/` returns no skip at HANDIN.

Ticket 12 AC mirror: at cutover `grep -rn "ticket 11" tests/` finds no skip.
