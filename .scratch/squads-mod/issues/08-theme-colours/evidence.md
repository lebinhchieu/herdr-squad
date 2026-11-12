# 08 evidence

## Behaviour

Hover exists in the pane API (Box `hover`, drawn as a sibling field of props). Stripe = absolute index in the full list (group rows count), odd rows. `{bg=… hover=…}` prefixes a row Box. Selected row = focus ring the engine inverts (not colour only).

Tests: claude plugin test . = 647 pass, 0 fail; tests/test_squadruntime.py, test_squadtree.py, test_old_language_inventory.py OK. No hex in hooks/squads (AC8.4). The only 0.9.1 left is the old v15 changelog entry (history).

### List (pane-text fixtures/tree.json 30 80 --styles)
```
rows=30 cols=80 lines=12
‹bold: Squads  2 need you›  [ Refresh (r) ]
/ filter (f)
{hover=userMessageBackgroundHover} ▾ ‹bold: plugin›  ‹warning bold: needs 2›‹dim:   4 open›
{bg=bashMessageBackgroundColor hover=userMessageBackgroundHover}   ▾ ‹warning bold: ●› g1        ‹warning bold: needs 2›             ‹warning: Answer 2 questions in api›‹dim:   3/7   30m  1w›
{hover=userMessageBackgroundHover}       ‹warning bold: ●› api       ‹warning bold: needs 2›             ‹warning: Answer 2 questions›       ‹dim:   1/3   30m  1w›
{bg=bashMessageBackgroundColor hover=userMessageBackgroundHover}       ‹dim: ○› ui                            ‹dim: Nobody working: resume›   ‹dim:   0/2   30m  0w›
{hover=userMessageBackgroundHover}       ‹success: ✔› docs      ‹dim: 2026-11-11  Closed. Read the report.›
{bg=bashMessageBackgroundColor hover=userMessageBackgroundHover}   ▾‹dim:  no goal (1)›
{hover=userMessageBackgroundHover}       ‹error bold: ▲› fix                 ‹error bold: stuck 1›   ‹error: 1 task stuck›             ‹dim:   1/4   30m  0w›
{bg=bashMessageBackgroundColor hover=userMessageBackgroundHover}   ▸‹dim:  Done (2)›
{hover=userMessageBackgroundHover} ▾ old-flat  ‹dim: flat squad: not supported›
‹dim: r refresh · f filter · Tab walks rows · Esc closes›
```

### Detail (--press plugin/goal:g1)
```
rows=30 cols=80 lines=42
[ ← Back (b) ]
‹warning bold: ● needs you   plugin›
g1
‹dim: Brief of g1›
Next       ‹warning: Answer 2 questions in api›
Needs you  ‹warning bold: 2›
Stuck      ‹dim: 0›
Tasks      3/7
Last       30m
Agents     1
‹bold: Scopes›
  ‹warning bold: ●› api       ‹warning bold: needs 2›             ‹warning: Answer 2 questions›      ‹dim:   1/3   30m  1w›
  ‹dim: ○› ui                            ‹dim: Nobody working: resume›  ‹dim:   0/2   30m  0w›
  ‹success: ✔› docs      ‹dim: 2026-11-11  Closed. Read the report.›
‹bold: Commands›
‹bold: ⧉ Resume  ›(‹warning: starts work›)
‹dim:   Start the Manager again.›
‹ide:   squad-start --resume g1 --squad plugin›
‹warning:   Not yet: agents are working›
‹bold: ⧉ Board  ›(‹success: read›)
‹dim:   Open the board. Keeps running: stop with Ctrl-C.›
‹ide:   squad-board --squad plugin --goal g1›
‹bold: ⧉ Report  ›(‹warning: writes›)
‹dim:   Write the report.›
‹ide:   squad-report g1 --squad /work/repo/.claude/squads/plugin›
‹bold: ⧉ Inbox list  ›(‹success: read›)
‹dim:   List open questions.›
‹ide:   squad-inbox --home /work/repo/.claude/squads/plugin/goals/g1 list --open --no…›
‹bold: ⧉ Watchdog status  ›(‹success: read›)
‹dim:   Is the watchdog on?›
‹ide:   squad-watchdog status --home /work/repo/.claude/squads/plugin/goals/g1›
‹bold: ⧉ Sleep when idle  ›(‹warning: writes›)
‹dim:   Use when leaving the machine.›
‹ide:   squad-watchdog sleep on --home /work/repo/.claude/squads/plugin/goals/g1›
‹bold: ⧉ New scope  ›(‹warning: starts work›)
‹dim:   Add a scope to the goal.›
‹ide:   squad-start "<text>" --in-goal g1 --name <N> --squad plugin›
‹bold: ⧉ Close goal  ›(‹error bold: destructive›)
‹dim:   Close the goal.›
‹ide:   squad-close plugin --goal g1 --dry-run›
‹warning:   Not yet: scope api is open›
‹dim: Press a command to copy it. Esc or b goes back.›
```
