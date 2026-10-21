# Core

## CORE-1 Task states
roles: all
topic: lifecycle

`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`.

## CORE-2 Message types
roles: all
topic: messages

Send with `SendMessage` as `<TYPE> <TASK-ID>: <text>`. Types: `ASK`, `ANSWER`, `DECISION`, `BLOCKED`, `HANDIN`, `PASS`, `FAIL`, `STATUS`. Rules: [MSG-1].

## CORE-3 Who owns what
roles: all
topic: owners

Technical design, quality, security: Tech Lead. Process, roster, spawning, scope size: Manager. UI design: Designer. Business AC, plan and done depend on the size: [WHO-1a], [WHO-1b].

## CORE-4 Two-round rule
roles: all
topic: messages

Agents who have not agreed after 2 exchanges send the topic to its owner, or to the Manager when the owner is one of them.

## CORE-5 Files are the truth
roles: all
topic: files

Write a durable thing to a file first, then send a message pointing at it.
