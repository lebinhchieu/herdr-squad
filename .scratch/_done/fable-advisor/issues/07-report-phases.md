# 07: `squad-report` phase breakdown per ticket
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Cite: [REV-15] report deliverable: copy it to `$SCOPE_DIR/evidence/<task>/` at the sha handed in.
Lane: B (then 08)
Files: `bin/squadreport*.py`, `bin/squad-report`, tests for squad-report (`grep -rl squadreport tests/`)
Source: idea 11. First read what the logs (`messages.jsonl`, ledger, usage) record per phase. If a phase cannot be measured, say so in the report; never invent numbers.

## Business AC
1. The report's data and HTML show, per ticket, turns and tokens per phase: spawn, build, HANDIN, each QA check, returns. A phase with no data shows "n/a".
2. The digest (`squadreport_digest.py`) carries the same table so the Coach can read it without transcripts.
3. Mango Parrot light palette in HTML (project.md); existing report tests pass; one new test for the table on a fixture scope.

## Technical AC (QA whitebox; agreed with dev-b in design notes, amend there)
T1. Data source per phase is written in `evidence.md` as a table: phase | field/file it reads | measurable yes/no. Each measurable phase reads a real recorded field; "n/a" appears only when the source has no record for that ticket and phase. No estimated or interpolated value, no default 0 for a missing source (0 and n/a are different outputs).
T2. Real samples (REV-4): run on two real scopes' logs read-only (a finished scope with returns and a scope with a ticket still open), including a ticket with no QA phase. I also run it once on live data.
T3. Payload shape (REV-6): in the data JSON every ticket row has every phase key, each value is `{turns, tokens}` or `null`/"n/a" by one fixed convention; the same shape in the digest table. Closed phases have an end; a phase with a start and no end is "n/a" or marked open, never negative or huge. A test checks all rows for all keys, not only totals. Existing readers of the data JSON (`squadreport_rollup.py`, `squadreport_query.py`, `squadboard*`) still work: `grep -rn` for consumers and run their tests.
T4. Rollup: `squad-report rollup` and `query` either carry the new field safely or ignore it; a data file from before this change (no phase key) still loads (back-compat test with a fixture from `tests/report_fixtures.py`).
T5. HTML: colours come only from the Mango Parrot light theme tokens already in the report CSS (no new hex outside that set; `grep` the diff for new `#rrggbb`); no dark theme; `n/a` readable. Visual check belongs to QA blackbox (REV-18a); I only check the code for no new colours.
T6. Digest: `squadreport_digest.py` adds the table within the digest's existing size cap; a test asserts the table rows match the data for the fixture scope. Redaction (`--redact`) still hides what it hid before (test or fixture).
T7. Tests: one new test for the table on a fixture scope (AC3) extends `report_fixtures.py` / an existing report test file. Run: that file, `grep -rl squadreport tests/` hits (collect, digest, tasks, rollup, query, ui, cli, html, embed). Existing ones pass, none skipped. Full suite not run by the Developer.
T8. No new dependency, no network; `squad-report` on a scope with no task data still exits as before (exit codes unchanged).
T9. Token and turn counts are summed from the same source the existing per-ticket totals use, so the phase sum is at most the ticket total (test asserts this on the fixture); the difference is shown or not hidden.
