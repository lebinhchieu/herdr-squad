# Your process rules
agent: mgr · role: manager · scope: goal g1 (size n/a, design no, qa full, goal yes)
plugin: 9.9.9 abc1234 · overlay: 2 operations applied · composed: 2026-10-22T10:00:00Z
rules: CORE-1 MSG-1 MSG-2a MSG-2b

## CORE-1 Task states
A task is ready, in progress, in review, passed or blocked; only the task owner changes its state.

## MSG-1 Manager owns the PO channel
The Manager alone talks to the PO and relays every question that needs a PO answer.

## MSG-2a Manager reports to the Team Lead [if size = S]
The Manager sends the Tech Lead every answer to a status question.

## MSG-2b Manager reports through the Team Lead [if size in M, L]
The Manager sends the Team Lead every answer to a status question.

## Index of other rules
- MSG-3 Manager relays design questions (manager)
- REV-3 One verdict per final sha (qa-whitebox, qa-blackbox)
- REV-7a Tech Lead reviews alone (tech-lead)
- REV-7b Both QAs review (qa-whitebox, qa-blackbox)
- REV-8 Screenshot per design state (dev)
- SQ-1 Style contract (tech-lead)
