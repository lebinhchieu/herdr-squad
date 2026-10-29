# Evidence: ticket 05, integration of tickets 01-04

## Behaviour

One branch holds all four tickets. Ticket 02 (`a1dd827`) was merged into `cc79738` (tickets 01, 03, 04) with `git merge --no-ff`. Only the ticket drafts conflicted (add/add): `03-body-styles.md` and `04-inbox-body-guide.md` kept the `cc79738` version (with `## Review`); ticket 02's draft (with its own `## Review`) and its evidence folder came in clean. The code merged without a conflict.

One small fix was needed after the merge: a comment in `hooks/po-inbox/done.test.ts` (ticket 02) used the word "size", and `tests/test_promotion_0_6_0.py` allows that word in `hooks/` only in listed files. The comment now says "a new terminal width" (same kind of fix as ticket 03's `a724d71`). No assertion and no test logic changed.

### AC1: history

Merge commit `aab73e2`. `git merge-base --is-ancestor` for both tickets:

```
$ git merge-base --is-ancestor a1dd827 HEAD && echo ok-02
ok-02
$ git merge-base --is-ancestor cc79738 HEAD && echo ok-04
ok-04
```

`git log --oneline 4a818d6..HEAD` (the 02, 03 and 04 commits, plus the merge and the comment fix on top):

```
a51b15a 05: reword a comment in done.test.ts (size-word allow-list in test_promotion_0_6_0; same fix as a724d71)
aab73e2 05: merge ticket 02 (a1dd827) into 01+03+04 branch
cc79738 04: evidence
3266b91 04: review fixes (guide accuracy, plain English, test cleanup), ticket notes
e1ce001 04: inbox body writing guide, parser test, guide/fixture sync test
d5109f5 03: evidence widths fix, review notes
f54e29c 03: evidence (real-pane captures, dark and light colour proof)
6004d58 03: ## Review
e485f05 03: review fixes (cut tags, caption whole, one > or <, one tag vocabulary, comments)
a1dd827 02: review fixes (4-row outcome test), ## Review
bd1cada 02: real-pane evidence
8dc79d3 02: Details row under a cut outcome, 2-space Done gap, ADR 0007 line
a724d71 03: reword a test name (size-word allow-list)
ff87d8a 03: item-level tests for body styles
23d1dec 03: tests for chips, diagram, links, badges, parser
a38f57d 02: tests for the list, the heading row, the Done list and the done item
9a9867a 03: wip parser, chips, diagram draw, table cells, fixtures
ac5d83b 02: list and Done list redesign (one row per item, heading row, outcome first)
98adb71 02: ticket copies 02-04 from the scope, design notes
ea95aa0 03: design notes
3e6a739 03: add tickets 03 and 04 drafts
```

### AC3: real-pane smoke check (24 rows x 80 columns)

`claude --plugin-dir <this worktree>` in a pty, the screen read through a pyte terminal model. A scratch inbox was seeded with the plugin's own `bin/squad-inbox add` from the fixtures in `hooks/po-inbox/fixtures/visual.ts` (`guideE1`, `guideR1`, `chips` + `relations`). Only the pane box is shown; theme: dark. Built on the merge commit plus the comment fix (code is the same as `a51b15a`).

**List (ticket 02).** One row per item, a heading row per group, the age on the right:

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Inbox · 2 to answer · 2 to read                                     ↓ 1 more │
│ Blocks work (1)                                                              │
│ 1: E1  answer  Which branch merges first: BRD-01 for BRD-02..06?         10h │
│ Blocks nothing (3)                                                           │
│ 2: E2  answer  Ship the board before Friday noon, or wait for QA?        10h │
│ 3: R1  read  Iteration 1 passed: all 3 tasks                             now │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Answer item with options (ticket 01).** Full question as title, options with the recommended one marked, then the note field; the body (`Context`) sits below the fold:

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back ]  E1 · blocks BRD-02..06 · 10h                             ↓ send  │
│ Which branch merges first: BRD-01 for BRD-02..06?                            │
│ ○ (a) PO merges BRD-01 as soon as it passes                            ✓ rec │
│ ○ (b) Developers stack on squad/dev-board-1                                  │
│ ○ (c) PO merges each passed branch as it passes                              │
│ Note (optional):                                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**Body styles (ticket 03).** Item R2 is the `chips` fixture followed by the `relations` fixture. First page: the three callouts as filled chips.

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ] [ Mark read (m) ]  R2 · read · blocks nothing · created now   │
│ Styles check: callouts, badges and a relations diagram                       │
│  ◆ decision  Merge BRD-01 first (a): one merge unblocks 5 tickets.           │
│  ⚠ warning  Option (b) needs a change outside this scope.                    │
│  › info  The suite ran at 14:02.                                             │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Next page: the badge table (`✓ ok`, `✗ fail`, `⚠ warn`, `– skip`), columns aligned:

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Task              WB        BB                                               │
│ ────────────────  ────────  ────────                                         │
│ 01 item view       ✓ ok      ✓ ok                                            │
│ 02 list and done   ✓ ok      ✗ fail                                          │
│ 03 body styles     ⚠ warn    – skip                                          │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Last page: the relations diagram (connectors, state tags, legend row):

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│   dependency map (A ──> B: B waits for A)                                    │
│   BRD-01 [ok] ──> spec [ok] ──┬──> BRD-02 [ok]                               │
│                               ├──> BRD-03 [warn]                             │
│                               └──> BRD-04..06 [skip]                         │
│   legend  [ok] done  [warn] at risk  [skip] skipped                          │
│ [ Mark read ]                                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### AC2: targeted tests

- `claude plugin test .`: 612 pass, 0 fail (10 files).
- `tests/test_inbox_body_guide.py`: ok (2 tests).
- `tests/test_po_inbox_mod.py`: ok (2 tests; it runs the mod suite again, 612 pass).
- `tests/test_promotion_0_6_0.py`: ok (8 tests) after the comment fix. Before it: 1 failure, `test_bin_and_hooks_hits_are_allow_listed`, because of the word "size" in the ticket 02 comment (this failure is in `a1dd827` alone; it is not two tickets disagreeing).
- `tests/test_old_language_inventory.py`: ok (2 tests; run from `tests/` because it imports `rulesview`).

The full suite was not run (QA whitebox runs it once on the final sha).
