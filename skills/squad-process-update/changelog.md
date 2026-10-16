## v4 — 2026-10-17
- snapshot: history/process-v4.md

### Files table: Team Lead rows
- sections: ## Files are the truth, messages are the talk
- change: rule
- why: the Team Lead keeps its Developers' roster rows, owns the plan file in M and L, and writes the iteration summary the Manager reads
- old: snapshot
- new: snapshot

### Developer cap shared out by the Team Lead
- sections: ## Defaults
- change: rule
- why: the Team Lead spawns Developers up to the cap; a goal Manager divides the cap among running scopes
- old: snapshot
- new: snapshot

### Team Lead spawns the Developers in M and L
- sections: ## Starting work
- change: rule
- why: in M and L the Team Lead spawns and retires the Developers; the Manager's confirm gate for its own spawns stays
- old: snapshot
- new: snapshot

### M gains the Team Lead
- sections: ## Sizes: not every scope runs the full pod; ### When a role is left out, its duties move. They are never dropped.
- change: rule
- why: M runs the plan, order and assignment through the Team Lead, who keeps the Manager out of the pod's traffic; S is unchanged
- old: snapshot
- new: snapshot

### Size changes and handover with a Team Lead
- sections: ### Changing size
- change: rule
- why: the Manager retires the roles that drop out when a scope moves down; a joining Team Lead takes the plan over from the Handover
- old: snapshot
- new: snapshot

### Base branch checked by the Manager
- sections: ## Inside a goal
- change: rule
- why: the Team Lead spawns with the base the Manager checked and named
- old: snapshot
- new: snapshot

### Pod contact and Team Lead rulings
- sections: ## Messages
- change: rule
- why: pod members message the Team Lead, which reports to the Manager only four things; the Team Lead's ruling follows the FINAL: rule; nobody relays a blocked pane
- old: snapshot
- new: snapshot

### Owners and escalation of plan and Developer duties
- sections: ## Who decides
- change: rule
- why: the Team Lead decides plan, order and assignment disputes in M and L and owns Developer spawning there
- old: snapshot
- new: snapshot

### 3 returns handled by the Team Lead
- sections: ## Task lifecycle
- change: rule
- why: the Team Lead steps in after 3 returns on one task in M and L
- old: snapshot
- new: snapshot

## v3 — 2026-10-16
- snapshot: history/process-v3.md

### Board removed
- sections: ## Messages
- change: reword
- why: the squad board is removed, so the Manager no longer reads it
- old:
```
- The Manager never pushes `STATUS`: it reads the board, logs, roster and task file first, and pings an agent only after 10 minutes of no pane activity.
```
- new:
```
- The Manager never pushes `STATUS`: it reads logs, the roster and the task file first, and pings an agent only after 10 minutes of no pane activity.
```

## v2 — 2026-10-15
- snapshot: history/process-v2.md

### Tighten the wording of every section
- sections: all
- change: reword
- why: roles read process.md at every start, so wording is tightened in all sections and no rule changed; the rule for editing the file now lives in the Manager's instructions
- old: snapshot
- new: snapshot

### Long suites: lock for browser files, time pass only when needed
- sections: ## Safety
- change: rule
- why: only the browser files need the lock and the runner skips phases the diff cannot affect, so suite runs no longer queue behind each other; the `flock ... nice -n 10` command text goes because the runner owns the lock, and the Developer now runs the suite in the background and waits for its completion notice (never `pgrep -f` or `pkill -f`)
- old:
```
- **Long suites: run once, read the receipt.** For a suite longer than ~2 minutes, one full run at a time for the whole squad, under a lock: `flock /tmp/<squad>-suite.lock nice -n 10 <suite command>` (a project may ship a runner that takes the lock and writes the receipts; `project.md` names it). The Developer runs the full suite once, on the final sha after every fix is in (while building, only the files it touched), and saves a receipt whose first line is `sha <git rev-parse HEAD> clean=<yes|no>` and whose tail is the suite's OK line. QA checks the receipt (same sha as the `HANDIN`, clean tree, OK), then runs only the targeted tests for the files in the diff and reads the diff; it runs the full suite itself only when the receipt is missing or its sha differs (an integration task is no exception). Targeted runs are free; the full suite is never started in the background while you wait on something else.
```
- new:
```
- **Long suites: run once, read the receipt.** A suite over ~2 minutes runs once per task. `project.md` may name the runner; it locks only its browser files and skips phases the diff cannot affect.
  - The Developer runs the full suite once, on the final sha after every fix, in the background, waits for its completion notice (never `pgrep -f` or `pkill -f`) and saves a receipt: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the suite's OK line. While building, only touched files.
  - QA checks the receipt (same sha as the `HANDIN`, clean tree, OK, its skipped-phase lines), then runs only targeted tests for the diff's files and reads the diff. It runs the full suite only when the receipt is missing or its sha differs, integration tasks included. Targeted runs are free.
```
