# Evidence: ticket 01, item view redesign

## Behaviour

Real-pane captures: `claude --plugin-dir <this worktree>` in a pty read through a pyte screen (driver: `/tmp/pi-tools/drive.py` with `--plugin-dir` pointed at the worktree). Seed items: E1 (answer, 3 options, recommendation), E5 (free reply), R1/R2 (read), E3 (withdrawn, handled). Body rows the host gives: 6 at 24 terminal rows, 11 at 40. Details was opened with Tab x7 and Enter.

### E1 answer item, Decide page

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h                              ↓ send  │
│ Which branch merges first: BRD-01 for BRD-02..06?                            │
│ ○ (a) PO merges BRD-01 as soon as it passes, and the Manager pings you ✓ rec │
│ ○ (b) Developers stack on squad/dev-board-1, branching from it by hand, whi… │
│ ○ (c) PO merges each passed branch into squad-board-spec as it passes        │
│ Note (optional):                                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h          ↓ send  │
│ Which branch merges first: BRD-01 for BRD-02..06?        │
│ ○ (a) PO merges BRD-01 as soon as it passes, and … ✓ rec │
│ ○ (b) Developers stack on squad/dev-board-1, branching … │
│ ○ (c) PO merges each passed branch into squad-board-spe… │
│ Note (optional):                                         │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h     │
│ Which branch merges first: BRD-01 for       │
│ BRD-02..06?                                 │
│ ○ (a) PO merges BRD-01 as soon as it… ✓ rec │
│ ○ (b) Developers stack on squad/dev-board-… │
│ ○ (c) PO merges each passed branch into sq… │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h                        ↓ more below  │
│ Which branch merges first: BRD-01 for BRD-02..06?                            │
│ ○ (a) PO merges BRD-01 as soon as it passes, and the Manager pings you       │
│       ✓ recommended: (a), one merge unblocks 5 tickets                       │
│ ○ (b) Developers stack on squad/dev-board-1, branching from it by hand,      │
│       which needs a base-ref option in squad-spawn outside the goal          │
│ ○ (c) PO merges each passed branch into squad-board-spec as it passes        │
│ Note (optional):                                                             │
│ [ Send answer ]                                                              │
│ Context                                                                      │
│ BRD-02..06 must branch from code that has BRD-01, and only the PO merges.    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h       ↓ context  │
│ Which branch merges first: BRD-01 for BRD-02..06?        │
│ ○ (a) PO merges BRD-01 as soon as it passes, and the     │
│       Manager pings you                                  │
│       ✓ recommended: (a), one merge unblocks 5 tickets   │
│ ○ (b) Developers stack on squad/dev-board-1, branching   │
│       from it by hand, which needs a base-ref option in… │
│ ○ (c) PO merges each passed branch into                  │
│       squad-board-spec as it passes                      │
│ Note (optional):                                         │
│ [ Send answer ]                                          │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 8h     │
│ Which branch merges first: BRD-01 for       │
│ BRD-02..06?                                 │
│ ○ (a) PO merges BRD-01 as soon as it        │
│       passes, and the Manager pings you     │
│       ✓ recommended: (a), one merge         │
│       unblocks 5 tickets                    │
│ ○ (b) Developers stack on                   │
│       squad/dev-board-1, branching from it… │
│ ○ (c) PO merges each passed branch into     │
│       squad-board-spec as it passes         │
╰─────────────────────────────────────────────╯
```

### E1 Details page (Enter on Details; the page opens at its top)

**24 x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Decide (b) ]  E1 · answer · blocks BRD-02..06 · created 8h ago           │
│ Which branch merges first: BRD-01 for BRD-02..06?                            │
│ ✓ recommends: (a), one merge unblocks 5 tickets                              │
│                                                                              │
│ Context                                                                      │
│ BRD-02..06 must branch from code that has BRD-01, and only the PO merges.    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Decide (b) ]  E1 · answer · blocks BRD-02..06 · created 8h ago           │
│ Which branch merges first: BRD-01 for BRD-02..06?                            │
│ ✓ recommends: (a), one merge unblocks 5 tickets                              │
│                                                                              │
│ Context                                                                      │
│ BRD-02..06 must branch from code that has BRD-01, and only the PO merges.    │
│ When BRD-01 passes QA whitebox, will you merge squad/dev-board-1 into        │
│ squad-board-spec?                                                            │
│                                                                              │
│ Context                                                                      │
│ • BRD-01 is at QA whitebox now.                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### R1 read item (Mark read on row 1)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R1 · read · blocks nothing · 40m           │
│ Iteration 1 passed: all 3 tasks                                              │
│ All 3 tasks passed QA whitebox and blackbox.                                 │
│                                                                              │
│   │ tests/run_suite.py --tz   OK  412 passed, 0 failed                       │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  ↓ more below           │
│ R1 · read · blocks nothing · 40m                         │
│ Iteration 1 passed: all 3 tasks                          │
│ All 3 tasks passed QA whitebox and blackbox.             │
│                                                          │
│   │ tests/run_suite.py --tz   OK  412 passed, 0 failed   │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]            │
│ R1 · read · blocks nothing · 41m            │
│ Iteration 1 passed: all 3 tasks             │
│ All 3 tasks passed QA whitebox and          │
│ blackbox.                                   │
│                                             │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R1 · read · blocks nothing · 41m           │
│ Iteration 1 passed: all 3 tasks                                              │
│ All 3 tasks passed QA whitebox and blackbox.                                 │
│                                                                              │
│   │ tests/run_suite.py --tz   OK  412 passed, 0 failed                       │
│                                                                              │
│ • Branches: squad/dev-po-inbox-tui-1, -2, -3                                 │
│ • Evidence: .scratch/po-inbox-tui/issues/01-item-view/evidence.md            │
│ [ Mark read ]                                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]                         │
│ R1 · read · blocks nothing · 42m                         │
│ Iteration 1 passed: all 3 tasks                          │
│ All 3 tasks passed QA whitebox and blackbox.             │
│                                                          │
│   │ tests/run_suite.py --tz   OK  412 passed, 0 failed   │
│                                                          │
│ • Branches: squad/dev-po-inbox-tui-1, -2, -3             │
│ • Evidence:                                              │
│   .scratch/po-inbox-tui/issues/01-item-view/evidence.md  │
│ [ Mark read ]                                            │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]            │
│ R1 · read · blocks nothing · 42m            │
│ Iteration 1 passed: all 3 tasks             │
│ All 3 tasks passed QA whitebox and          │
│ blackbox.                                   │
│                                             │
│   │ tests/run_suite.py --tz   OK  412 passe │
│   │ d, 0 failed                             │
│                                             │
│ • Branches: squad/dev-po-inbox-tui-1, -2,   │
│   -3                                        │
╰─────────────────────────────────────────────╯
```

