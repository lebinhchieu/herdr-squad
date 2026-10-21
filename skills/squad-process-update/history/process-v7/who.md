# Who decides

## WHO-1a Owners in S
roles: manager, tech-lead
when: size = S
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business AC | The ticket as written | Manager | Goal change, scope cut |
| Plan, task order, assignment | Tech Lead | Manager | Deadline or budget overrun |
| Task done | Tech Lead review | Manager | n/a |

## WHO-1b Owners in M and L
roles: manager, ba, team-lead, tech-lead
when: size in M, L
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business scope, business AC | BA | Manager | Goal change, scope cut |
| Plan, task order, assignment | Team Lead | Team Lead | Deadline or budget overrun |
| Task done | QA whitebox + QA blackbox | Manager | n/a |

## WHO-2 Technical owners
roles: manager, tech-lead
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Technical design, quality, security | Tech Lead | Manager | Irreversible tech choice (data model, new dependency, vendor) |
| Migration, backward compatibility, deploy plan (order, rollback) | Tech Lead | Manager | Destructive data migration, breaking change for other teams |

## WHO-2b Promotion owners in S
roles: tech-lead, manager
when: size = S
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| What is promoted to the project docs | Tech Lead | Manager | n/a |

## WHO-2c Promotion owners in M and L
roles: tech-lead, ba, manager
when: size in M, L
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| What is promoted to the project docs | Tech Lead (technical), BA (business) | Manager | n/a |

## WHO-3a Process owner in S
roles: manager
when: size = S
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Process, roster, spawning, scope size | Manager | n/a | Changes to role instructions; size confirmation and moving down |

## WHO-3b Process owner in M and L
roles: manager, team-lead
when: size in M, L
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Process, roster, spawning, scope size | Manager; Team Lead for Developers | n/a | Changes to role instructions; size confirmation and moving down |

## WHO-4 UI design owner
roles: designer, manager, tech-lead
when: design = yes
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| UI design (screens, states, flows) | Designer | Manager | n/a |

## WHO-5 Merge and deploy owners
roles: manager
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Merge a passed branch ([MRG-1]) | PO asks; the Manager runs it | n/a | Always, per merge |
| Push, deploy (any env), running migrations on shared data | PO only | n/a | Always |

## WHO-6 Editing the rules
roles: manager
topic: owners

A Manager edits the squad's rules (`process.local.md`) only after re-reading them, in small edits, each logged in `process-log.md` (date, change, why). Role instructions (the plugin's agent files) the Manager does not edit: it drafts the change in the iteration file and gets PO approval at check-in.

## WHO-7 Outside decision makers
roles: manager, ba, team-lead, tech-lead
topic: owners

Questions for an outside decision maker `project.md` names go to the place it says (for example an open-points file), never to that person.

## WHO-8 Disputes
roles: manager
topic: owners

The parties come straight to the Manager after 2 exchanges; no one relays. Decide, write the decision to the place `project.md` names, then send `DECISION` ([MSG-7a], [MSG-7b]).

## WHO-8a Disputes, Manager in S
roles: manager
when: size = S
topic: owners

The Manager settles every dispute.

## WHO-8b Disputes, Manager in M and L
roles: manager
when: size in M, L
topic: owners

The Manager settles every dispute except plan, order and assignment ones, which the Team Lead settles.

## WHO-8c Disputes, Team Lead
roles: team-lead
when: size in M, L
topic: owners

Settle plan, order and assignment disputes. Write the ruling where the plan lives, and send it as `FINAL:` ([MSG-7b]). When you are yourself a party to such a dispute, do not settle it; after the two-round rule it goes to the Manager.
