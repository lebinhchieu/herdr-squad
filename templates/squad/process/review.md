# Review and checks

## REV-1 Confirmation, Manager
roles: manager
when: handin-target = manager
topic: review

On `HANDIN`: open the Developer's `evidence.md` (design shots too); confirm `## Behaviour` and `## Review` ([REV-22]) are there, with the suite receipt in `$SCOPE_DIR/evidence/` ([SUITE-2d]). `squad-evidence check` on its folder must pass, so an unembedded shot fails. Send `PASS` or `FAIL` to the Developer; a missing or unverified item is a `FAIL`. You do not redo the Developer's checks ([SIZE-7a]).

## REV-1b Confirmation, Team Lead
roles: team-lead
when: handin-target = team-lead
topic: review

On `HANDIN`: make the confirmation of [REV-1] (`## Behaviour` and `## Review` in `evidence.md`, suite receipt, `squad-evidence check` passing) and send `PASS` or `FAIL` to the Developer; you do not redo the Developer's checks.

## REV-2 QA whitebox review
roles: qa-whitebox
when: qa-white = yes
topic: review

On `HANDIN`, check out the Developer's branch (read-only), then:
1. Review the diff against the technical AC and the repo's conventions.
2. Run the tests and linters `project.md` lists, on the changed files.
3. Check that each new behaviour has a test and each new endpoint is covered.

## REV-2b Migration check
roles: qa-whitebox
when: risk-owner = tech-lead
topic: review

When the task changes a schema, data, API or contract: run the migration and its rollback locally, check that existing callers still work, and check that the Tech Lead's deploy notes match the code.

## REV-3 One verdict per final sha
roles: tech-lead, qa-whitebox, qa-blackbox
aware: team-lead
when: tech-lead = yes
topic: review

The Tech Lead names one final sha per task before QA verdicts; doc-only edits wait until every finding is in, and each QA gives one verdict on that sha.

## REV-3b Final sha
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: review

The final sha of a task is the one in the Developer's latest `HANDIN`, unless [REV-3] names another. Doc-only commits come after every finding is in, and each QA sends a single verdict on that sha.

## REV-4 Real samples
roles: qa-whitebox
aware: tech-lead
when: qa-white = yes
topic: review

Code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted. The technical AC require them.

## REV-5a Live run
roles:
when: qa-white = no
topic: review

Run code that parses another tool's output once, read-only, on live data.

## REV-5b Live run, QA whitebox
roles: qa-whitebox
when: qa-white = yes
topic: review

QA whitebox runs code that parses another tool's output once, read-only, on live data.

## REV-6 Payload shape
roles: qa-whitebox
aware: tech-lead
when: qa-white = yes
topic: review

A ticket that changes a payload is checked on its field shape (every row has the fields the consumer reads, every closed item has its end), not only on totals.

## REV-7 Technical AC
roles: tech-lead, qa-whitebox
when: tech-ac = tech-lead
topic: review

Agree the technical AC before work starts: tests that must exist, lint clean, patterns followed, security checks, performance limits.

## REV-8 Business AC with QA blackbox
roles: ba, qa-blackbox
when: business-ac = ba and qa-black = yes
topic: review

Agree the business AC before work starts, as Given/When/Then a user can observe in the running app. The BA writes them where `project.md` says AC live and records the agreement.

## REV-9 QA blackbox check
roles: qa-blackbox
when: qa-black = yes
topic: review

On `HANDIN`, test the running app the way `project.md` says (for example Playwright against the dev server, with the Developer's branch deployed or served locally). Walk every business AC, plus the obvious unhappy paths a real user would hit.

## REV-10 QA whitebox findings
roles: qa-whitebox
when: qa-white = yes
topic: review

Write findings to `$SCOPE_DIR/evidence/<task>/qa-w.md`: each finding with file:line, why it matters, and what would pass. Embed a screenshot as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it. Read the ticket's `evidence.md` `## Behaviour` as the Developer's claim, not as proof.

## REV-11 QA blackbox evidence
roles: qa-blackbox
when: qa-black = yes
topic: review

Write evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md`: each AC → what you did → what you saw → pass/fail, with each screenshot embedded as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it.

## REV-12 Verdict
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: review

Send `PASS` or `FAIL` to the Developer only.

## REV-13a Hand in, Manager
roles: dev
when: handin-target = manager
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to the Manager.

## REV-13c Hand in, Team Lead
roles: dev
when: handin-target = team-lead
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to the Team Lead.

## REV-13b Hand in, both QAs
roles: dev
when: qa-white = yes and qa-black = yes
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox and QA blackbox.

## REV-13d Hand in, QA blackbox alone
roles: dev
when: qa-white = no and qa-black = yes
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA blackbox only.

## REV-14a Diff check
roles: dev
topic: review

After a PASS, a later commit goes to the same checkers as `HANDIN <task>: diff check <passed sha>..<new sha>`; tell the plan owner after every checker passes it.

## REV-15 Report deliverables
roles: manager
aware: tech-lead, team-lead
topic: review

Name this in the task file of a report or doc task: a report or doc deliverable is also copied into `$SCOPE_DIR/evidence/<task>/` at the sha handed in; the `HANDIN` names that path (QA blackbox cannot read worktrees).

## REV-16 Style contract
roles: tech-lead
when: tech-lead = yes
topic: review

For a scope with a UI mock, the Tech Lead writes `style-contract.md`; the UI AC cite it.

## REV-17 Style findings
roles: qa-whitebox, qa-blackbox
when: handin-target = qas
topic: review

A QA lists all style findings of a sha in one return.

## REV-18a Presentational values, QA whitebox
roles: qa-whitebox
aware: qa-blackbox
when: qa-white = yes and qa-black = yes
topic: review

Never assert presentational values the mock fixes; QA blackbox owns them.

## REV-18b Presentational values, QA blackbox
roles: qa-blackbox
aware: qa-whitebox
when: qa-white = yes and qa-black = yes
topic: review

QA blackbox owns the presentational values the mock fixes; QA whitebox never asserts them.

## REV-19b Hand in, QA whitebox alone
roles: dev
when: qa-white = yes and qa-black = no
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox only.

## REV-20 Behaviour check, QA whitebox
roles: qa-whitebox
when: behaviour-check = qa-white
topic: review

There is no QA blackbox: on `HANDIN` also check each business AC against the Developer's `## Behaviour` (command, output, screenshot if a screen exists), re-running a command when its claim is not clear. Record each AC → seen → pass/fail in `qa-w.md`. Your `PASS` is Done.

## REV-21 Business AC, BA alone
roles: ba
when: business-ac = ba and qa-black = no
topic: review

Write the business AC alone, as Given/When/Then a person can observe (a command and its output, a file, a message), where `project.md` says AC live, and tell the owner of the behaviour check, who checks them.

## REV-21b Business AC, the ticket
roles: qa-whitebox
when: business-ac = ticket and qa-black = no
topic: review

There is no BA: the business AC are the ticket as written ([SIZE-5a]). One a person cannot observe (a command and its output, a file, a message) is a finding in `qa-w.md`; a business doubt goes to the Manager ([SIZE-13]).

## REV-22 Review
roles: dev
when: qa-white = no
topic: review

Before `HANDIN` start a fresh-context review subagent (`model: sonnet`, `effort: high`, no fork) on your diff; findings and fixes: `## Review`; `squad-evidence check <folder>` must pass. Parsing another tool's output: [REV-5a].

## REV-22a Architecture review
roles: dev
when: qa-white = no and architecture = yes
topic: review

Give the review subagent `$SCOPE_DIR/architecture.md` to check the diff conforms.