### R2 read item with sections (blank row above headings in the tall tier)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R2 · read · blocks nothing · 40m           │
│ Long plan with many sections to read before the next check in                │
│ Section 1                                                                    │
│ • point 1a with some words to wrap around the pane width a bit more          │
│ • point 1b                                                                   │
│ Section 2                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  ↓ more below           │
│ R2 · read · blocks nothing · 40m                         │
│ Long plan with many sections to read before the next     │
│ check in                                                 │
│ Section 1                                                │
│ • point 1a with some words to wrap around the pane width │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]            │
│ R2 · read · blocks nothing · 41m            │
│ Long plan with many sections to read before │
│ the next check in                           │
│ Section 1                                   │
│ • point 1a with some words to wrap around   │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R2 · read · blocks nothing · 41m           │
│ Long plan with many sections to read before the next check in                │
│ Section 1                                                                    │
│ • point 1a with some words to wrap around the pane width a bit more          │
│ • point 1b                                                                   │
│                                                                              │
│ Section 2                                                                    │
│ • point 2a with some words to wrap around the pane width a bit more          │
│ • point 2b                                                                   │
│                                                                              │
│ Section 3                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  ↓ more below           │
│ R2 · read · blocks nothing · 42m                         │
│ Long plan with many sections to read before the next     │
│ check in                                                 │
│ Section 1                                                │
│ • point 1a with some words to wrap around the pane width │
│   a bit more                                             │
│ • point 1b                                               │
│                                                          │
│ Section 2                                                │
│ • point 2a with some words to wrap around the pane width │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]            │
│ R2 · read · blocks nothing · 42m            │
│ Long plan with many sections to read before │
│ the next check in                           │
│ Section 1                                   │
│ • point 1a with some words to wrap around   │
│   the pane width a bit more                 │
│ • point 1b                                  │
│                                             │
│ Section 2                                   │
│ • point 2a with some words to wrap around   │
╰─────────────────────────────────────────────╯
```

### Handled item (E3, withdrawn)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h                       ↓ more below  │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated.                                        │
│ Context                                                                      │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h, burning about 1% of 7d │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h   ↓ more below  │
│ What name for the new mode?                              │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by │
│ E1, the Manager decided alone after the PO delegated.    │
│ Context                                                  │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h,    │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h    │
│ What name for the new mode?                 │
│ Withdrawn by the Manager 2026-10-29 15:05:  │
│ Superseded by E1, the Manager decided alone │
│ after the PO delegated.                     │
│ Context                                     │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h                                     │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated.                                        │
│ Context                                                                      │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h, burning about 1% of 7d │
│ every 5 min with 5 agents working. Account 1 was at 91% 7d 7 h ago, and its  │
│ token has expired, so the auto-switch can't see it or switch to it.          │
│ Iteration 2 (8 tickets) won't fit in what's left.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h                 │
│ What name for the new mode?                              │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by │
│ E1, the Manager decided alone after the PO delegated.    │
│ Context                                                  │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h,    │
│ burning about 1% of 7d every 5 min with 5 agents         │
│ working. Account 1 was at 91% 7d 7 h ago, and its token  │
│ has expired, so the auto-switch can't see it or switch   │
│ to it. Iteration 2 (8 tickets) won't fit in what's left. │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 8h    │
│ What name for the new mode?                 │
│ Withdrawn by the Manager 2026-10-29 15:05:  │
│ Superseded by E1, the Manager decided alone │
│ after the PO delegated.                     │
│ Context                                     │
│ Account 2 is at 94% 7d (resets Wed 05:00)   │
│ and 79% 5h, burning about 1% of 7d every 5  │
│ min with 5 agents working. Account 1 was at │
│ 91% 7d 7 h ago, and its token has expired…  │
│ … 3 more rows [ Details ]                   │
╰─────────────────────────────────────────────╯
```

