# Evidence

## EVID-1 Where evidence lives
roles: dev, tech-lead, qa-whitebox, qa-blackbox
topic: evidence

Evidence lives next to the ticket in `evidence.md`: folder = ticket path with `.md` → `.evidence/` (a project without ticket files: next to `tasks/<id>.md`). Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-2a Behaviour section
roles: dev
topic: evidence

The Developer writes `## Behaviour` and commits it with its code.

## EVID-2b Assemble the evidence
roles: dev
topic: evidence

Once every checker passed, run `squad-evidence add <ticket> --heading "<H>" --from <review file>` for each review file in `$SCOPE_DIR/evidence/<task>/`, then `squad-evidence check <folder>`, commit, and send `HANDIN <task>: evidence sha <sha>` to the Tech Lead.

## EVID-2c Check the evidence commit
roles: tech-lead
topic: evidence

On the Developer's `HANDIN <task>: evidence sha <sha>`, run `squad-evidence check <folder> --base <passed sha>` and accept it only when it exits 0.

## EVID-3a Reviewer file in S
roles: dev, tech-lead
when: size = S
topic: evidence

`tl-review.md` is the reviewer file in S.

## EVID-3b Reviewer files in M and L
roles: dev, qa-blackbox, qa-whitebox, team-lead
when: size in M, L
topic: evidence

`qa-w.md` and `qa-b.md` are the reviewer files in M and L.

## EVID-4 Behaviour evidence, S
roles: dev
when: size = S
topic: evidence

Write `## Behaviour` of the ticket's `evidence.md` yourself: Playwright or API checks for each AC, with what you ran and what you saw. Save each screenshot in that folder's `img/`, embed it as `![alt](img/<file>)` right under the AC it answers, and commit it with the code.

## EVID-5 Design screenshots, S
roles: dev
when: size = S and design = yes
topic: evidence

Save one screenshot per screen and state in the ticket's evidence `img/` and embed each as `![alt](img/<file>)` right under the design item it answers in `evidence.md`.
