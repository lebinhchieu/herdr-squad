# 25 Panels dropdown opens under its button
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: none (the popover of design v5/v6 stays; only where it opens changes).
Status: ready-for-agent
Iteration: 2
Blocked by: none
Feature: 2 (hide/show panels), 14 (Columns control) (`tasks/features.md`); PO iteration 2, issue 1 (image 1)

## What the PO gets
He clicks "Panels" in the top bar and the list opens right under that button, where he looks. Today it opens at the bottom of the page.

## Rules
- A popover (the Panels list in the top bar and the Columns list in a panel header, same component) opens directly under the button that opened it: its top edge touches the button's bottom edge (gap at most 4 px), its left edge lines up with the button's left edge.
- If it would leave the window on the right, it moves left just enough to stay inside (8 px margin). If it would leave the window at the bottom, it gets a maximum height (window minus the button's bottom minus 8 px) and its list scrolls; its footer (Close / Reset columns) stays in view (design v6, section 6).
- It follows the button when the page is scrolled and when the font size changes. It closes with Close, Esc, a click outside, or a second click on the button; focus returns to the button.
- No change to what is in the list, to hide/show behaviour, to saved settings, or to the colours.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T25.AC1** Given the page at 1440 x 900, scrolled to the top, when the PO clicks "Panels", then the list opens with its top edge within 4 px of the button's bottom edge and its left edge within 2 px of the button's left edge (not at the bottom of the page, not at the page edge).
- **T25.AC2** Given the list is open, when the page is scrolled 600 px, then the list is still within 4 px of its button (it follows the button; the top bar is not sticky today and stays so, so the button scrolls with the page). Given the list is opened while the page is already scrolled so the button is on screen, then AC1 holds.
- **T25.AC3** Given the window is 1000 px wide at "Extra large" font, when the PO opens "Panels", then the whole list is inside the window (8 px margin); if it is taller than the room below the button it scrolls inside and "Close" stays visible.
- **T25.AC4** Given the list is open, when the PO presses Esc, clicks outside, or clicks "Panels" again, then it closes; given Esc, then keyboard focus is on the "Panels" button.
- **T25.AC5** Given the "Columns" button of the Tasks panel, then its list opens under the "Columns" button by the same rule as AC1 (and AC3 at Extra large, as T20.AC8 says).
- **T25.AC6** Given the PO hides a panel from the list and shows it again, then both still work as before and the list stays open (T10.AC2 holds).

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Fixtures
None beyond the fixture squad (fixture of ticket 02) and a window set to 1000 x 800.

## Touched files
Set by the Manager: `templates/board/board.js`, `templates/board/board.css`; test in `tests/test_squadboard_panels.py` (browser: position of the list against the button at 3 font sizes and 2 scroll positions).

## Comments
