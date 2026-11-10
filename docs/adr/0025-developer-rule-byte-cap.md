# 0025: The Developer rule byte cap is a gate, set at 5440 B

Status: accepted

## Context
`tests/test_dev_rules_size.py` holds the composed Developer rules of every team shape under `LIMIT`, so a Developer's start-up stays small. The cap was 5400 B. The check-table rules (ticket 09) did not fit.

## Decision
- The Tech Lead raised `LIMIT` from 5400 to 5440 B for ticket 09. The change is permanent and was listed to the PO at the check-in. The ceiling is 5480 B; going above needs the Tech Lead.
- After merging all lanes the measured maximum is 5433 B, so `LIMIT` stays 5440 (the measured maximum rounded up to 20 B).
- Ticket 10 does not lower it, because Developers get no rule index.
- Rules moved out of the Developer set (REV-5a, EVID-5) stay one `squad-process rule <ID>` away.

## Consequences
- A new Developer rule must be paid for in the same change by folding repeated wording, or the Developer asks the Tech Lead.
- The Manager's byte bases in the same test moved with the phase rules.
