# Review and checks

## REV-1 Tech Lead review, S
roles: tech-lead
when: size = S
topic: review

On `HANDIN`: read the diff, run the tests and lint yourself, and check the Developer's `evidence.md` (the design screenshots too): `squad-evidence check` must pass, so a screenshot that is not embedded fails. Write `tl-review.md` in `$SCOPE_DIR/evidence/<task>/` and send `PASS` or `FAIL`. Be as skeptical as a QA: unverified = FAIL.

## REV-2 QA whitebox review
roles: qa-whitebox
when: size in M, L
topic: review

On `HANDIN`, check out the Developer's branch (read-only), then:
1. Review the diff against the technical AC and the repo's conventions.
2. Run the tests and linters `project.md` lists, on the changed files.
3. Check that each new behaviour has a test and each new endpoint is covered.
4. When the task changes a schema, data, API or contract: run the migration and its rollback locally, check that existing callers still work, and check that the Tech Lead's deploy notes match the code.

## REV-3 One verdict per final sha
roles: tech-lead, qa-whitebox, qa-blackbox
aware: team-lead
when: size in M, L
topic: review

The Tech Lead names one final sha per task before QA verdicts; doc-only edits wait until every finding is in, and each QA gives one verdict on that sha.

## REV-4 Real samples
roles: qa-whitebox, tech-lead
topic: review

Code that parses another tool's output (pane text, logs, an API) needs two real samples, including the constant or idle case, before a pattern is trusted. The Tech Lead's technical AC require them.

## REV-5a Live run, S
roles: tech-lead
when: size = S
topic: review

Run code that parses another tool's output once, read-only, on live data.

## REV-5b Live run, M and L
roles: qa-whitebox
when: size in M, L
topic: review

QA whitebox runs code that parses another tool's output once, read-only, on live data.

## REV-6 Payload shape
roles: qa-whitebox, tech-lead
topic: review

A ticket that changes a payload is checked on its field shape (every row has the fields the consumer reads, every closed item has its end), not only on totals.

## REV-7 Technical AC
roles: tech-lead, qa-whitebox
when: size in M, L
topic: review

Agree the technical AC before work starts: tests that must exist, lint clean, patterns followed, security checks, performance limits.

## REV-8 Business AC with QA blackbox
roles: ba, qa-blackbox
when: size in M, L and qa-b = yes
topic: review

Agree the business AC before work starts, as Given/When/Then a user can observe in the running app. The BA writes them where `project.md` says AC live and records the agreement.

## REV-9 QA blackbox check
roles: qa-blackbox
when: size in M, L and qa-b = yes
topic: review

On `HANDIN`, test the running app the way `project.md` says (for example Playwright against the dev server, with the Developer's branch deployed or served locally). Walk every business AC, plus the obvious unhappy paths a real user would hit.

## REV-10 QA whitebox findings
roles: qa-whitebox
when: size in M, L
topic: review

Write findings to `$SCOPE_DIR/evidence/<task>/qa-w.md`: each finding with file:line, why it matters, and what would pass. Embed a screenshot as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it. Read the ticket's `evidence.md` `## Behaviour` as the Developer's claim, not as proof.

## REV-11 QA blackbox evidence
roles: qa-blackbox
when: size in M, L and qa-b = yes
topic: review

Write evidence to `$SCOPE_DIR/evidence/<task>/qa-b.md`: each AC → what you did → what you saw → pass/fail, with each screenshot embedded as `![alt](path)` (absolute, or relative to the file); the Developer's `squad-evidence add` copies it.

## REV-12 Verdict
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: review

Send `PASS` or `FAIL` to the Developer only.

## REV-13a Hand in, S
roles: dev
when: size = S
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to the Tech Lead.

## REV-13b Hand in, M and L
roles: dev
when: size in M, L and qa-b = yes
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox and QA blackbox.

## REV-14a Diff check after PASS, S
roles: dev
when: size = S
topic: review

After a PASS, a later commit goes to the Tech Lead as `HANDIN <task>: diff check <passed sha>..<new sha>`.

## REV-14b Diff check after PASS, M and L
roles: dev
when: size in M, L and qa-b = yes
topic: review

After a PASS, a later commit goes to both QAs as `HANDIN <task>: diff check <passed sha>..<new sha>`; tell the Team Lead after both pass it.

## REV-15 Report deliverables
roles: tech-lead
topic: review

A report or doc deliverable is also copied into `$SCOPE_DIR/evidence/<task>/` at the sha handed in; the `HANDIN` names that path (QA blackbox cannot read worktrees).

## REV-16 Style contract
roles: tech-lead
topic: review

For a scope with a UI mock, the Tech Lead writes `style-contract.md`; the UI AC cite it.

## REV-17 Style findings
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: review

A QA lists all style findings of a sha in one return.

## REV-18a Presentational values, QA whitebox
roles: qa-whitebox
aware: qa-blackbox
when: size in M, L
topic: review

Never assert presentational values the mock fixes; QA blackbox owns them.

## REV-18b Presentational values, QA blackbox
roles: qa-blackbox
aware: qa-whitebox
when: size in M, L
topic: review

QA blackbox owns the presentational values the mock fixes; QA whitebox never asserts them.

## REV-19 Hand in and Done, no QA blackbox
roles: dev
when: size in M, L and qa-b = no
topic: review

`HANDIN <task>: branch squad/<squad>/$SQUAD_SCOPE/$SQUAD_NAME, commit <sha>, how to run it` to QA whitebox only, copy the Team Lead. After a PASS, a later commit goes to QA whitebox as `HANDIN <task>: diff check <passed sha>..<new sha>`. Done when QA whitebox sent `PASS`: tell the Team Lead and wait; it retires you.

## REV-20 Behaviour check, no QA blackbox
roles: qa-whitebox
when: size in M, L and qa-b = no
topic: review

There is no QA blackbox: on `HANDIN` also check each business AC against the Developer's `## Behaviour` (command, output, screenshot if a screen exists), re-running a command when its claim is not clear. Record each AC → seen → pass/fail in `qa-w.md`. Your `PASS` is Done.

## REV-21 Business AC, no QA blackbox
roles: ba
when: size in M, L and qa-b = no
topic: review

Write the business AC alone, as Given/When/Then a person can observe (a command and its output, a file, a message), where `project.md` says AC live, and tell QA whitebox, who checks them.
