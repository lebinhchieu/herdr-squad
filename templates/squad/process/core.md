# Core

## CORE-1 Task states
roles: all
topic: lifecycle

`ready → building → (blocked ↔ building) → handed in → checking → done | returned → building`.

## CORE-2 Message types
roles: all
topic: messages

Send with `SendMessage` to the agent name in `roster.md`, as `<TYPE> <TASK-ID>: <text>`. Types: `ASK`, `ANSWER`, `DECISION`, `BLOCKED`, `HANDIN`, `PASS`, `FAIL`, `STATUS`.

## CORE-3 Who owns what
roles: all
topic: owners

Tech Lead: design, quality, security. Manager: process, roster, scope size. Designer: UI. Business AC, plan, done by size: [WHO-1a], [WHO-1b].

## CORE-4 Two-round rule
roles: all
topic: messages

No agreement after 2 exchanges: send the topic to its owner, or to the Manager when the owner is one of you.

## CORE-5 Files are the truth
roles: all
topic: files

Write a durable thing to a file first, then message a pointer to it.

## CORE-6 Rules not attached
roles: all
topic: rules

A rule cited as `[ID]` that is not in this file: run `squad-process rule <ID>`. `squad-process who <ID>` shows which roles it binds.