### What the captures show
- E1 at 24x80 (6 body rows): Back + header + `↓ send`, title, three options (one `✓ rec`), Note. Send and Context are on the next page.
- At 40 rows (11 body rows) the reason row sits under (a) once and Send is in view; the hint reads `↓ context` or `↓ more below`.
- At 47 and 60 columns the title can take 2 rows, so Note falls to the next page. This is item.md section 3 (title up to 2 rows) meeting a narrow pane, not a bug; the tests allow one extra row below 80 columns (T2 carve-out, named in the HANDIN).
- Read items: `Mark read (m)` on row 1; at 47 columns the header drops to its own row 2 (drop order step 4), Back and Mark read stay.
- Details: the host keeps the scroll it needed to show the focused button, so a first capture opened mid-page. The mod now puts the focus ring on Back (`$.ui.focus`) after each switch, and the page opens at its top. The mock harness does not deliver `ui.focus` to a hook, so this is proven by the captures, not by a unit test.
- Not captured on the real pane: an item with no body (the CLI did not list my seed item; the no-body state is covered by the unit test `state rows: no body`), and a free-text item at 40 rows.

## Tests
- `claude plugin test .`: 507 pass, 0 fail.
- Python, run from `tests/`: test_po_inbox_mod (505+ plugin tests inside, SQUAD_REQUIRE_CLAUDE=1), test_po_inbox_contract, test_squadinbox, test_old_language_inventory, test_dev_rules_size: all OK.
- T15 grep: `grep -rl 'show-all\|Show all\|more lines\|full title\|your pick' tests/ hooks/po-inbox/` (the strings this ticket removed from the pane): hits only inside `hooks/po-inbox/` (the files edited here, and `fixtures/visual.ts` text). No test under `tests/` names a pane string. Every hit file was run (the whole plugin test run).
- Glossary: no new term; "Details page" and "Decide page" are screen names in the design only.
- Old test to new test: V-01 -> T2; 3.1c -> notice-above-title; 3.1d -> `3.1e`/body fold tests at bodyRows 14 and 10 are covered by `body fold: E1 at 6 rows` and `state rows`; M1/M3/M4/M5 rewritten under the same names; QAB F3 (`… full header`) -> `long blocks: Decide clips the header, Details draws it whole`; Show all tests -> Details tests; Select label cut -> `state rows: very long option`.

### R6 read item with no body (title only)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R6 · read · blocks nothing · 51m           │
│ Heads-up: nightly job finished                                               │
│ [ Mark read ]                                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R6 · read · blocks nothing · 51m           │
│ Heads-up: nightly job finished                                               │
│ [ Mark read ]                                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Title only: the title row and one Mark read button, no empty body area at either height.

