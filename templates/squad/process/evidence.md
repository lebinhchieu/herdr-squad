# Evidence

## EVID-1 Where evidence lives
roles: manager
aware: tech-lead, qa-whitebox, qa-blackbox
topic: evidence

Evidence lives next to the ticket in `evidence.md`: folder = ticket path minus `.md`, so `issues/05-x.md` → `issues/05-x/evidence.md` (a project without ticket files: `tasks/<id>/evidence.md`); an old `<stem>.evidence/` folder is still read. Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-2a Behaviour
roles: dev
when: handin-target = qas
topic: evidence

You write `## Behaviour` in the ticket's `evidence.md`, commit it with your code, and embed screenshots as `![alt](img/<file>)`.

## EVID-2b Assemble evidence
roles: dev
when: tech-ac = tech-lead
topic: evidence

After every checker passed: `squad-evidence add <ticket> --heading "<H>" --from <file>` per file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Tech Lead.

## EVID-2d Assemble evidence, Manager
roles: dev
when: tech-ac = qa-white
topic: evidence

Once every checker has passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Manager.

## EVID-2c Check the evidence commit, Tech Lead
roles: tech-lead
when: tech-lead = yes
topic: evidence

On the Developer's `HANDIN <task>: evidence sha <sha>`, run `squad-evidence check <folder> --base <passed sha>` and accept it only when it exits 0.

## EVID-2e Check the evidence commit, Manager
roles: manager
when: tech-ac = qa-white
topic: evidence

The Developer's `HANDIN <task>: evidence sha <sha>` is accepted only when `squad-evidence check <folder> --base <passed sha>` exits 0.

## EVID-3a Review record without a QA
roles: manager
when: handin-target = manager
topic: evidence

With no QA on the team there is no reviewer file: `## Review` in the ticket's `evidence.md` ([REV-22]) is the review record, and your `PASS` is the verdict.

## EVID-3b Reviewer files, both QAs
roles: qa-blackbox, qa-whitebox
aware: team-lead
when: qa-white = yes and qa-black = yes
topic: evidence

`qa-w.md` and `qa-b.md` are the reviewer files.

## EVID-4 Behaviour
roles: dev
when: behaviour-check = manager
topic: evidence

Commit `## Behaviour` with the code: Playwright or API checks per AC (run, seen), shots `![alt](img/<file>)` under their AC.

## EVID-5 Design shots
roles: manager
when: ui-check = manager and design = yes
topic: evidence

Save one screenshot per screen and state in `img/`, under its design item.

## EVID-6 Behaviour per AC, QA whitebox checks
roles: dev
when: behaviour-check = qa-white
topic: evidence

In `## Behaviour` record for each business AC what you ran (command) and what you saw (output); screenshots only if a screen exists. QA whitebox checks it.

## EVID-7 Reviewer file, QA whitebox alone
roles: qa-whitebox
aware: team-lead
when: qa-white = yes and qa-black = no
topic: evidence

`qa-w.md` is the only reviewer file; no `qa-b.md` is expected.

## EVID-8 Reviewer file, QA blackbox alone
roles: qa-blackbox
aware: team-lead
when: qa-black = yes and qa-white = no
topic: evidence

`qa-b.md` is the only reviewer file; no `qa-w.md` is expected.
