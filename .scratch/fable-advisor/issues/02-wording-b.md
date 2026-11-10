# 02: Wording fixes B (Manager PASS, QA blackbox, irreversible choice, when-keys, citations, small items)
Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, suite-owner=qa-white, promote-owner=qa-white. Test economy: targeted tests only; full suite only after the PO's yes via the Manager (CLAUDE.md Running tests).
Lane: W (after 01)
Files: `templates/squad/process/*.md`, the two rules tests
Source: findings 2, 3, 4, 7, 10, 12 in `review-findings.md`. Do NOT shorten the rule index here (ticket 10 does).

## Business AC
1. EVID-3a says the Manager's confirmation (no `PASS`) is the verdict, consistent with REV-1, TEAM-3, LC-27.
2. QA blackbox: one rule on shots vs the running app. Shots are a starting point; blackbox runs the app for every AC a shot does not clearly prove and never signs off from shots alone. REV-9, SIZE-8b, SIZE-17d, START-13 agree.
3. One rule for an irreversible choice: Architect/Tech Lead/Manager recommend, the PO decides; it cites a row that is always attached.
4. Finding 7: ITER-3b, EVID-2b/2d/2e and REV-14a use the right `when:` key and the evidence-only-commit exception (MRG-2) is stated.
5. Finding 10 citations fixed (ITER-2, ITER-17, CORE-3, GOAL-6b, SUITE-1b, SUITE-2d, SIZE-24b).
6. Finding 12: MSG-8a and SPAWN-10a agree (10 minutes before a ping); suite rules say "default is targeted; a full run needs the PO's yes"; "Chieu" in generic templates becomes "the PO"; MSG-9 example uses a bare `NN`.
7. `squad-process lint` clean; the two rules tests pass.
Since 2, 3 and 4 change what QA and the Manager do, QA whitebox and blackbox check them.
