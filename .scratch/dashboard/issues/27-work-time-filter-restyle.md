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
- Light Mango Parrot tokens only (design-v7 s4; names there, hex in `templates/board/board.css`): block `--panel2`, border 1 px `--border`, radius 8 px; chips `--bg`, `--border`, text `--ink`, labels `--muted`. **The active choice (chosen task, chosen view, `Show real time` on) is a mango chip: background `--t-need`, border `--mango`, text `--ink`, bold** (PO/Manager decision on design-v7 open point 1; it is a stated exception to T10.AC12, which now reads "mango only for needs-you things and the active choice of the Work time filter"). Hover: border `--ink`. No pure white (#FFFFFF), no dark background, no new colour.
- Padding inside the block at least 8 px on every side (design: .75em = 9 px at Normal, never under 8); the text of a label or chip is at least 6 px from its own border; chips are 8 px apart. **Two rows, each on one line at 1440 px** (the Work time panel column is about 700 px wide): the Task row (label + chips) and the View row (label + chips, then the `-` `+` and arrow buttons), then a range line (range, gap select, `Show real time`). The two rows are not merged onto one line. At 1000 px and at "Extra large" a row wraps onto a second line (never overlaps, never cut; a wrapped row hangs under its chips, not under its label).
- The block stays at the top of the panel body while the lanes scroll (sticky, opaque background).
- A visible focus ring on every control (keyboard use); the buttons have a hover state; "-" and "+" and the arrows keep their tooltips.
- No `%` character.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T27.AC1** Given the Work time panel at 1440 x 900, then the filter block's computed background equals `--panel2` and its border is 1 px `--border` (token names in `design-v7.md` s4; hex = the value in the light theme file `templates/board/board.css`; none is #FFFFFF).
- **T27.AC2** Given the filter block, then the space between its edge and its first control is at least 8 px on all four sides, and the space between any label or button text and that control's own border is at least 6 px.
- **T27.AC3** Given the filter block at 1440 px on the fixture (tasks 01 to 04), then the Task row is on one line (label, All tasks, 01 to 04, unattributed) and the View row is on one line (label, Last 1 h, Today, 3 days, All, then `-`, `+`, and the earlier / later arrows, in that order), chips and buttons 8 px (within 1 px) apart; the two rows are separate lines (design-v7 s4: a column is about 700 px wide). Given 1000 px wide and given "Extra large", then there is no overlap and no cut text, and a row uses a second line only when its controls do not fit on one.
- **T27.AC4** Given the active choice (the chosen task, the chosen view, and `Show real time` when on), then it is a mango chip: computed background `--t-need`, border `--mango`, text `--ink`, bold; the other chips are `--bg` / `--border` / `--ink` and not bold; given a keyboard Tab, then each control shows a 2 px `--ink` focus ring.
- **T27.AC8** Given the mouse over a chip or a button, then its border turns `--ink` (hover state); given "-", "+" and the arrows, then each has a tooltip (Zoom out, Zoom in, Earlier, Later).
- **T27.AC5** Given every colour used in the block, then it is one of the tokens named in `design-v7.md` s4 (`--panel2`, `--border`, `--bg`, `--ink`, `--muted`, `--t-need`, `--mango`, `--err`), and the computed value equals that token's value in the light theme file.
- **T27.AC6** Given a Task filter chosen, then a View change, "+", "-" or an arrow, then the filter stays and the timeline reacts as before (T16.AC3, AC4, AC7 hold).
- **T27.AC7** Given the built page, then the block matches `design-v7.md` s4 in each state it lists: normal; loading (range adds `· loading`); error (adds `· could not load this range` in `--err`); no tasks (only All tasks and unattributed); many tasks (chips wrap, label column stays); active choice; hover; focus; Extra large; 1000 px wide.
- **T27.AC9** Given the Work time lanes scrolled down, then the filter block stays at the top of the panel body and the lanes do not show through it (opaque).
- **T27.AC10** Given the text `%` anywhere in the block, then none is found.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: agreed (PASS AC 25-30, 2026-11-04; `tasks/business-ac-agreement.md`).

## Fixtures
Fixture squad with a goal and a scope that has tasks 01 to 04 (Work time data, ticket 15).

## Touched files
Tech Lead (`tasks/issues-tech/27.md`): `templates/board/timeline.js` only (its CSS is in that file, not board.css); test in `tests/test_squadboard_panels.py` (computed style: background not white, padding values, one line at 1440).

## Comments
