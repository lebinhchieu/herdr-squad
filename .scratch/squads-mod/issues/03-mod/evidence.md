## Behaviour

Command: `hooks/squads/pane-text FILE ROWS COLS [--press KEYS] [--filter TEXT] [--copy-fails] [--refresh-error MSG]`
FILE is tree.json, tree-empty.json, real.json, or `-` for stdin (`bin/squad-tree --json | hooks/squads/pane-text - 11 60`).
Keys: copy = press a command key like `c0:board:head` in a detail; Esc back = `back`; filter = `--filter TEXT`; refresh error = `--refresh-error MSG`.

`pane-text fixtures/tree.json 11 60`
```
rows=11 cols=60 lines=11
Squads  2 need you  [ Refresh (r) ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1      needs 2             Answer 2 qu…  3/7   30m
      ● api     needs 2             Answer 2 …  1/3   30m
      ○ ui                          Nobody wo…  0/2   30m
      ✔ docs      2026-11-11  Closed. Read the report.
  ▾ no goal (1)
↓ 2 more
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text fixtures/tree-empty.json 6 40`
```
rows=6 cols=40 lines=3
Squads  [ Refresh (r) ]
No squads here.
Start one with /squad:squad-init
```

`pane-text fixtures/real.json 11 100`
```
rows=11 cols=100 lines=11
Squads  [ Refresh (r) ]
/ filter (f)
▾ accounts  needs 0  0 open
  ▸ Done (2)
▾ board  needs 0  0 open
  ▸ Done (1)
▾ plugin  needs 0  3 open
  ▾ · process-fixes                        All scopes closed: close goal  20/200 10h  0w
      ✔ no-touches       2026-11-11  Closed. Read the report.
↓ 13 more
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text fixtures/tree.json 40 40`
```
rows=40 cols=40 lines=12
Squads  2 need you  [ Refresh (r) ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1    needs 2             Answe…
      ● api   needs 2             Ans…
      ○ ui                        Nob…
      ✔ docs  2026-11-11  Closed. Read …
  ▾ no goal (1)
      ▲ fix             stuck 1   1 t…
  ▸ Done (2)
r refresh · f filter
```

Refresh error:
```
rows=11 cols=60 lines=11
Squads  2 need you  [ Refresh (r) ]
⚠ squad-tree failed: squad-tree failed (last good list show…
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1      needs 2             Answer 2 qu…  3/7   30m
      ● api     needs 2             Answer 2 …  1/3   30m
      ○ ui                          Nobody wo…  0/2   30m
      ✔ docs      2026-11-11  Closed. Read the report.
↓ 3 more
r refresh · f filter · Tab walks rows · Esc closes
```

Tests: `claude plugin test` 640 pass, 0 fail; test_po_inbox_mod, test_squadtree, test_hooks_json, test_windows_safe, test_utf8_helpers, test_instructions: 64 OK.
