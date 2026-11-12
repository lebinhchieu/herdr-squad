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

## Return 1 (QA whitebox and blackbox, sha 8a499dc)

Keys: a goal/scope detail starts with Resume (c0), so Board is `c1:board:head`; a squad detail has Board as `c0:board:head`. Fold a goal: `plugin/goal:g1:fold`.

`pane-text hooks/squads/fixtures/tree.json 12 100 --filter api`
```
rows=12 cols=100 lines=6
Squads  2 need you  [ Refresh (r) ]
/ api▏
▾ plugin  needs 2  4 open
  ▾ ● g1        needs 2             Answer 2 questions in api  3/7   30m  1w
      ● api       needs 2             Answer 2 questions         1/3   30m  1w
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text hooks/squads/fixtures/tree.json 12 100 --filter zzzz`
```
rows=12 cols=100 lines=4
Squads  2 need you  [ Refresh (r) ]
/ zzzz▏
No match for "zzzz".
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text hooks/squads/fixtures/tree.json 12 100 --refresh-error boom`
```
rows=12 cols=100 lines=12
Squads  2 need you  [ Refresh (r) ]
⚠ Refresh failed, nothing was changed (last list kept): squad-tree failed: boom
[ Try again ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1        needs 2             Answer 2 questions in api  3/7   30m  1w
      ● api       needs 2             Answer 2 questions         1/3   30m  1w
      ○ ui                            Nobody working: resume     0/2   30m  0w
      ✔ docs      2026-11-11  Closed. Read the report.
↓ 3 more
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text hooks/squads/fixtures/tree.json 12 46`
```
rows=12 cols=46 lines=12
Squads  2 need you  [ Refresh (r) ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1        needs 2  Answer 2 questions i…
      ● api       needs 2  Answer 2 questions
      ○ ui        Nobody working: resu…  0/2
      ✔ docs  2026-11-11  Closed. Read the re…
  ▾ no goal (1)
      ▲ fix       stuck 1  1 task stuck  1/4
  ▸ Done (2)
r refresh · f filter
```

`pane-text hooks/squads/fixtures/tree.json 12 38`
```
rows=12 cols=38 lines=12
Squads  2 need you  [ r ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● g1        needs 2  Answer 2 que…
      ● api       needs 2  Answer 2 q…
      ○ ui        Nobody working: res…
      ✔ docs  2026-11-11  Closed. Rea…
  ▾ no goal (1)
      ▲ fix       stuck 1  1 task stu…
  ▸ Done (2)
r refresh · f filter
```

`pane-text hooks/squads/fixtures/tree.json 12 30`
```
rows=12 cols=30 lines=12
Squads  2 need you  [ r ]
/ filter (f)
▾ old-flat  flat squad: not s…
▾ plugin  needs 2  4 open
  ▾ ● g1     needs 2  Answer …
      ● api   needs 2  Answer…
      ○ ui        Nobody work…
      ✔ docs  2026-11-11  Clo…
  ▾ no goal (1)
      ▲ fix   stuck 1  1 task…
  ▸ Done (2)
r refresh · f filter
```

`pane-text /tmp/tree-esc.json 12 100`
```
rows=12 cols=100 lines=12
Squads  2 need you  [ Refresh (r) ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▾ ● ansi      needs 2             Answer 2 questions in api  3/7   30m  1w
      ● api       needs 2             Answer 2 questions         1/3   30m  1w
      ○ ui                            Nobody working: resume     0/2   30m  0w
      ✔ docs      2026-11-11  Closed. Read the report.
  ▾ no goal (1)
      ▲ fix                 stuck 1   1 task stuck               1/4   30m  0w
  ▸ Done (2)
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text hooks/squads/fixtures/tree.json 12 100 --press plugin/goal:g1:fold --then /tmp/tree2.json`
```
rows=12 cols=100 lines=9
Squads  2 need you  [ Refresh (r) ]
/ filter (f)
▾ old-flat  flat squad: not supported
▾ plugin  needs 2  4 open
  ▸ ● g1        needs 2             Answer 2 questions in api  6/7   30m  1w
  ▾ no goal (1)
      ▲ fix                 stuck 1   1 task stuck               1/4   30m  0w
  ▸ Done (2)
r refresh · f filter · Tab walks rows · Esc closes
```

`pane-text hooks/squads/fixtures/tree.json 12 100 --loading`
```
rows=12 cols=100 lines=2
Squads  [ Refresh (r) ]
Reading .claude/squads …
```

Tests after return 1: `claude plugin test` 644 pass, 0 fail; test_po_inbox_mod, test_squadtree (new T2.12), test_hooks_json, test_windows_safe, test_utf8_helpers, test_instructions: all OK.
