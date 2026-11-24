# 04 Plan panel on the board

Status: ready-for-agent

Spec: `.scratch/po-clarity/spec.md` · Blocked by: 01

## Problem

Chieu can't see **how** the work will be done: in which order, what blocks what, how long each part should take, and what each part is for. The facts are partly written already (`tasks/NN.md` has `Lane:` and `Depends on:`), but nothing shows them together. Aims and estimates are not written anywhere.

## Change

There is a new board panel, `plan` (own file `templates/board/panel_plan.js`, `BOARD.registerPanel`). It is a panel, not a tab, and works for both kinds of home:

| Home | Rows are | Read from |
|---|---|---|
| Goal | its scopes | `goal.md` scope table |
| Scope | its tasks | `tasks/NN.md` + ticket 01's reader |

It has no Needs-you list: the inbox panel already shows that.

**Wireframe, a scope** (`upstream-proposals` data, with aims and estimates added):

```text
┌ Plan · upstream-proposals ─────────────────────────────────────┐
│ Aim: adopt 37 overlay rules into the plugin                    │
│ ███████████████░  10 of 11 passed · est 9h · spent 11h [warn]  │
│                                                                │
│ STEP 1 · can start now                                         │
│  01 usage row at commit   cost row lands with commit  1h  [ok] │
│  03 evidence before retire  QA files kept           1h  [ok]   │
│  04 merge by relation     merge order from git      1h  [ok]   │
│ STEP 2 · after step 1                                          │
│  05 planning checks       ← 03   start checks run   1h  [ok]   │
│  02 base failures file    ← 04   known reds listed  1h  [ok]   │
│ STEP 3                                                         │
│  06 integration           ← 01-05  one branch       2h  [ok]   │
│  07 designer tmp test     ← 06   test stops leaking .5h [ok]   │
│ STEP 4                                                         │
│  10 po-inbox timing       ← 08   no flaky timing    1h  [warn] │
│     est 1h · spent 3h                                          │
│  11 session lookup        ← 08   ...                1h  ▶ now  │
└────────────────────────────────────────────────────────────────┘
```

- **Step** = depth in the `Depends on` graph. Everything in a step can run side by side.
- `← NN` = blocked by. Hovering a row also highlights the rows it blocks.
- **est** comes from the file. **Spent** comes from the board's existing work-time reader (approx, as today). When spent is over 1.5x est, the row shows `[warn]`.
- The state badge comes from task events (as in the tasks panel). `▶ now` marks building or checking.

**Wireframe, a goal** (guardian `clarify`): the same layout, one row per scope, with steps taken from the table's "Depends on" column. A row that waits on something outside the goal shows it in words (`waits: Matt A5, A6`).

**Fields the plan writers fill (new rule in `starting.md`, plan step; roles Manager and Team Lead):**

| Field | Where | Example | Who |
|---|---|---|---|
| `Aim:` | `tasks/NN.md`; goal.md column "Aim" | `Aim: QA files kept after the Dev retires` | Manager at plan |
| `Estimate:` | `tasks/NN.md`; goal.md column "Est" | `Estimate: 1h` (Dev build + checks) | Tech Lead, else Manager |
| `Depends on:` | already in `tasks/NN.md` and goal.md | `Depends on: 03, 04` | as today |

`Aim:` is one line, at most 60 characters, in plain words, with no bare IDs (same check as ticket 03). A missing field shows `–` and does not break the panel.

## AC

- AC1: on a fixture scope with 01 (no deps), 02 (← 01) and 03 (← 01, 02), the panel shows 3 steps in that order, each with its `← NN`.
- AC2: on the fixture goal, the scope rows show steps from "Depends on", and outside waits show in words.
- AC3: a task with spent over 1.5x its estimate shows `[warn]` and both numbers.
- AC4: a missing `Aim:` or `Estimate:` shows `–`. A dependency loop shows the looped rows in one step marked `[fail] loop`, never a crash.
- AC5: the new plan rule passes `squad-process lint` and attaches to the Manager and the Team Lead. The ticket template from 06 has the three lines.
- AC6: one new read route, `GET /api/plan`, under the existing Host and token checks; no write route.
- AC7: `squad-board --demo` shows the panel for a scope and for a goal. Both screenshots go in the evidence.

## Comments
