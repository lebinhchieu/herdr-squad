# Evidence: ticket 02, list and Done list redesign

## Behaviour

Real-pane captures: `claude --plugin-dir <this worktree>` in a pty read through a pyte screen (driver as in ticket 01, with the plugin dir set to this worktree). Seed: the design data. Answers E1 (blocks BRD-02..06), E2 (blocks all remaining work), E5 (blocks nothing); reads R1, R2; done E3 (withdrawn), E4 (answered in chat), R3 (read). Body rows the host gives: 6 at 24 terminal rows, 11 at 40. Widths are terminal columns (the pane body is 4 narrower). Ages are real clock ages (the seed is from today). A second seed (`long`) has a 330-character withdrawal reason on E3.

What to look at: the list is one row per item at 24 rows (3 items, was 2) with the short age on the last cell; the Done button and `↓ N more` are on the heading row; at 40 rows items keep two rows. The Done list is heading + 1 row per item. The done item opens with the outcome line under the title; a long one is cut at 3-4 rows with `… full text [ Details ]` and Details shows it whole.

### List

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]                   ↓ 2 more │
│ Blocks work (2)                                                              │
│ 1: E1  answer  Which branch merges first: BRD-01 for BRD-02..06?          9h │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d                       9h │
│ Blocks nothing (3)                                                           │
│ 3: E5  answer  What name should the new mode have in the CLI and in the…  9h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 answer · 2 read  [ Done (3) (d) ]     ↓ 2 more │
│ Blocks work (2)                                          │
│ 1: E1  answer  Which branch merges first: BRD-01 fo…  9h │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d   9h │
│ Blocks nothing (3)                                       │
│ 3: E5  answer  What name should the new mode have i…  9h │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ Inbox · 3 answer · 2 read  [ Done (3) (d) ] │
│ Blocks work (2)                             │
│ 1: E1  answer  Which branch merges fir…  9h │
│ 2: E2  answer  Usage limits: account 2…  9h │
│ Blocks nothing (3)                          │
│ 3: E5  answer  What name should the ne…  9h │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 to answer · 2 to read  [ Done (3) (d) ]                   ↓ 1 more │
│ Blocks work (2)                                                              │
│ 1: E1  answer  Which branch merges first: BRD-01 for BRD-02..06?             │
│     blocks BRD-02..06 · created 9h ago                                       │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d                          │
│     blocks All remaining work · created 9h ago                               │
│ Blocks nothing (3)                                                           │
│ 3: E5  answer  What name should the new mode have in the CLI and in the doc… │
│     blocks nothing · created 9h ago                                          │
│ 4: R1  read  Iteration 1 passed: all 3 tasks                                 │
│     blocks nothing · created 1h ago                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ Inbox · 3 answer · 2 read  [ Done (3) (d) ]     ↓ 1 more │
│ Blocks work (2)                                          │
│ 1: E1  answer  Which branch merges first: BRD-01 for BR… │
│     blocks BRD-02..06 · 9h                               │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d      │
│     blocks All remaining work · 9h                       │
│ Blocks nothing (3)                                       │
│ 3: E5  answer  What name should the new mode have in th… │
│     blocks nothing · 9h                                  │
│ 4: R1  read  Iteration 1 passed: all 3 tasks             │
│     blocks nothing · 1h                                  │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ Inbox · 3 answer · 2 read  [ Done (3) (d) ] │
│ Blocks work (2)                             │
│ 1: E1  answer  Which branch merges first: … │
│     blocks BRD-02..06 · 9h                  │
│ 2: E2  answer  Usage limits: account 2 is … │
│     blocks All remaining work · 9h          │
│ Blocks nothing (3)                          │
│ 3: E5  answer  What name should the new mo… │
│     blocks nothing · 9h                     │
│ 4: R1  read  Iteration 1 passed: all 3 tas… │
│     blocks nothing · 1h                     │
╰─────────────────────────────────────────────╯
```

### List, after PageDown (the rest of the items)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ 1: E1  answer  Which branch merges first: BRD-01 for BRD-02..06?          9h │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d                       9h │
│ Blocks nothing (3)                                                           │
│ 3: E5  answer  What name should the new mode have in the CLI and in the…  9h │
│ 4: R1  read  Iteration 1 passed: all 3 tasks                              1h │
│ 5: R2  read  Long plan with many sections to read before the next check…  1h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ 1: E1  answer  Which branch merges first: BRD-01 fo…  9h │
│ 2: E2  answer  Usage limits: account 2 is at 94% 7d   9h │
│ Blocks nothing (3)                                       │
│ 3: E5  answer  What name should the new mode have i…  9h │
│ 4: R1  read  Iteration 1 passed: all 3 tasks          1h │
│ 5: R2  read  Long plan with many sections to read b…  1h │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ 1: E1  answer  Which branch merges fir…  9h │
│ 2: E2  answer  Usage limits: account 2…  9h │
│ Blocks nothing (3)                          │
│ 3: E5  answer  What name should the ne…  9h │
│ 4: R1  read  Iteration 1 passed: all 3…  1h │
│ 5: R2  read  Long plan with many secti…  1h │
╰─────────────────────────────────────────────╯
```

