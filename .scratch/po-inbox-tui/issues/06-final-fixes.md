# Task 06: Fixes from the final check (four findings)

Status: handed in
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
- W-F1 (`ui.tsx`): `handledBlock` now returns the outcome (`parts`) apart from the refused-send leftovers (`changed`, `unsent`, `extraRows`). The done item draws outcome, Details row, then an `aside` box with the leftovers. `room` also subtracts the notice rows; the cut floor is 1 row so the Details row always fits.
- W-F2: four `Why:` lines in `docs/inbox-body-guide.md`; new test `test_every_rule_has_a_why_line` (fails on the 8a3abd5 guide for those four rules).
- B-F2 (`headingRow`): drop order is long words + hint, long words, short words, Done on its own row. The old "under 60 columns the words are short" rule is gone for the list heading (Manager ruling: accepted, follows list.md section 7). Changed list.test.ts assertions: 59 columns long + hint; new 56 case; 42/44 columns; no Done at 47 shows long words.
- B-F1 (`actions.ts`): `focusTop` asks `$.ui.focus` for the Done button, else the first item, else Back on the Done list. Called from `goTo` (list and Done), after Mark read and after a successful Send. The test host has no `ui.focus`, so `mod.test.ts` uses a fake `$` and checks the key asked for.

## Review

`mattpocock-skills:code-review` on `git diff 8a3abd5..HEAD` (Standards and Spec sub-agents). Evidence: `issues/06-final-fixes/evidence.md`.

Fixed after review:
- Spec: item 2 had no test. Added `test_every_rule_has_a_why_line` in `tests/test_inbox_body_guide.py`; it fails on the old guide for 4 rules.
- Spec: the W-F1 test could pass without a `full text` row. The 60-word, 80x6 case now requires it (`mustCut`); the comment is clearer.
- Standards: the claimed dead `longOk` and stale comment were already gone (checked in the diff).

Kept, on purpose:
- `focusTop` is a focus request, not a scroll reset. The host scrolls only as far as the focused button needs. With a Done button the heading is in view (shown in the evidence). With no done items the first item gets the focus, so the heading row can still sit above the view by a row; the host gives no scroll call. Not checked in a real pane.
- `goTo` calls `focusTop` on every move to the list or Done list, not only after a scrolled item. This keeps one rule. It changes the focus ring after Back from an unscrolled item (it lands on Done).
- The `changed` line now follows the Details row (it is not in `room`). This is the ticket's second option.
- Cut floor `Math.max(1, room - 1)` (was 2): needed so Details stays in view at 80x6.
- Smells (bare focus keys `'done'`/`'back'`, `focusTop` knowing the list order, `handledBlock` return shape): judgement calls; ticket says no refactor. Not changed.
- Glossary gaps (outcome, Details row, done item, unsent note) for `/domain-modeling`.
- The 60-column heading test passes before and after; the 56, 44 and 42 cases are the ones that fail on the old code.

Tests: `claude plugin test .` 618 pass; Python tests for guide, mod, promotion, hooks_json, old_language_inventory, po_inbox_contract ok.
