# Evidence: ticket 01, item view redesign

## Behaviour

Real-pane captures: `claude --plugin-dir <worktree>` in a pty (pyte screen), seed items E1 (answer, 3 options, recommendation), R1/R2 (read), E3 (withdrawn, handled). `Body rows` = rows the host gives the pane: 6 at 24 terminal rows, 11 at 40. The Tab key moved focus; the host scrolls the pane to follow it.

### E1 answer item, Decide page (first viewport)

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
│ unblocks 5 tickets                          │
│ ○ (b) Developers stack on                   │
│       squad/dev-board-1, branching from it… │
│ ○ (c) PO merges each passed branch into     │
│       squad-board-spec as it passes         │
╰─────────────────────────────────────────────╯
```

### E1 Details page (opened with Tab to Details, Enter), 24 rows x 80

**Details**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ When BRD-01 passes QA whitebox, will you merge squad/dev-board-1 into        │
│ squad-board-spec?                                                            │
│                                                                              │
│ Context                                                                      │
│ • BRD-01 is at QA whitebox now.                                              │
│ • 5 tickets wait on it: BRD-02, 03, 04, 05, 06.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### R1 and R2 read items

**R1 24x80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R1 · read · blocks nothing · 26m           │
│ Iteration 1 passed: all 3 tasks                                              │
│ All 3 tasks passed QA whitebox and blackbox.                                 │
│                                                                              │
│   │ tests/run_suite.py --tz   OK  412 passed, 0 failed                       │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**R1 24x47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]            │
│ R1 · read · blocks nothing · 27m            │
│ Iteration 1 passed: all 3 tasks             │
│ All 3 tasks passed QA whitebox and          │
│ blackbox.                                   │
│                                             │
╰─────────────────────────────────────────────╯
```

**R2 24x80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R2 · read · blocks nothing · 26m           │
│ Long plan with many sections to read before the next check in                │
│ Section 1                                                                    │
│ • point 1a with some words to wrap around the pane width a bit more          │
│ • point 1b                                                                   │
│ Section 2                                                                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**R2 40x80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R2 · read · blocks nothing · 27m           │
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

### Handled item (withdrawn)

**24x80**

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

**40x80**

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

### What the captures show
- E1 at 24x80: Back + header + `↓ send`, title, all three options and Note in the 6 rows; `✓ rec` once. At 40 rows the reason row sits under (a) and Send is in view.
- 47 columns: title takes 2 rows, so Note falls to the next page (hint says so at 60 and 80; at 47 the header has no room for the hint, drop order step 1).
- Read item: `Mark read (m)` on row 1; at 47 columns the header drops to row 2 (drop order step 4); Back and Mark read stay.
- Handled item: state line first, then Context.
- Known host behaviour: after pressing Details the host keeps the scroll offset it had to show the focused Details button, so the page opened scrolled down in my capture. The mod cannot set the scroll.

## Tests
- `claude plugin test .`: 505 pass, 0 fail (before the final commit; see the hand-in sha).
- Targeted Python: `tests/test_po_inbox_mod.py`, `test_po_inbox_contract.py`, `test_squadinbox.py`, `test_old_language_inventory.py`, `test_dev_rules_size.py` all OK.
- grep rule (T15): `grep -rl 'Show all\|show-all\|your pick\|Your answer\|recommends:\|more lines\|full title\|Options' tests/ hooks/po-inbox/ docs templates bin` hits: tests/test_squadinbox_answer.py, test_squad_close.py, test_squadinbox.py, tests/fixtures/inbox/home/escalations.md, tests/po_inbox_fixtures.py (all CLI/fixture text, not pane text; this ticket changes none of them), hooks/po-inbox/*, bin/squad-spawn, bin/squadinbox.py, templates/*/escalations.md (not touched). Ran: test_squadinbox, test_po_inbox_contract (fixtures), test_po_inbox_mod. Green.
- Glossary: no new term added; `Details page` and `Decide page` are screen names in the design only.