## Return 3: Manager rulings (FINAL 01) and fixes

- **F1 (P6):** an answer item is stored as `cut-title<br>full question<br>…`. Real fixture: `squad-inbox add --kind answer --title <first 80 chars> --body-file F` (F line 1 is the full question). Before: title cut at 80, the full question repeated under Context. After: title is the full question, body starts at the next line. Real pane 24x80 (E6): title `Shall we ship … before Friday at noon, or` / `wait for QA first?`, no repeat. A title cut that ends in a space is handled (length judged before the trim). Tests: markup.test.ts `P6 title cut at 80 characters`.
- **F2:** a read item that blocks nothing drops `blocks nothing` last (after clipping and the age), so the header stays on row 1 at 60 and 47 columns. At 80 columns the header copy is unchanged on purpose. Real pane 24x60, read item R7: `R7 · read · 1h` on row 1.
- **F3:** `… 1 more row` is singular. The mid-word cut at the row edge is allowed. The lost line break in the short-tier fold of a long first block: not changed. I did not find a bug in the fold; the first block over the budget is clipped as one text.
- **F4:** the Details hint is `↓ more below` at every width (the `↓ context` hint is only for Decide).
- **F5 (Manager ruling, FINAL):** AC2 holds at 80 and 60 columns. At 47 columns a 2-row title may push Note (24 rows) or Note and Send (40 rows) below the first viewport. The order is kept and Tab reaches them. The title is not shortened further. Real pane 24x47 (E6): title 2 rows, Note on the last row.

## QA whitebox

### QA whitebox, task 01, sha 6455014: FAIL (3 findings, all small)

