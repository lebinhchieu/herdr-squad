# squad-report backlog (from iteration 1, ticket 10 dropped)

Status: needs-triage

## Collect / data
- 01: `iter_records` returns extra keys.
- 02: a stale unanswered ASK keeps counting as blocked.
- 02: prices are fitted from cost-state, not a list; other Claude accounts' transcripts are invisible.
- 03: legacy alias task ids show as separate rows.

## Query / CLI
- 07: `--top 0` falls back to 5.
- 07: `blocks` cap per segment is untested.
- 07: `role --role` ignores `--top`.

## Report HTML
- 05: Elapsed KPI legend clipped.
- 05: drawer returns table cut off.
- 05: blocks shown as cards.
- 05: iteration table lacks a Tasks column.
- 05: longest blocks includes waiting.

## Rollup
- 06: skipped rows show folder name, not file name.
- 06: calendar strip (Could) not built.
- Task x role grid and per-agent timeline (Could) not built.

## Process
- Developer cap is a rule, not a lock (nothing stops an over-cap spawn).
- Tests that several tickets edit (e.g. test_squad_report_cli.py) conflict at integration; split per ticket.
- Stale bin/__pycache__ broke suite run 1; test_ca_autoswitch timing flake (899 s).
