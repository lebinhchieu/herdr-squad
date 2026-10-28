# QA whitebox 03 — sha 0a9790a: FAIL (2 doc findings)

Checked: diff 3ce1fba..0a9790a (HANDOFF, README, SKILL only) against bin/cwake, bin/cautoswitch, bin/cswitch at 0a9790a. All behaviour claims match the code (clauses 1-3, marker/30 min, wake gap, 15 min in-flight skip, 60 s gate, WAKE SKIPPED lines, own/retired pane skip, text, CSWITCH_WAKE=off, dry-run, install state list, .gitignore). Unverified items are stated as unverified. Style: ok.

## F1 — checklist step 5 cannot be observed (HANDOFF.md:71)
Says the sender "should show `wake sent` with reason `failed-send` in its marker". After a wake, `cwake.wake` deletes the marker (`done()`, bin/cwake:252, log line :271) and the log line is `<ts> <pane> <name> wake sent` with no reason. So the PO can never see `failed-send` after the real tick; a `wake sent` could equally come from clause 1/3. The step is the one live sample of clause 2, so it must be doable.
Pass: give an observable route, e.g. before the tick finishes (or after the batch, before the wake) run `cwake --mark <sender> --clauses 2 --since <epoch of batch start>` and `cat ~/.claude-accounts/wake-pending/<sender>` -> `... failed-send`; or tell the PO to read the sender's transcript for the failed `SendMessage` and the wake prompt. Say which one proves clause 2.

## F2 — checklist step 2 "and nothing else" is wrong (HANDOFF.md:68)
`cautoswitch --once --dry-run` also prints the tick status line `HH:MM:SS ok: <ws> -> cN 5h..` (cautoswitch tick, print before the pane loop) and, over threshold, a `[dry-run] would set ... default` line. Pass: "prints `[dry-run] would cswitch ...` for that pane, no `wake`/`WAKE` line in cswitch.log, wake-pending unchanged".

Suite: full run on 0a9790a started (receipt in evidence/ when done); docs-only fix will need a re-check of changed files and a suite run on the final sha.

# Round 2 — sha bc4e1e7: PASS
Diff 0a9790a..bc4e1e7 = HANDOFF.md lines 68/71 only. F2 fixed (status line + `would cswitch` named, no wake line, wake-pending unchanged). F1 fixed: route (a) checked against bin/cwake: `--mark --clauses 2 --since` works after the wake (transcript survives, mark() writes marker, rm needed else next tick wakes: cautoswitch wake_step); route (b) sound. Non-blocking nit: nested backticks in item 5 render oddly.
Early suite on 0a9790a: 1449 tests OK (browser skipped by --if-changed). Final-sha run on bc4e1e7: see evidence/suite-default.txt.
