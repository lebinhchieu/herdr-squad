# Dashboard design v4

Status: draft (nothing final; the PO picks). Author: board-ux-dashboard. Base: v3 (`design-v3.md`, `proto-v3.html` unchanged). Input: `tasks/po-feedback-v3.md` (5 points).
Files (open over `http://127.0.0.1:<port>`): `proto-v4.html` (the board; demo bar on top is not part of the design), `proto-timeline-1.html`, `-2.html`, `-3.html` (Work time alone, same fake data). Screenshots `img/v4-*.png`. Sources and `build.py` are in `_src/`.

## The 5 PO points
| # | Solved by |
|---|---|
| 1 chip text low | One chip style: `inline-flex`, `align-items:center`, `line-height 1`, fixed height. Count, filter chip, recommend mark, source dot, zone and warning use it too. A long text ellipsises with a tooltip. Measured on pixels with Segoe UI loaded (ink gap above vs below, the PO's chips "accepted" and "decided in shared/decisions.md"): at most 1 px at Normal and Extra large, 1 px at Small too (`img/v4-chips-po-*.png`). |
| 2 always select | No "all" anywhere. Nothing selected = the picker only. Selected = ONE goal (its scopes together, scope is a chip/column) or ONE scope. See Picker. |
| 3 timeline | Three prototypes below. v4 uses option 1 in Work time. Zoom, idle compression, x-axis in local time, sticky task filter: in all three. |
| 4 useful data | Not a UI decision: BA owns it (value of each item, what to ignore). Panels are modules, so a cut is cheap. |
| 5 data and effort | Not a UI decision: Architect owns it (what data exists, effort). Same module rule. |

## Picker flow
- Open: `--scope X` or `--goal Y` opens it directly and wins. Else the selection remembered for this squad (in `board-ui.json`, version 4, with the recent list). Else the picker. A flag or memory that names a missing item opens the picker with a note (`img/v4-picker-badflag.png`).
- Picker screen (`v4-picker*.png`): search by name and brief (`/` focuses it), sort (last active, needs you, name), Recent (4), Open (goals and loose scopes), Done (collapsed). A goal row has a chevron that shows its scopes; the row opens the goal. Each row: status, work counts, needs-you chip, last active (age and time). Needs-you counts cover the whole squad: they are the reason to pick one. Banner and tab title still ignore the selection (Manager decision).
- Header selector (`v4-combobox*.png`): one button, ARIA combobox. Search, arrows, Enter, Esc; groups Recent, Open (goal with its open scopes), Done; footer "Open the picker". In a scope the header shows "in goal X" as a link back to the goal.
- Needs you panel: items of other goals and scopes become buttons "E8 · board-cli" that switch the selection (replaces "Show all").
- Scale proof: 8 goals, 25 scopes (one very long name, 2 loose, 1 goal with 4 scopes, 1 with 3), 20 of them with generated tasks, agents, branches and questions.
- States: empty squad, opening, unknown sources (names show, counts say "unknown"), search with no match, bad flag, first time.

## Goals and Scopes panels: decision
- The Goals panel goes: the picker is the goal list.
- The Scopes panel becomes "Scopes of this goal", shown only while a goal is selected: status, open tasks, needs you, last active; a row click narrows to that scope. With a scope selected it is hidden and the header line carries the goal link, brief, team, iteration.
- Why: a list of all scopes on the page is the thing the PO rejected; a goal's own scopes are few (2 to 8) and are the natural next click.

## Three timelines
| | 1 Swimlanes (Gantt) | 2 One row per task | 3 Overview + detail |
|---|---|---|---|
| Rows | agents, grouped Manager, Developers, QA | tasks, grouped by scope | agent bands, plus "working at once" |
| Colour | state | agent; state by pattern | state |
| Best for | who did what, when; who waits on whom | how a task went (dev, QA FAIL, dev, PASS); branch and worktree on the row | many days; where was the busy time |
| Cost | many rows with 10+ agents | agent identity needs a legend | most chrome; the strip is real-time, the detail collapsed |
- Shared: local-zone axis with a day row (date breaks), drag on the axis to zoom, Ctrl+wheel or pinch, +/- and arrows, drag the chart to pan, presets 1 h / Today / 3 days / All, sticky task filter, block click opens detail (task, worktree, branch, commits, artifacts, reports), "approx" marks as in v3.
- Idle compression: a gap where no agent works or waits, longer than N minutes (control, default 60; 15 min to 4 h), becomes a fixed-width hatched break labelled "night · 14 h 40 min", "weekend · 2 d 7 h" or "idle · 1 h 08 min". "Show real time" turns it off. Waiting or blocked blocks (also on you) never collapse: a night spent waiting on you stays visible. Break labels use real elapsed time; checked in Bangkok, Kolkata and New York (DST change inside the weekend).
- Recommendation: option 1 as the Work time panel (it is in v4); add option 2 as a second tab "by task" if the PO asks "how did task 03 go". Option 3's strip only pays off for ranges of a week or more.

## Modules
Each panel is one `PANELS.x` block plus one `COLDEF.x` block in `proto-v4.html`; to cut a panel delete both and its name in `ORDER` and `DEF`. Work time is a separate engine (`TLE`) that needs only a list of lanes and blocks. The Developer needs from the data: per agent, blocks with start, end, state and task; commits, verdicts, artifacts with time; worktree and branch per agent (new fields from the transcript reader; effort is the Architect's).

## Open points
1. The "approx" task label needs the data answer of point 5; if it is cut, blocks lose their label and keep colour.
2. A goal with 8+ scopes: the Scopes panel scrolls; no grouping by status yet.
3. Narrow screens (under about 1000 px) hide the brief column only; the board itself is still not designed for them.
4. Wheel: on the three standalone pages the plain wheel over the chart zooms. In the board panel only Ctrl+wheel and pinch zoom, so the page can still scroll. The PO may prefer the same in both.
