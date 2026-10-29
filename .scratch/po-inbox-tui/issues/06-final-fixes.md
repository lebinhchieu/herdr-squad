# Task 06: Fixes from the final check (four findings)

Status: ready-for-agent
Duties: plan-owner=manager, design-notes=dev, tech-ac=dev, business-ac=ticket, code-check=dev (self-review, Manager confirms), behaviour-check=dev evidence (Manager confirms), handin-target=manager, suite-owner=qa-white (at the end only), promote-owner=qa-white, risk-owner=manager, doubt-owner=manager, choice-owner=manager
Team: no QA while building; a fresh QA whitebox and QA blackbox re-check after you. Hand in to the Manager. Branch from `8a3abd5` (final sha of 01-05). `BLOCKED 06` on a risk flag or doubt. Targeted tests only (touched files + `grep -rl` hits); no full suite (QA whitebox runs it once on your final sha).
Goal: scope brief `../scope.md`, plan `../iterations/1.md`. Designs in `../ui-design/` (list.md, done.md). Reports: `../evidence/final/qa-w.md` (F1, F2) and `../evidence/final/qa-b.md` (F1, F2).

## What (all four; nothing else, no refactor, no clean-up)
1. **W-F1, done item outcome room (ticket 02 AC6).** `hooks/po-inbox/ui.tsx` (~line 592): the outcome `room` ignores the notice (up to 2 rows), the line "This item changed while you were reading it." and the "Your unsent note" block. After a refused send the `… full text [Details]` row sits below the first viewport. Fix so the outcome and its Details row stay in the first viewport (subtract those rows from `room`, or draw the outcome and Details row before the draft block). Test in `done.test.ts`: refused send, 60-word reason, 80x6, the `full text` row is within the first 6 rows.
2. **W-F2, guide Whys (ticket 04 AC1).** `docs/inbox-body-guide.md` lines ~53, 60, 61, 62 (Rules): add a one-line `Why:` under each of the four rules that lack one. Plain short English.
3. **B-F2, drop order (ticket 02 AC4, list.md section 7).** At 60 columns the heading shows short counts AND the `↓ N more` hint. The order is: drop the hint first, then shorten counts, then move Done to its own row. When the long counts plus the button fit, show them without the hint. Test at 80, 60, 47 columns (list.test.ts).
4. **B-F1, scroll carry-over (ticket 02 AC4).** After Back from a scrolled item, after Send and after Mark read, the list opens scrolled down, so the heading row (Done button, hint) is off screen. Reset the list scroll to the top whenever the list is shown again from an item. Repro: open R1, PageDown twice, `b`. Test it.
Ruled, do NOT touch: QA-W F3-F5, QA-B F3 (below 47 columns), F4 (short-tier fold mid-word cut), F5 (waiting sub-row timestamp).

## Touches
`hooks/po-inbox/ui.tsx`, `done.test.ts`, `list.test.ts` (and `ui.test.ts` if scroll state is tested there), `docs/inbox-body-guide.md`; `tests/test_inbox_body_guide.py` stays green. Not touched: `markup.ts`, `draw.tsx`, `core.ts`.

## AC
1-4 as the four items above, each with a test that fails before the fix. 5. Real-pane evidence at 24 rows: (a) the refused-send done item at 80 columns, (b) the list heading at 60 columns, (c) the list after Back from a scrolled R1; in `issues/06-final-fixes/evidence.md`; `squad-evidence check` ok. 6. Run `mattpocock-skills:code-review` on `git diff 8a3abd5..HEAD`; write `## Review`. Re-run the `grep -rl` hits for any changed string (CLAUDE.md); the test_promotion test fails on the word "size" in test comments: avoid it.

## Design notes
(Developer writes here before building.)
