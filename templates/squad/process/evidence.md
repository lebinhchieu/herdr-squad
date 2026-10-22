# Evidence

## EVID-1 Where evidence lives
roles: manager
aware: tech-lead, qa-whitebox, qa-blackbox
topic: evidence

Evidence lives next to the ticket in `evidence.md`: folder = ticket path minus `.md`, so `issues/05-x.md` → `issues/05-x/evidence.md` (a project without ticket files: `tasks/<id>/evidence.md`); an old `<stem>.evidence/` folder is still read. Embed screenshots as `![alt](img/<file>)`; a screenshot only named or linked is not evidence.

## EVID-2a Behaviour
roles: dev
when: size in M, L
topic: evidence

You write `## Behaviour` in the ticket's `evidence.md`, commit it with your code, and embed screenshots as `![alt](img/<file>)`.

## EVID-2b Assemble evidence
roles: dev
when: size = L
topic: evidence

After every checker passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Tech Lead.

## EVID-2d Assemble evidence, M
roles: dev
when: size = M
topic: evidence

Once every checker has passed: `squad-evidence add <ticket> --heading "<H>" --from <review file>` per review file in `$SCOPE_DIR/evidence/<task>/`, `squad-evidence check <folder>`, commit, `HANDIN <task>: evidence sha <sha>` to the Manager.

## EVID-2c Check the evidence commit
roles: tech-lead
when: size = L
topic: evidence

On the Developer's `HANDIN <task>: evidence sha <sha>`, run `squad-evidence check <folder> --base <passed sha>` and accept it only when it exits 0.

## EVID-2e Check the evidence commit, M
roles: manager
when: size = M
topic: evidence

The Developer's `HANDIN <task>: evidence sha <sha>` is accepted only when `squad-evidence check <folder> --base <passed sha>` exits 0.

## EVID-3a Review record in S
roles: manager
when: size = S
topic: evidence

S has no reviewer file: `## Review` in the ticket's `evidence.md` ([REV-22]) is the review record, and your `PASS` is the verdict.

## EVID-3b Reviewer files in M and L
roles: qa-blackbox, qa-whitebox
aware: team-lead
when: size in M, L and qa-b = yes
topic: evidence

`qa-w.md` and `qa-b.md` are the reviewer files in M and L.

## EVID-4 Behaviour, S
roles: dev
when: size = S
topic: evidence

Commit `## Behaviour` with the code: Playwright or API checks per AC (run, seen), shots `![alt](img/<file>)` under their AC.

## EVID-5 Design shots, S
roles: dev
when: size = S and design = yes
topic: evidence

Save one screenshot per screen and state in `img/`, under its design item.

## EVID-6 Behaviour per AC, no QA blackbox
roles: dev
when: size in M, L and qa-b = no
topic: evidence

In `## Behaviour` record for each business AC what you ran (command) and what you saw (output); screenshots only if a screen exists. QA whitebox checks it.

## EVID-7 Reviewer file, no QA blackbox
roles: qa-whitebox
aware: team-lead
when: size in M, L and qa-b = no
topic: evidence

`qa-w.md` is the only reviewer file; no `qa-b.md` is expected.
