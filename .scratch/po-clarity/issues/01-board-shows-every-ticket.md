# 01 Board shows every ticket of a scope

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md`

## Problem

Today the board takes tickets from **only the first source that has files** (`squadtickets.SOURCES`, `bin/squadtickets.py:15`). On `upstream-proposals` that source is `main`'s `.scratch/upstream-proposals/issues/`, which holds 01-06. Tickets 07-11 were drafted later. They live in two other places the board never reads:

```diagram Where ticket 10 lives today
Tech Lead drafts tasks/10-ticket.md
▼
Dev commits .scratch/.../10-po-inbox-timing.md
on branch ...-10 (not on main)
▼
Board reads main's .scratch only  [fail]
▼
Chieu sees 01-06; 07-11 are missing
```

Example, on 2026-11-24:

| Ticket | On main | On a Dev branch | Draft in `tasks/` |
|---|---|---|---|
| 06 | yes | yes | no |
| 07 | no | `-06`, `-08`, `-10` | `07-ticket.md` |
| 10 | no | `-10` | `10-ticket.md` |
| 11 | no | `-10`, `-11` | `11-ticket.md` |

## Change

`squadtickets.scope_tasks` merges all sources by ticket number instead of stopping at the first one. When a ticket has several copies, the newest wins:

1. the copy on the ticket's own Developer branch (`...-NN`), read with `git show <branch>:<path>`
2. else the copy on the newest scope branch that has it
3. else the draft `tasks/NN-ticket.md`
4. else `main`'s `.scratch`

Each row keeps a `source` field. The tasks panel shows the source as a small grey tag (`main`, `branch -10`, `draft`), so Chieu can see that a ticket is not on main yet:

```text
┌ Tasks ─────────────────────────────────────┐
│ 06 rm-ui-ac-notes         passed    main   │
│ 07 designer-tmp-test      passed    branch │
│ 10 po-inbox-timing        checking  branch │
│ 11 session-lookup         building  draft  │
└────────────────────────────────────────────┘
```

## AC

- AC1: on a fixture scope with tickets on main (01-02), on a Dev branch only (03) and as a draft only (04), the tasks panel lists 01-04 once each.
- AC2: a ticket on both main and its own branch shows the branch copy's title and `Status:`.
- AC3: `squad-report` and the picker use the same function and list the same tickets (one test).
- AC4: the board still makes no writes to git. A branch is read with `git show` and `git ls-tree` only, with the 5 s timeout `squadboard_git.py` already uses.
- AC5: the ADR 0020 amendment line "first source with a task wins" is changed to "all sources merge by number, newest copy wins".

## Comments
