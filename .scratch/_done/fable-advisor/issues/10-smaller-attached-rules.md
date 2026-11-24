# 10: Smaller attached rules
Status: blocked (waits for 04 and 07; Tech Lead added first, SIZE-13)
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: after wave 2
Files: `bin/squadcompose.py`, rule index generation, the rule files `roles:` / `when:` headers, tests for compose
Source: idea 4 plus finding 12 (shorten the index, about 200 lines). Measure before and after with `squad-usage` and ticket 07's report.

## Business AC
1. The attached rules of a role no longer include rules for phases it is not in; those print when the phase starts: merge rules from `squad-merge-check`, close rules from `squad-close`, Coach rules at Coach spawn.
2. The rule index shrinks; CORE-6 `squad-process rule <ID>` still finds every rule.
3. No role loses a rule it needs to act: a contract test lists, per role, the rules it must have attached.
4. Before and after: attached lines per role in the evidence.
