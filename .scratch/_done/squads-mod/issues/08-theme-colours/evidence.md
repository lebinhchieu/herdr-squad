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

## Review
AC trace
- AC8.1 | hooks/squads/squads.test.tsx "list: every second row has the stripe..." and "scrolling keeps the stripe of each row" | `claude plugin test .`
- AC8.2 | same first test (hover=userMessageBackgroundHover on every row Box; engine drops it when the pointer leaves) | `claude plugin test .`; list dump above
- AC8.3 | squads.test.tsx "styles: ..." (`‹ide: `) | `claude plugin test .`; detail dump above
- AC8.4 | `grep -rniE '#[0-9a-f]{6}|rgb\(' hooks/squads/*.ts hooks/squads/*.tsx` (no hit outside fixtures.ts data); 647 plugin tests pass | as written
- AC8.5 | this file, List and Detail dumps | `hooks/squads/pane-text fixtures/tree.json 30 80 --styles [--press plugin/goal:g1]`
- AC8.6 | plugin.json, changelog v16, tests/test_squadruntime.py | `grep -rl '0\.9\.1'` hits only the old v15 changelog entry (history)

## Review qa-w

### 08 QA whitebox, sha 6ed9247 (branch squad/plugin/squads-mod/plugin-dev-squads-mod-8, base main 291f4d3)

Verdict: PASS. No findings that break an AC or a test.

#### Checks (my own runs, read-only clone at 6ed9247)
| AC | Check | Result |
|---|---|---|
| 8.1 | ui.tsx `draw(r, at)`: stripe on `win.from + i` odd (absolute index, group rows count); tests "every second row..." and "scrolling keeps the stripe" | ok |
| 8.2 | Box has `key` and `hover={{backgroundColor: HOVER}}` on the same Box. Host types (claude-code.d.ts BoxProps.hover): hover applies while pointer is over the nearest keyed Box, this one included; no hook | ok |
| 8.3 | core.ts COMMAND_STYLE = `{color:'ide'}` (not bold before, not bold now); test expects `‹ide: ` | ok |
| 8.4 | `grep -rniE '#[0-9a-f]{6}|rgb\(' hooks/squads/*.ts hooks/squads/*.tsx` no hit; `cd hooks/squads && claude plugin test ../..` 647 pass 0 fail; python (squadruntime squadtree windows_safe utf8_helpers instructions) 127 OK | ok |
| 8.5 | evidence.md dumps; I re-ran `pane-text fixtures/tree.json 30 80 --styles`: same stripe/hover lines | ok |
| 8.6 | plugin.json 0.9.2, changelog v16, test_squadruntime.py 0.9.2; only `0.9.1` left is the v15 changelog entry (history) | ok |

SQ-10: no bin/ or printed text touched; not needed.

#### Follow-ups (not blocking)
- Not live-verified in the real host: that the hover background paints on a Box that has no own background, and that the stripe fills the pane width. The type docs say hover may override backgroundColor, and a Box in a column stretches. QA blackbox to look if a real screen is possible.
- Test limit: the tests check the props (bg, hover), not the pointer. The engine applies hover with no hook, so there is nothing more to test in the mod.
- Old `0.9.1` in the v15 changelog entry is history, kept.

## Review qa-b

### 08 QA blackbox, sha 6ed9247

Method: `git archive 6ed9247` to a scratch dir; `hooks/squads/pane-text <file> ROWS COLS --styles [--press KEY]` on the fixtures; same commands on `git archive c16cabf` (ticket 07) to compare. No code read. Types file of the mod API read for what `hover` does.

| AC | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| 8.1 stripe | live | tree.json 30x80 --styles; 8x80 with `--press below` and `below,below`; `--press plugin/done`; `--filter api` | Rows alternate: plugin none, g1 `bg=bashMessageBackgroundColor`, api none, ui bg, docs none, no-goal bg, fix none, Done bg, old-flat none. Group rows count. Scrolling: no-goal stays striped, fix stays plain, Done stays striped. Opening Done: g0 plain, tiny striped. Selected row: see limit 1 | pass |
| 8.2 hover | live (prop) | same dumps | Every row has `hover=userMessageBackgroundHover` (striped and plain). The API doc says the surface applies `hover.backgroundColor` while the pointer is over the Box and removes it on leave. Real pointer: see limit 2 | pass (prop level) |
| 8.3 command | live | `--press plugin/goal:g1`, `plugin/goal:g1/scope:api`, `plugin/scope:fix`, `plugin` (squad) | All command lines `‹ide: ...›` (07 sha: `permission`); titles bold as before; "Not yet" commands also `ide` | pass |
| 8.4 no hex, text unchanged | live | `grep -rniE '#[0-9a-f]{6}\|rgb\(' hooks/squads/*.ts hooks/squads/*.tsx` = no hit (exit 1). Plain dumps (no --styles) of tree.json 30x80, goal detail, 8x60, 14x40, tree-empty, real.json 30x100 diffed with 07 sha: 0 diff lines. `--styles` diff = only the `{bg/hover}` prefixes and permission->ide | pass |
| 8.5 evidence | shot | Developer's evidence.md has the list and detail style dumps; my dumps match | pass |
| 8.6 version | live | plugin.json = 0.9.2; changelog entry "Plugin 0.9.2"; test_squadruntime.py names 0.9.2; `grep -rl '0\.9\.1'` hits only changelog.md = the old 0.9.1 entry (history) | pass |
| tests | live | `claude plugin test .` on the archive: 647 pass, 0 fail | pass |

Limits (could not check, no real terminal screen here):
1. The selected row's look, and whether a stripe/hover fills the full pane width on a real screen: the dump is text and style runs only. The group rows (`no goal (1)`, `Done (2)`) are short text; a Box row should stretch, but I did not see it.
2. A real mouse move over a row. Checked only that the engine's hover prop is set on every row.
Chieu: one look at the real pane (hover a row, scroll) closes both.
