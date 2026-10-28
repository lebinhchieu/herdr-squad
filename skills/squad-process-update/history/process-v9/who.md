# Who decides

## WHO-1a Plan owner, Manager
roles: manager
when: plan-owner = manager
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Plan, task order, Developer spawning | Manager | Manager | Deadline or budget overrun |

## WHO-1b Task done
roles: manager, ba, team-lead, tech-lead
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Task done | Every checker on the team (`duties:`); with none, the Manager confirms the Developer's evidence and review | Manager | n/a |

## WHO-1c Business owner, BA
roles: manager, ba, tech-lead
when: business-ac = ba
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business scope, business AC, business doubt | BA | Manager | Goal change, scope cut |

## WHO-1d Business owner, ticket
roles: manager
when: business-ac = ticket
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Business AC | The ticket as written | Manager | Goal change, scope cut |
| Business doubt | Manager adds the BA ([SIZE-13]) | Manager | n/a |

## WHO-1e Plan owner, Team Lead
roles: manager, team-lead, tech-lead
when: plan-owner = team-lead
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Plan, task order, assignment | Team Lead | Team Lead | Deadline or budget overrun |

## WHO-2 Technical owners, Tech Lead
roles: manager, tech-lead
when: tech-lead = yes
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Technical design, quality, security | Tech Lead | Manager | Irreversible tech choice (data model, new dependency, vendor) |
| Migration, backward compatibility, deploy plan (order, rollback) | Tech Lead | Manager | Destructive data migration, breaking change for other teams |

## WHO-2d Technical owners without a Tech Lead
roles: manager
when: tech-lead = no
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Design notes, technical AC | Developer in the task file; agreed with QA whitebox when it is on the team | Manager | Irreversible tech choice (data model, new dependency, vendor) |
| Irreversible design choice | Manager, after an advisor call | Manager | The PO-listed items stay with the PO |

## WHO-2e Architecture owner
roles: manager, tech-lead, architect
when: architecture = yes
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Architecture (components, boundaries, contracts, constraints) | Architect | Manager | Irreversible tech choice (data model, new dependency, vendor) |
| Irreversible design choice | Architect lists and recommends; the Manager escalates it | Manager | The PO decides |

This replaces the "Irreversible" rows and cells of [WHO-2] and [WHO-2d]. The Developer's design notes, or the Tech Lead's design of each task, stay inside it.

## WHO-2b Promotion owner, QA whitebox
roles: manager
when: promote-owner = qa-white
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| What is promoted to the project docs | QA whitebox | Manager | n/a |

## WHO-2f Promotion owner, Developer
roles: manager
when: promote-owner = dev
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| What is promoted to the project docs | Developer | Manager | n/a |

## WHO-2c Promotion owner, Tech Lead
roles: tech-lead, ba, manager
when: promote-owner = tech-lead
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| What is promoted to the project docs | Tech Lead (technical), and the BA when on the team (business) | Manager | n/a |

## WHO-3a Process owner, Manager
roles: manager
when: plan-owner = manager
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Process, roster, spawning, the team | Manager | n/a | Changes to role instructions; team confirmation and removing a role |

## WHO-3b Process owner, Manager with a Team Lead
roles: manager, team-lead
when: plan-owner = team-lead
topic: owners

| Topic | Owner | Breaks a dispute | Always goes to PO |
|---|---|---|---|
| Process, roster, spawning, the team | Manager; Team Lead for Developers | n/a | Changes to role instructions; team confirmation and removing a role |

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

## WHO-8a Disputes, Manager plans
roles: manager
when: plan-owner = manager
topic: owners

The Manager settles every dispute.

## WHO-8b Disputes, Manager with a Team Lead
roles: manager
when: plan-owner = team-lead
topic: owners

The Manager settles every dispute except plan, order and assignment ones, which the Team Lead settles.

## WHO-8c Disputes, Team Lead
roles: team-lead
when: plan-owner = team-lead
topic: owners

Settle plan, order and assignment disputes. Write the ruling where the plan lives, and send it as `FINAL:` ([MSG-7b]). When you are yourself a party to such a dispute, do not settle it; after the two-round rule it goes to the Manager.
