# Task 05: Integration of tickets 01-04

Status: handed in
Source ticket: `.claude/squads/plugin/scopes/po-inbox-tui/tasks/issues/05-integration.md` (merge only; code changes only for a real break the merge causes).

## What was done
- Merged ticket 02 (`a1dd827`) into `cc79738` (01 + 03 + 04) with `git merge --no-ff`: merge commit `aab73e2`. Only the drafts of 03 and 04 conflicted (add/add): both kept from `cc79738`. Ticket 02's draft (with its own `## Review`) and its evidence folder came in as they are. No code conflict; `core.ts` is not touched by ticket 02, so the expected `core.ts` clash did not happen.
- One fix after the merge, `a51b15a`: a comment in `hooks/po-inbox/done.test.ts` (ticket 02) said "a size". `tests/test_promotion_0_6_0.py` (`test_bin_and_hooks_hits_are_allow_listed`) allows that word in `hooks/` only in listed files. The comment now says "a new terminal width". The failure was already in `a1dd827` alone, so it is not two tickets disagreeing, and no assertion changed (same kind of fix as ticket 03's `a724d71`). The Manager should confirm this is inside the "real break" rule.
- Tests and real-pane captures: `05-integration/evidence.md`.

## Review
Run: `mattpocock-skills:code-review` on `git diff cc79738..HEAD` (Standards and Spec axes, two reviewers). The diff is ticket 02's change plus the comment reword. Nothing below was fixed here: ticket 05 allows no refactors or new features, and these points are in ticket 02's code, which has its own `## Review`.

### Spec axis
- Merge is `--no-ff` with parents `cc79738` and `a1dd827`; both `merge-base --is-ancestor` checks pass (AC1). The 03 and 04 drafts and folders are identical to `cc79738`; 02 keeps its `## Review` and evidence (confirmed).
- `a51b15a` (comment reword) is not a merge break: the word comes from 02. It is a comment, not an assertion. Flagged for the Manager (see above).
- Notes carried over from 02 (already accepted by the Manager in the plan): a long outcome keeps 3 rows plus a Details row; the `↓ N more` hint counts items; `ui.test.ts` hotkey list reordered to `['d','1','2','3','4']` because the Done button moved to the heading row (hotkeys themselves unchanged).

### Standards axis
- No conflict between 02 and 03: `heightTier`, `DEFAULT_BODY_ROWS`, `bodyBudget` and `tableLayout` were already in `core.ts` at `cc79738`; the `draw.tsx` signatures that `ui.tsx` calls match; new `key="details"` does not collide. The targeted tests and real-pane captures agree (evidence).
- Possible gap (reviewer, not verified by me): the Done item's outcome `room` does not subtract the notice rows and floors at 2, so a long title plus a notice might push the `… full text` row below the first viewport (ADR 0007). No test covers it. Suggest a follow-up check by QA whitebox.
- Smells (judgement calls, ticket 02 code, not changed): `function top(tree)` is copied in `list.test.ts` and `done.test.ts`; the `bodyRows`-or-default plus `heightTier` line is repeated in three screens (and in `bodyBudget`); `headingRow` takes 7 arguments and is called twice in `listScreen`; `short` means two things; `doneScreen` and `headingRow` each decide how the heading fits.
- Glossary: "heading row" and "short age" may be missing from `CONTEXT.md` (note for `/domain-modeling`).
