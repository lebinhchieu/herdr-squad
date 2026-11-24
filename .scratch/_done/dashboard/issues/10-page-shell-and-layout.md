# 10 page shell and layout
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 1
Blocked by: 09
Feature: 1, 15, tz, cross-cutting, LF (`tasks/features.md`)

## What the PO gets
The page frame: header, panels that fit, drag/hide/resize, font size, time zone, refresh.

## Rules
- Light Mango Parrot palette (values from the light theme file); mango only on needs-you things (count, banner, chip, ready-to-merge). **No `%` character anywhere in visible text.**
- Header: choice, switcher, zone offset (e.g. "+07"), "updated hh:mm:ss" (browser zone), font size control: three steps named **Small / Normal / Extra large**, default Normal.
- Tab title: `(N) <squad>` when N > 0, else `<squad>`; N = the squad-wide needs-you count.
- Refresh every **5 s**. "not updating" after 3 failed refreshes. A missing source shows "unknown: <source>".
- Age words (G8, used by every panel): `under 1 min ago`, `N min ago`, `N h ago`, `N d ago`; never "just now" for unknown.
- Times: one function, browser zone; data stays UTC; zone unreadable = "UTC"; ages do not depend on the zone.
- Layout engine: drag, hide (list of hidden panels), resize, Reset layout; the permission banner cannot be hidden or dragged. **Fit rule** (gutter 12 px, the Designer may change it): a panel is as tall as its content up to a maximum, then scrolls inside; the grid packs tight. No column picker (cut).
- Window: at 1000 px wide nothing overlaps or is cut off; below it the page scrolls sideways.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T10.AC1** Given the PO moves a panel and resizes another, when reloaded, then both stay (and on another port, see ticket 09).
- **T10.AC2** Given the PO hides a panel, then it returns from the hidden list; the permission banner has no hide control and cannot be dragged away. Given Reset layout, then the default layout returns.
- **T10.AC3** LF1. Given the default layout at 1440 x 900 on the fixture, then no panel body has an empty band larger than 16 px under its last row, unless the PO resized it.
- **T10.AC4** LF2. Given any two neighbouring panels, or a panel and the page edge, then the gap is the same gutter (12 px) and no empty grid cell wider than the gutter sits beside a panel in a row.
- **T10.AC5** LF3. Given a short panel (e.g. Files, 1 row) next to a taller one (8 rows), then the short one leaves no blank grid space and the panels below move up.
- **T10.AC6** LF4. Given the PO hides a panel, then the others move up to close the gap; given he shows it again, it returns without overlapping.
- **T10.AC7** LF5. Given the PO drags a panel to a new place and resizes one, then after drop there is no overlap and no new dead gap, and both stay after reload.
- **T10.AC8** LF6. Given a panel whose content is longer than its height, then it scrolls inside; nothing is clipped without a scrollbar.
- **T10.AC9** LF7. Given Small, Normal and Extra large font, and a 1000 px wide window, then LF1 to LF6 still hold.
- **T10.AC10** Given "Extra large", when reloaded, then it stays; no text is cut off (a small panel scrolls); no horizontal scroll in picker rows; no text is cut in chips.
- **T10.AC11** Given every panel and state of the fixture, then no `%` character appears in the visible text (font size names included).
- **T10.AC12** Given every state of the fixture, then the mango colour appears only on needs-you things.
- **T10.AC13** Given needs-you N = 3, then the tab title is "(3) <squad>"; given 0, then "<squad>".
- **T10.AC14** Given the browser at +07 and ts `2026-11-03T02:00:00Z`, then the page shows 09:00 and the header "+07". Given ts `23:30Z` at +07, then the next local day shows. Given zone Asia/Kolkata, then "+05:30". Given the zone is unreadable, then "UTC".
- **T10.AC15** Given a time 3 h ago, then "3 h ago" in any zone; given 20 s, "under 1 min ago"; given 3 days, "3 d ago".
- **T10.AC16** Given the server stops, then within 15 s the header says "not updating"; given it restarts, then within 5 s the header returns to "updated hh:mm:ss".
- **T10.AC17** Given a missing source in the fixture, then "unknown: <source>" and never an empty panel that looks fine.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M12.
- New: `templates/board/index.html`, `board.css`, `board.js`, `layout.js` (pure `layout.pack`, drag, resize, fit).
- Edit: none. Panels register themselves in a list in `board.js` so later tickets add a file, not an edit.
- Tests (new): `tests/test_squadboard_page.py` (browser: PO's short-next-to-tall case at 3 font sizes, 1/3/8-row panels, no dead gap) and a plain test for `layout.pack`.
- Design: `ui-design/design-v5.md` (must read `Status: final` before this ticket starts).

## Comments
