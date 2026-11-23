# Upstream the squads' proposed rules

Status: ready-for-agent

## Why

Three squads hold `upstream: proposed` overlay operations (`squad-process upstream --squad-dir <dir>`): guardian (wpw), board and plugin. On 2026-11-24 Chieu agreed a review of all 37 against the plugin's rules:

- 13 were dropped from the overlays (already covered or clashing; logged in each squad's `process-log.md`).
- 6 merge into 2 new plugin rules (tickets 01, 02).
- 13 go upstream as new rules or edits (tickets 03-06).
- 4 stay local only: board SQ-7, plugin SQ-5, SQ-10, SQ-23. Not in this scope.
- plugin SQ-4 (finding tiers) waits on Chieu's decision. Not in this scope.

## Scope rules

- Rule text: plain English, one idea per sentence, under the 60-word lint limit.
- Every changed or added rule passes `python3 bin/squad-process lint`.
- Do not write numbers into a rule that the tools already hold: use the agent's `line` column from `squad-usage`, never a fixed 100k or 150k.
- New rules respect SAFE-6 (the Manager does no role's work) and SAFE-7 (the Manager never reads `_done/`).
- The last ticket that touches plugin files bumps the plugin version and the changelog (plugin SQ-5).
- When the plugin adopts a rule, `squad-process upgrade --check` on each squad lists its overlay op as adopted. Removing the op from the overlay is the squad's step after re-pinning, not a ticket here.

## Tickets

| # | Ticket | Sources |
|---|---|---|
| 01 | Read your usage row at commit and verdict | board SQ-5, plugin SQ-3c, SQ-3d |
| 02 | Squad-wide base failures file | guardian SQ-41, plugin SQ-15, SQ-17 |
| 03 | Developer stays until the evidence check is clean | plugin SQ-20, EVID-2d replace |
| 04 | Integration and merge by relation | plugin SQ-6, SQ-6b, SQ-7, SQ-7b |
| 05 | Planning and start checks | plugin SQ-1, SQ-8, SQ-21, SQ-22 |
| 06 | Small edits: rm, UI AC, notes pointers | guardian SQ-35, board SQ-8, SQ-9 |
