# E Integration and promotion (ADR 0011 D6 update)

Status: needs-triage (draft)
Type: task
Source: iteration 2
Touches: merge only; then `docs/adr/0011-plugin-runs-on-native-windows.md` (D6) and `.scratch/squad-plugin-windows/issue-po-inbox.md` (committed as the ticket source)
Blocked by: 09, 10, 11, 12 (all passed)

## What
Step 1 (integration Developer): branch from `59a8d1b`, merge the passed branches of 09-12, resolve conflicts (none expected), run touched tests, hand in; no code beyond merge fixes. Tech Lead then runs `--tz` on that sha.
Step 2 (promotion, same or a fresh Developer, based on the passed integration sha the Manager names): update ADR 0011 D6 from "mod unchanged" to "the mod runs `['python3', <root>/bin/squad-inbox, ...]`; checked by an argv test; real Windows pane check stays with the PO"; add D-notes for CRLF normalisation and skipped Windows-only tests; docs only.

## Technical AC (Tech Lead)
1. Receipt first line `sha <sha> clean=yes`, OK at the tail, `--tz`.
2. ADR edit changes only D6 and the "also true" list; docs only.
3. QAW and QAB record PASS on the exact final sha.

## Comments

### Tech Lead amendment (2026-10-17)
- ADR 0011 edits: D6 and the "also true" list (CRLF normalisation in `read_body`; Windows-only tests skipped with a reason). I write the wording in `promote.md`; the Dev copies it.
- Role-instruction change (ticket 11) is listed for the PO in the hand-in; the PO already approved it (E5).
- Receipt: `run_suite.py --tz` on the integration sha, then again on the promotion sha if it differs.

- BA AC (spec.md story 18): `windows-checklist.md` stays at 12 steps or fewer, copied from `evidence/iter2/windows-checklist.md`; W7 extended (answer from the pane, then `answer` event with `source: pane` and a `delivered` event in `inbox.jsonl`), W8 extended (one CRLF `--body-file`, CR count 0). Add the D command line from `tests/RUNNING-ON-WINDOWS.md`. Also read spec.md "For promotion". Only Windows proves A's host launch and D's 0 failures: the PO runs both.
