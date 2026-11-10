# 03: Three small rules: bundle small tickets, fresh Manager after a long wait, rule metrics
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: W (after 02)
Files: `templates/squad/process/*.md` (the rule files that fit: planning/lifecycle, cost, iterations), the two rules tests
Source: `improvement-ideas.md` ideas 5, 8, 10 (cards: https://claude.ai/artifact/WiPfRxuWB3HWPoKFegU5F5).

## Business AC
1. Bundle rule (idea 5): the plan owner may bundle 2-3 tickets of at most 2 files each, different files, into one Developer session, one `HANDIN` listing each ticket and sha, one QA pass, one verdict line per ticket. Both QAs still check every ticket (not SQ-9). One FAIL returns only the failed ticket.
2. Long-wait rule (idea 8): the Manager, after a wait for the PO longer than the cache lifetime, writes notes and runs `squad-respawn` before its next spawn or reply, at any context size. The Developer states the cache lifetime used and where it was verified (check with Claude docs or `squad-usage` data; if it cannot be verified, say so in the rule).
3. Experiment rule (idea 10): each rule added to a squad overlay names its metric and baseline; the Coach reads the metric at close; no change in 2 scopes means remove (the PO may keep one on purpose).
4. Each is one rule, stated once, with a rule ID that `squad-process lint` accepts; the two rules tests pass.
