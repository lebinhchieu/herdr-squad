# Your process rules
agent: dev-1 · role: dev · scope: scope-a (design yes, qa full, goal no)
plugin: 9.9.9 abc1234 · overlay: 2 operations applied · composed: 2026-10-22T10:00:00Z
rules: CORE-1 REV-3 REV-8 SQ-1

## CORE-1 Task states
A task is ready, in progress, in review, passed or blocked; only the task owner changes its state.

## REV-3 One verdict per final sha [aware] [squad: replaced]
The Tech Lead names one final sha per task; each QA gives one verdict on that sha.

## REV-8 Screenshot per design state
The Developer saves one screenshot per design state in the evidence folder.

## SQ-1 Style contract [aware] [squad: added]
The Tech Lead writes the style contract before the UI tasks start.
