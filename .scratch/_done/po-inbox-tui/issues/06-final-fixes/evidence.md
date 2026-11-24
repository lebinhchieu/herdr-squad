# Evidence: ticket 06, four fixes from the final check

## Behaviour

Real pane: `claude --plugin-dir <this worktree>` in a pty, 24 rows, the screen read through a pyte terminal model (the driver of QA blackbox, plus a step that runs a shell command). A scratch inbox was seeded with the plugin's own `bin/squad-inbox`: E1 to E3 (answer), R1 (read, long body), one done item. Only the pane box is shown. Built on `1f724f2`; the code is final there.

### AC5a, W-F1: refused send, 60-word reason, 80 columns

The PO picks (a), types a note, presses Send. Just before, the Manager withdraws E1 with a 60-word reason, so the CLI refuses. The 6 body rows hold Back, the notice, the title, the outcome and the Details row.

First 6 rows:

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E1 · blocks BRD-02..06 · 11h                      ↓ context  │
│ ⚠ squad-inbox: E1 is withdrawn at 2026-10-29T11:29:00Z: reason0 reason1      │
│ reason2 reason3 reason4 reason5 reason6 reason7 reason8 reason9 reason10 re… │
│ Which branch merges first?                                                   │
│ Withdrawn by the Manager 2026-10-29 18:29: reason0 reason1 reason2 reason3…  │
│ … full text [ Details ]                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

After PageDown: the "changed" line and the unsent note come after the Details row.

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ This item changed while you were reading it.                                 │
│ Your unsent note (not sent):                                                 │
│ my words                                                                     │
│ ○ (a) BRD-01                                                           ✓ rec │
│ ○ (b) BRD-02                                                                 │
│ Context                                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

Before the fix (`8a3abd5`) the Details row was 4 rows below the fold (QA whitebox F1). The tests `done item after a refused send, ...: the outcome and its Details row stay in the first viewport` (done.test.ts, 3 cases) failed before the fix and pass now.

### AC5b, B-F2: list heading at 80, 60 and 47 columns

The hint goes first, then the long words, then Done moves to its own row.

80 columns: long counts, button and hint.

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 to answer · 1 to read  [ Done (1) (d) ]                   ↓ 1 more │
│ Blocks work (1)                                                              │
```

60 columns: the long counts and the button fit, the hint does not, so the hint is dropped (before: short words AND the hint).

```
╭────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 to answer · 1 to read  [ Done (1) (d) ]        │
│ Blocks work (1)                                          │
```

47 columns: the long counts and the button do not fit, so the short words, no hint.

```
╭───────────────────────────────────────────✕─╮
│ Inbox · 3 answer · 1 read  [ Done (1) (d) ] │
│ Blocks work (1)                             │
```

Test: `heading row, drop order ... (80, 60, 59, 56, 47, 40 columns)` in list.test.ts (56 is the body width of a 60-column terminal).

Note for the Manager: the old rule "under 60 columns the words are short" (V-15) is gone for the list heading; the short words now come only when the long ones do not fit. `list.test.ts` had two assertions of the old rule; I changed them (59 columns with the hint; three counts at 42 and 44 columns; no done items at 47 columns shows the long words).

### AC5c, B-F1: the list after Back from a scrolled R1

Repro: `/inbox`, open R1 (`4`), PageDown twice, `b`.

Before (`8a3abd5`): the heading row is off the screen; the list starts at `Blocks work`.

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Blocks work (1)                                                              │
│ 1: E1  answer  Which branch merges first?                                11h │
│ Blocks nothing (3)                                                           │
│ 2: E2  answer  Ship the board before Friday noon, or wait for QA?        11h │
│ 3: E3  answer  What name for the new mode?                               11h │
│ 4: R1  read  Iteration 1 passed: all 3 tasks                              3h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

After (`1f724f2`): the list opens at the top; the Done button is in view.

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 to answer · 1 to read  [ Done (1) (d) ]                   ↓ 1 more │
│ Blocks work (1)                                                              │
│ 1: E1  answer  Which branch merges first?                                11h │
│ Blocks nothing (3)                                                           │
│ 2: E2  answer  Ship the board before Friday noon, or wait for QA?        11h │
│ 3: E3  answer  What name for the new mode?                               11h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

The page now asks the host for the focus on its first button (the Done button, else the first item; the Done list asks for Back). Tests: `list scroll: ...` in mod.test.ts (3 tests; they fail without the call).

### Tests

- `claude plugin test .`: 618 pass, 0 fail (10 files).
- `tests/test_inbox_body_guide.py`, `test_po_inbox_mod.py`, `test_promotion_0_6_0.py`, `test_hooks_json.py` ok; `test_old_language_inventory.py` and `test_po_inbox_contract.py` ok (run from `tests/`).
- The full suite was not run (QA whitebox runs it).
