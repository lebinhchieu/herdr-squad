# 21 stale token save
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: none (no new screen; the existing "settings not shared" and "layout not saved" messages stay).
Status: ready-for-agent
Iteration: 2
Blocked by: 09, 10
Feature: 14 (`tasks/features.md`); found by QA blackbox while checking ticket 10

## What the PO gets
After the board server restarts, saving a setting still works. Today it fails with "Settings could not be saved" until the PO reloads the page.

## Rules
- The page's save token comes from page load and the server forgets it on restart (ticket 09, T09.AC5). When a save is refused because the token is old, the page fetches a new token and retries that save once, with no message to the PO.
- One retry only. If the retry fails too, the normal failure rule of ticket 09 applies (T09.AC2, AC3 messages). No retry loop, no retry on a Host refusal.
- A write with a wrong or missing token and no page behind it is still refused (T09.AC5 stays true).

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T21.AC1** Given the page is open, the server restarts, and the PO then hides a panel (or changes font size), then no error shows, and after a reload the change is still there.
- **T21.AC2** Given the same restart, then the header returns to "updated hh:mm:ss" within 5 s (T10.AC16) and the save in AC1 is not lost.
- **T21.AC3** Given a save with a made-up token sent directly to the server, then it is refused and `board-ui.json` is unchanged (T09.AC5 still holds).
- **T21.AC4** Given the retry also fails (file unwritable), then the page shows "settings not shared" as T09.AC2 says, and does not retry again.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: confirmed (`tasks/business-ac-agreement.md`).

## Touched files
Set by the Manager: `templates/board/board.js` (save code); test in `tests/test_squadboard_page.py`.

## Comments