Checked: diff vs main (6d5bad2), `claude plugin test .` from the worktree (507 pass, 0 fail, run by me), technical AC T1-T15, one live read-only run of the pane (E1 24x80, E2 40x80, R2 24x47, Done list and handled E3 24x80, driven with the Developer's seed items; I did not press Send or Mark read). Live output matches the design and the evidence captures.

Passed: T1 (`heightTier`, core.ts:400, boundary test), T2/T3/T10 (item.test.ts), T4, T5 (typing b/m/digits in Note), T6 state rows, T7 (fold count with blank heading rows), T8 (markup.test.ts, 5 cases), T9, T12 (actions.ts diff is only the rename; listScreen/doneScreen unchanged), T14 (ADR 0007 one line, matches section 12), T15 (grep run, hits listed). No `.skip`/`.todo`; test count rose in every touched file. Carve-outs accepted: +1 row at widths below 80 for a 61-char title (design allows a 2-row title), `ui.focus` on Back has no unit test (harness cannot deliver it; Details page-top shown on the real pane in evidence.md).

#### F1 (T11, dead code): `recPointer` is no longer used
`hooks/po-inbox/core.ts:428` `export function recPointer` has no caller outside `core-visual.test.ts:249-290` after the top pointer row was removed. T11 says the pointer use is removed, not left unused. Pass: delete `recPointer` and its tests (the `clipCells` tests in the same describe stay). If ticket 02 needs it, say so in the ticket and keep it.

#### F2 (style, one return per REV-17): `wrapCells2` duplicates `wrapRows`
`hooks/po-inbox/draw.tsx:321` `wrapCells2` wraps by words to N rows with `…` on the last; `hooks/po-inbox/ui.tsx:138` `wrapRows` does the same job (past `maxRows` the last row ends with `…`). Also: the name ends in `2`; `let cut` (draw.tsx:326, assigned at :335) is written and never read; `clipLine` (draw.tsx:346) is a one-line alias of `clipCells`. Pass: one wrap helper (move `wrapRows` into draw.tsx and import it in ui.tsx, or make `optionRows` use it), no write-only variable, call `clipCells` directly. Existing option tests must stay green.

#### F3 (T13, real samples): no live capture of an item with no body
T13 lists the idle/constant cases: handled item, item with no body, read item. evidence.md has the handled and read items but the Developer says the no-body seed item was not listed. Pass: capture a title-only answer item on a real pane at 24 and 40 rows (no Context, no Details, no hint) and add it to evidence.md.

#### Re-check at 52a1e4a (2nd round, LC-3b)

F1 fixed: `recPointer` and its tests are gone; no other hit in hooks/.
F2 fixed: one `wrapRows` in core.ts:428, used by ui.tsx and draw.tsx; `wrapCells2`, `clipLine`, `cut` gone. Option wrap tests (item.test.ts:998) pass at 1 and 2 rows.
F3 fixed: evidence.md "R6 read item with no body" has captures at 24 and 40 rows.
Tests: `claude plugin test .` 493 pass, 0 fail (my run).

##### F4 (new, same defect class as F1): dead import left by the removal
- hooks/po-inbox/core-visual.test.ts:4 imports `sanitize`. Its only use was in the deleted recPointer test; no use remains (`grep -n sanitize` = this line only).
- Why it matters: LC-8b defect class "dead code left after a removal"; the removal was not finished.
- Pass: drop `sanitize` from that import. Nothing else needed; I re-check that one line.

#### Re-check at 2f39c66 (diff 7ea5df2..2f39c66)

Run: `claude plugin test .` 500 pass, 0 fail (my run). Code read: markup.ts split, ui.tsx topLayout fallback, `row`/`rows`, ctxBelow in Details. The code changes look right. Two of the three new tests do not test what their names say.

##### F5: the singular-row test cannot fail
- hooks/po-inbox/item.test.ts:1157 `F3: the fold marker is singular for one hidden row` opens a 40-line body and asserts `/… \d+ more rows\n/`. That is the plural, with many hidden rows. The new branch `hiddenRows === 1 ? 'row' : 'rows'` (ui.tsx:505) is never run with 1. M1 at item.test.ts:601 was loosened to `rows?`, so it passes either way.
- Mutation check by reading: change the code back to always `rows` and all 500 tests still pass.
- Pass: a test that gets exactly 1 hidden row and asserts `… 1 more row\n` and not `1 more rows`. Name it for what it does.

##### F6: the Details hint test never asserts the hint
- hooks/po-inbox/item.test.ts:1165 is named "says `↓ more below`" but only asserts `not.toContain('↓ context')`. If the hint vanished, it would pass.
- Pass: assert `toContain('↓ more below')` for a Details page that is taller than the pane (E1 at 47 cols, 24 rows, or a longer body if E1 fits), and keep the `not` line.

Not findings: F2 test (item.test.ts:1147) and the four markup.test.ts P6 tests are real and assert the behaviour.

## QA blackbox

### QA blackbox, task 01 (item view redesign)

Verdict: **FAIL** on 7ea5df2 (tested on 6455014 and 52a1e4a; 7ea5df2 only drops a test import, so I did not re-run the matrix).
Method: real `claude` pane through a pty driver (pyte screen dump), worktree as `--plugin-dir`, copies of the seed home. No code read.
Captures (text dumps of the pane): `captures/`. Sizes run: 24 and 40 rows x 80, 60, 47 columns. Items: E1 (3 options + rec), E2 (2 options, rec text without key), E5 (free text), R1, R2 (read), E3 (handled, in Done), a title-only read item, 7-option item, 80-char-title item.

#### AC results

| AC | What I did / saw | Result |
|---|---|---|
| 1 Matches design | 24x80 E1 matches the item.md short-tier mock row by row (`captures/m24x80-E1-p0.txt`). 40x80 E1 matches the tall-tier mock (`m40x80-E1-p0.txt`). Read item has Mark read (m) on row 1; handled item order correct. Differences listed in Findings. | FAIL (F2..F5) |
| 2 Answer item | Back+header+hint on one row; options are `○/●` rows; `✓ rec` tag short tier, reason row tall tier; no pointer row; Note; Send; Context. At 24x80 and 24x60 title, 3 options and Note are in the first viewport. At 24x47 Note is not (title 2 rows) (F5). | PASS at 80/60, see F5 at 47 |
| 3 Nothing pre-picked | All rows `○` on open. Note only, Enter: sent as free reply ("E1 answered. Sending to the Manager."). Enter in empty Note: `⚠ Nothing to send: pick an option or type a reply.` | PASS |
| 4 Details | Tab to Details, Enter: page opens at top with `[ ← Decide (b) ]` focused, full header/title/rec, whole body. PageDown scrolls. `b` returns to Decide, pick `●` (b) kept (`m24x80-E1pick-*`). End of page has a second Decide button. | PASS |
| 5 Read item | `Mark read (m)` row 1, second `[ Mark read ]` at end, short tier folds `… 21 more rows [ Details ]` (`m24x80-R2-p2`). Title-only read item: no marker, no hint. | PASS (header copy F2) |
| 6 Handled item | State line first, `Your answer` with option and note, options with `●`, then Context (`u5-p0.txt`, 40x80). | PASS |
| 7 Body | Chips have no padding spaces. Tall tier: blank row above headings, none above the first; short tier none (`m40x80-R2-p0`, `m24x80-R2-p0`). | PASS |
| 8 Title rule P6 | Item with an 80-char stored title and a body whose first line is the full question: pane title stays cut at 80 chars (`…before Friday at noon`) and Context starts with the full text. Expected: full first body line as title, dropped from body. (`v1-p0.txt`, `v1-p1.txt`) | **FAIL** (F1) |
| 9 Heights | Short tier at 6 rows and tall tier at 11 rows behave as designed in all runs. | PASS |
| 10, 11 | Not mine (whitebox / Developer evidence). | n/a |

#### Findings

- **F1 (AC8, blocking).** Repro: `squad-inbox add --kind answer --title "<first 80 chars of Q>" --body-file F` where F line 1 is the full question (97 chars), then open the item at 24x80. Pane title: `Shall we ship … before Friday at noon` (cut). Context first row: `Shall we ship … at noon, or wait for QA?`. The full text should be the title and should not repeat in Context. If this is not how such items arrive in real use, give me the fixture that triggers P6 and I re-check.
- **F2 (design diff, low).** Read item header reads `R1 · read · blocks nothing · 54m`; the design mock (section 6) shows `R1 · read · 3m`. At 60 and 47 columns the header then moves to its own row 2 (`m24x60-R1`, `m24x47-R1-p0`); the drop order in section 13 says clip `blocks …` first, which would keep it on row 1.
- **F3 (low).** Fold marker reads `… 1 more rows` (plural). On E2 at 24x80 the last shown row is `…or switch to it. Iterat…`: the line break of the body is lost and the row is cut mid-word (`m24x80-E2-p1`). Details shows the same text as two rows.
- **F4 (low).** Details hint is `↓ context` at 47 columns and `↓ more below` at 60/80; design section 4 says `↓ more below` on Details.
- **F5 (needs owner ruling, not counted as fail by me).** At 47 columns a 2-row title pushes Note out of the first viewport at 24 rows (`m24x47-E1-p0`), and at 40x47 Note and Send are out (`m40x47-E1-p0`). Developer flagged this; geometry makes AC2 impossible there. Designer is retired: the Manager decides if this is accepted.

#### Not tested

Docked fullscreen layout; send-failed and "item changed while open" notices; cell-not-written notice. The pty driver is flaky when many panes start at once (first keys sometimes lost); every result above was seen on a clean run.

---

### Re-check on 580f199 (final sha; 2f39c66 plus test-only change)

Verdict: **PASS**. Real `claude` pane via pty driver, worktree as `--plugin-dir`. Captures: `captures/` (`a*`, `b*`, `c*`, `r4-80-*`).

| Finding | What I did | What I saw | Result |
|---|---|---|---|
| F1 title P6 | Answer item, stored title = first 80 chars, body line 1 = full question (97 chars), 24x80 (`a80-E6-p0/p1`) | Title is the full question on 2 rows; Context starts with the next body line only | PASS |
| F1 cut ending in space | Same, 80th char a space (`c80-E9-p0`) | Not exercisable by the CLI: `squad-inbox add` trims the trailing space, so the stored title is 79 chars, and the 80-char rule does not apply (title stays cut, full question repeats in Context). Matches design text ("80 characters long"). Note only, not a fail | note |
| F2 header | Read item with "blocks nothing" at 60 and 47 cols (`b60-R4`, `b47-R4`, `b47-R1`, `a60-R1`) | Header on row 1 with Back and Mark read; at 47 the age is dropped too (design order) | PASS |
| F2 at 80 | Read item blocks nothing, 24x80 (`r4-80-readblocksnothing`) | `R1 · read · blocks nothing · now` kept (Developer says on purpose; design mock shows no "blocks nothing") | accepted, low |
| F3 | E2 at 24x80 (`b80-E2-p1`) | `… 1 more row [ Details ]` singular. Last shown row still ends mid-word `Iterat…` (Developer: allowed) | PASS (cosmetic note) |
| F4 | E1 at 47 cols, Tab x7 to Details, Enter (`c47-E1-det`) | `[ ← Decide (b) ]  ↓ more below` | PASS |
| F5 order at 47 | E1 24x47 (`b47-E1-p0/p1`) | Title 2 rows, options, then Note, Send, Context in order after PageDown (accepted by FINAL 01) | PASS |

Not tested (as before): docked fullscreen layout; send-failed, item-changed and cell-not-written notices.
