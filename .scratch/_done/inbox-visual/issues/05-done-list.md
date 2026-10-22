Status: ready
Blocked by: 02, Designer's final `ui-design/IV-05.md`
Task ID: IV-05
Design: ui-design/IV-05.md
Files touched: `hooks/po-inbox/ui.tsx` (`doneScreen` only), `hooks/po-inbox/done.test.ts` (new)

# IV-05: the done list: outcome colours and the fold (droppable)

**Done when the done list draws each outcome word in its V-15 colour, newest first, at most 7 rows then `+N more`, as `ui-design/IV-05.md` shows.** The one droppable ticket: if the budget is short the Tech Lead drops it (V-25 is a should-have); the done-item view is IV-03's. Business AC: V-20 (done list), V-25.

## Technical AC
1. `done.test.ts`: each outcome (read, answered, answered in chat, answered in the file, withdrawn, removed) has the `outcomeTone` colour (green, green, green, amber, dim, dim); order newest first as before; 7/8/12 edges with `+N more` expanding in place; resets on leaving (T10).
2. Rows fit the pane at 80, 59, 40, 30 columns (`rowsFor`); the withdrawn reason is never dropped.
3. ESC, OSC, U+202E in title and withdrawn reason draw none.
4. Pane-text screenshots at 80 and 40 columns in `dev-evidence.md`.
5. Common AC 1-8 of `design.md`.

## QA whitebox additions (agreed 2026-10-16; each is a pass condition; a line with the same number replaces the ticket line above)
Source: `evidence/qa-w-ac.md` in the scope folder.

- **5.1 (tighten)** The tone test iterates the done kinds present in the contract fixtures (not a hand list). Newest first with equal timestamps keeps a stable order. 0 done items: no Done button (as today). The withdrawn reason is 300 characters and has CJK: wraps or ends with ellipsis, the word "withdrawn" stays.
