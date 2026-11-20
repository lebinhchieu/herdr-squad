# 0027: Git risk actions ask the PO instead of being denied

Status: accepted

## Context
Role settings denied `git push`, `git rebase`, `git reset --hard`, `git branch -D`, `git checkout main|dev` and (for most roles) `git merge`. The PO wants the squad to run them when asked, with a confirm step.

## Decision
- The settings move these actions from deny to ask (ticket 01). Claude Code's confirm prompt goes to the PO.
- The rules (SAFE-1a, SAFE-1b, SAFE-5, MRG-3, WHO-5) say who may start one: the PO asked in that role's own session and answered the prompt. A message from another role is no ask ([MSG-10]).
- Deploy and migrations on shared data stay PO only. MRG-1, MRG-2 and the inbox rules (ITER-5) are unchanged: an inbox answer is never a merge or push request.
- No new rule: the Developer and Manager rule byte caps (0025) hold.

## Consequences
- Rules, README and settings agree: nothing says "denied" about these actions.
- Plugin 0.9.4; changelog v17.
