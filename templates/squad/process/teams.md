# Team variants

## TEAM-1 Passed, QA whitebox alone
roles: manager, ba, team-lead, tech-lead
when: qa-white = yes and qa-black = no
topic: teams

Passed = every checker on the team has passed the task: QA whitebox PASS, and with a Designer the built-UI check. QA whitebox checks the Developer's `## Behaviour` against the business AC, so one PASS is enough here and no other is awaited.

## TEAM-2 Passed, QA blackbox alone
roles: manager, ba, team-lead, tech-lead
when: qa-black = yes and qa-white = no
topic: teams

Passed = every checker on the team has passed the task: QA blackbox PASS and, with a Designer, the built-UI check. The Developer's `## Review` is confirmed by its owner ([SIZE-22]), who sends no PASS.

## TEAM-3 Passed, no QA
roles: manager, ba, team-lead, tech-lead
when: qa-white = no and qa-black = no
topic: teams

Passed = the HANDIN evidence check exits 0 ([LC-27]): `evidence.md` and `## Review` exist. The code-check owner ([SIZE-22]) still reads both and sends `FAIL` on a problem, never `PASS`. There is no QA PASS to wait for.

## TEAM-4 Behaviour check, QA whitebox
roles: qa-whitebox
when: behaviour-check = qa-white
topic: teams

No QA blackbox is on the team: you check the Developer's `## Behaviour` in `evidence.md` against the business AC, as well as the code and the tests.

## TEAM-5 Business AC, BA alone
roles: ba
when: business-ac = ba and qa-black = no
topic: teams

The BA owns the business AC and writes them alone; QA whitebox checks the Developer's `## Behaviour` against them.

## TEAM-6 Code check, Tech Lead
roles: tech-lead
when: code-check = tech-lead
topic: teams

No QA whitebox is on the team: confirm that each task's `evidence.md` holds a `## Review` from the Developer's review subagent, and read what it found.

## TEAM-7 Removing a role
roles: manager
topic: teams

Remove a role only at an iteration boundary with the PO's OK. Its duties move along the chain, its open threads go to the new owner (the `## Handover` names it). Run `squad-team remove <role> --at-boundary`: it edits `team:` and prints who to respawn. Retire the removed role's session. Tasks already passed stay passed; unfinished tasks use the new rule.
