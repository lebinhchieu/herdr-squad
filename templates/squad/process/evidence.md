# Evidence

## EVID-1 Where evidence lives
roles: tech-lead, qa-whitebox, qa-blackbox
topic: evidence

Evidence lives next to the ticket in `evidence.md`: folder = ticket path with `.md` → `.evidence/` (a project without ticket files: next to `tasks/<id>.md`). Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-2a Behaviour
roles: dev
when: size in M, L
topic: evidence

You write `## Behaviour` in the ticket's `evidence.md`, commit it with your code, and embed screenshots as `![alt](img/<file>)`.

## EVID-2b Assemble evidence
roles: dev
topic: evidence

After every checker passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Tech Lead.

## EVID-2c Check the evidence commit
roles: tech-lead
topic: evidence

On the Developer's `HANDIN <task>: evidence sha <sha>`, run `squad-evidence check <folder> --base <passed sha>` and accept it only when it exits 0.

## EVID-3a Reviewer file in S
roles: tech-lead
when: size = S
topic: evidence

`tl-review.md` is the reviewer file in S.

## EVID-3b Reviewer files in M and L
roles: qa-blackbox, qa-whitebox, team-lead
when: size in M, L and qa-b = yes
topic: evidence

`qa-w.md` and `qa-b.md` are the reviewer files in M and L.

## EVID-4 Behaviour, S
roles: dev
when: size = S
topic: evidence

Write `## Behaviour` in the ticket's `evidence.md` and commit it with the code: Playwright or API checks per AC, what you ran and saw, screenshots embedded as `![alt](img/<file>)` under their AC (with a design: one per screen and state, under its design item).

## EVID-5 Design shots, S
roles: tech-lead
when: size = S and design = yes
topic: evidence

Save one screenshot per screen and state in the ticket's evidence `img/` and embed each as `![alt](img/<file>)` right under the design item it answers in `evidence.md`.

## EVID-6 Behaviour per AC, no QA blackbox
roles: dev
when: size in M, L and qa-b = no
topic: evidence

In `## Behaviour` record for each business AC what you ran (command) and what you saw (output); screenshots only if a screen exists. QA whitebox checks it.

## EVID-7 Reviewer file, no QA blackbox
roles: qa-whitebox, team-lead
when: size in M, L and qa-b = no
topic: evidence

`qa-w.md` is the only reviewer file; no `qa-b.md` is expected.