### Done list

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)                                     │
│ 1: E3  withdrawn  What name for the new mode?                             1h │
│ 2: E4  answered in chat  Old question handled in chat                     1h │
│ 3: R3  read  Deploy note                                                  1h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)                 │
│ 1: E3  withdrawn  What name for the new mode?         1h │
│ 2: E4  answered in chat  Old question handled in ch…  1h │
│ 3: R3  read  Deploy note                              1h │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)    │
│ 1: E3  withdrawn  What name for the ne…  1h │
│ 2: E4  answered in chat  Old question …  1h │
│ 3: R3  read  Deploy note                 1h │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)                                     │
│ 1: E3  withdrawn  What name for the new mode?                             1h │
│     withdrawn: Superseded by E1, the Manager decided alone after the PO del… │
│ 2: E4  answered in chat  Old question handled in chat                     1h │
│ 3: R3  read  Deploy note                                                  1h │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)                 │
│ 1: E3  withdrawn  What name for the new mode?         1h │
│     withdrawn: Superseded by E1, the Manager decided al… │
│ 2: E4  answered in chat  Old question handled in ch…  1h │
│ 3: R3  read  Deploy note                              1h │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]   Done · newest first (3)    │
│ 1: E3  withdrawn  What name for the ne…  1h │
│     withdrawn: Superseded by E1, the Manag… │
│ 2: E4  answered in chat  Old question …  1h │
│ 3: R3  read  Deploy note                 1h │
╰─────────────────────────────────────────────╯
```

### Done item, withdrawn (design reason)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h                       ↓ more below  │
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
│ [ ← Back (b) ]  E3 · blocks nothing · 9h   ↓ more below  │
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
│ [ ← Back (b) ]  E3 · blocks nothing · 9h    │
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
│ [ ← Back (b) ]  E3 · blocks nothing · 9h                                     │
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
│ [ ← Back (b) ]  E3 · blocks nothing · 9h                 │
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
│ [ ← Back (b) ]  E3 · blocks nothing · 9h    │
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

### Done item, withdrawn with a long reason (cut, `… full text [ Details ]`)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h                          ↓ context  │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated the naming question to the Manager in   │
│ the check-in on Tuesday; the options were never sent, so nothing was lost a… │
│ … full text [ Details ]                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h      ↓ context  │
│ What name for the new mode?                              │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by │
│ E1, the Manager decided alone after the PO delegated     │
│ the naming question to the Manager in the check-in on T… │
│ … full text [ Details ]                                  │
╰──────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h    │
│ What name for the new mode?                 │
│ Withdrawn by the Manager 2026-10-29 15:05:  │
│ Superseded by E1, the Manager decided alone │
│ after the PO delegated the naming questio…  │
│ … full text [ Details ]                     │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h                       ↓ more below  │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated the naming question to the Manager in   │
│ the check-in on Tuesday; the options were never sent, so nothing was lost    │
│ and the earlier answer in the file stays valid. Nothing is needed from the…  │
│ … full text [ Details ]                                                      │
│ Context                                                                      │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h, burning about 1% of 7d │
│ every 5 min with 5 agents working. Account 1 was at 91% 7d 7 h ago, and its  │
│ token has expired, so the auto-switch can't see it or switch to it. Iterat…  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**40 rows x 60**

```
╭────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h   ↓ more below  │
│ What name for the new mode?                              │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by │
│ E1, the Manager decided alone after the PO delegated     │
│ the naming question to the Manager in the check-in on    │
│ Tuesday; the options were never sent, so nothing was lo… │
│ … full text [ Details ]                                  │
│ Context                                                  │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h,    │
│ burning about 1% of 7d every 5 min with 5 agents         │
│ working. Account 1 was at 91% 7d 7 h ago, and its token… │
╰──────────────────────────────────────────────────────────╯
```

**40 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · blocks nothing · 9h    │
│ What name for the new mode?                 │
│ Withdrawn by the Manager 2026-10-29 15:05:  │
│ Superseded by E1, the Manager decided alone │
│ after the PO delegated the naming question  │
│ to the Manager in the check-in on Tuesday…  │
│ … full text [ Details ]                     │
│ Context                                     │
│ Account 2 is at 94% 7d (resets Wed 05:00)   │
│ and 79% 5h, burning about 1% of 7d every 5  │
│ min with 5 agents working. Account 1 was a… │
╰─────────────────────────────────────────────╯
```

