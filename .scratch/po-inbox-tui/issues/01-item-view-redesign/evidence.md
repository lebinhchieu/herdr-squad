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
