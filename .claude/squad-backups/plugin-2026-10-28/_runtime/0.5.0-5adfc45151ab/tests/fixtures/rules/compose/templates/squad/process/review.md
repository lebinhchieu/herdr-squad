# Review

## REV-3 One verdict per final sha
roles: qa-whitebox, qa-blackbox
aware: dev, team-lead
when: size in M, L
topic: review

The Tech Lead names one final sha per task before QA verdicts; each QA gives one verdict on that sha.

## REV-7a Tech Lead reviews alone
roles: tech-lead
aware: dev
when: size = S
topic: review

The Tech Lead reads the diff and the evidence and sends the verdict, because the scope has no QA.

## REV-7b Both QAs review
roles: qa-whitebox, qa-blackbox
when: size in M, L
topic: review

Each QA checks the handed-in sha and sends one verdict to the Developer.

## REV-8 Screenshot per design state
roles: dev
when: design = yes
topic: review

The Developer saves one screenshot per design state in the evidence folder.
