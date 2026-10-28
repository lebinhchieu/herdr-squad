# Review

## REV-3 One verdict per final sha
roles: qa-whitebox, qa-blackbox
aware: dev, team-lead
when: size in M, L
topic: review

The Tech Lead names one final sha per task before QA verdicts; each QA gives one verdict on that sha.

## REV-4 Blackbox check by the Developer
roles: dev
when: qa-b = no and size = S
topic: review

- The Developer saves a Playwright or API check for each AC in the evidence file.
- The Tech Lead reads that check before the PASS.
