# 27 Work time filter block restyle
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO, E10).
Design: `ui-design/design-v7.md` (start only when it reads `Status: final`; LC-2b). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 2
Blocked by: design-v7
Feature: 16 (`tasks/features.md`, ticket 16); PO iteration 2, issue 3 (image 3)

## What the PO gets
The filter block of the Work time panel looks like the rest of the page: soft background, room around the text, controls in order. Today it is white, has no padding, and the text touches the border.

## Rules
- The block holds: **Task** (All tasks, each task, unattributed), **View** (Last 1 h, Today, 3 days, All), the zoom buttons ("-", "+") and the arrows (earlier / later). It keeps all of them, with the same behaviour (ticket 16: T16.AC3, AC4, AC7); only the look changes.
- Light Mango Parrot tokens only, read from the theme file (`project.md`): background and border from the panel/border tokens, text from the ink/muted tokens, the active View choice marked by weight and an ink-on-border-token look, not by mango (mango stays only for needs-you, T10.AC12). No pure white (#FFFFFF), no dark background, no new colour.
- Padding inside the block at least 8 px on every side; the text of a label or button is at least 6 px from its own border; controls are 8 px apart and sit on one line at 1440 px; they wrap onto a second line (never overlap, never get cut) at 1000 px and at "Extra large".
- A visible focus ring on every control (keyboard use); the buttons have a hover state; "-" and "+" and the arrows keep their tooltips.
- No `%` character.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T27.AC1** Given the Work time panel at 1440 x 900, then the filter block's computed background and border colours equal the token values that `design-v7.md` lists for the block (token name and hex each; none is #FFFFFF).
- **T27.AC2** Given the filter block, then the space between its edge and its first control is at least 8 px on all four sides, and the space between any label or button text and that control's own border is at least 6 px.
- **T27.AC3** Given the filter block at 1440 px, then Task, View, "-", "+" and the arrows are on one line in that order with 8 px between them; given 1000 px wide and given "Extra large", then there is no overlap and no cut text, and a second line is used only when the controls do not fit on one.
- **T27.AC4** Given the active View choice, then it is marked by the token pair `design-v7.md` lists (not the mango colour: T10.AC12 holds) and the others are not; given a keyboard Tab, then each control shows a focus ring.
- **T27.AC8** Given the mouse over a control, then it shows a hover state; given "-", "+" and the arrows, then each has a tooltip.
- **T27.AC5** Given every colour used in the block, then each equals a token value listed in `design-v7.md` (names and hex), and each of those is a value of the light theme file.
- **T27.AC6** Given a Task filter chosen, then a View change, "+", "-" or an arrow, then the filter stays and the timeline reacts as before (T16.AC3, AC4, AC7 hold).
- **T27.AC7** Given the built page, then the block matches `design-v7.md` in its closed and open (Task list open) states.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Fixtures
Fixture squad with a goal and a scope that has tasks 01 to 04 (Work time data, ticket 15).

## Touched files
Set by the Manager: `templates/board/board.css` (the filter block), the Work time panel file only if it needs a class name; test in `tests/test_squadboard_panels.py` (computed style: background not white, padding values, one line at 1440).

## Comments