### Done item, Details page of the long reason (whole text)

**24 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · answer · blocks nothing · created 9h ago  ↓ more below  │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated the naming question to the Manager in   │
│ the check-in on Tuesday; the options were never sent, so nothing was lost    │
│ and the earlier answer in the file stays valid. Nothing is needed from the   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

**24 rows x 47**

```
╭───────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  ↓ more below                │
│ E3 · answer · blocks nothing · created 9h   │
│ ago                                         │
│ What name for the new mode?                 │
│ Withdrawn by the Manager 2026-10-29 15:05:  │
│ Superseded by E1, the Manager decided alone │
╰─────────────────────────────────────────────╯
```

**40 rows x 80**

```
╭────────────────────────────────────────────────────────────────────────────✕─╮
│ [ ← Back (b) ]  E3 · answer · blocks nothing · created 9h ago  ↓ more below  │
│ What name for the new mode?                                                  │
│ Withdrawn by the Manager 2026-10-29 15:05: Superseded by E1, the Manager     │
│ decided alone after the PO delegated the naming question to the Manager in   │
│ the check-in on Tuesday; the options were never sent, so nothing was lost    │
│ and the earlier answer in the file stays valid. Nothing is needed from the   │
│ PO. If the name should change later, ask again with the new options and the  │
│ current usage numbers so the choice does not depend on this thread. The      │
│ Manager will note the decision in the iteration file..                       │
│ Context                                                                      │
│ Account 2 is at 94% 7d (resets Wed 05:00) and 79% 5h, burning about 1% of 7d │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Tests

`claude plugin test .` (all 10 test files of the mod; they are the files this ticket touches or that cover the same screens): 525 pass, 0 fail. New tests are in `list.test.ts` (short and tall tier, heading row drop order at 80/60/59/47/40, hint, fold, widths for ASCII/CJK/emoji at 80..30) and `done.test.ts` (Done heading narrow order, short age, tall withdrawn sub-row, done item outcome, Details). No `bin/` or `templates/` text was touched, so there are no `grep -rl` hits to run beyond the mod tests.
