# Team variants

## TEAM-1 Done, QA whitebox alone
roles: manager, ba, team-lead, tech-lead
when: qa-white = yes and qa-black = no
topic: teams

Done = every checker on the team has passed the task: QA whitebox PASS, and with a Designer the built-UI check. QA whitebox checks the Developer's `## Behaviour` against the business AC, so one PASS is enough here and no other is awaited.

## TEAM-2 Done, QA blackbox alone
roles: manager, ba, team-lead, tech-lead
when: qa-black = yes and qa-white = no
topic: teams

Done = every checker on the team has passed the task: QA blackbox PASS, and the Developer's `## Review` confirmed by its owner ([SIZE-22]). With a Designer, also the built-UI check.

## TEAM-3 Done, no QA
roles: manager, ba, team-lead, tech-lead
when: qa-white = no and qa-black = no
topic: teams

Done = the Developer's checks, `evidence.md` and `## Review` exist, and the code-check owner ([SIZE-22]) confirms both. There is no QA PASS to wait for.

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

Remove a role only at an iteration boundary with the PO's OK. Its duties move along the chain, its open threads go to the new owner, and the `## Handover` names that owner. Retire the removed role's session. Tasks already passed stay passed; unfinished tasks use the new Done.
