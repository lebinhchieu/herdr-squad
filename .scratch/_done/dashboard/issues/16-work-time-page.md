# 16 work time page
Duties: plan-owner=manager, design-notes=dev, tech-ac=qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=qa-white, promote-owner=qa-white, risk-owner=manager, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge.
Design: ui-design/design-v5.md (start only when it reads `Status: final`). AC added: built UI matches the design: every screen and state (QA blackbox checks it).
Status: ready-for-agent
Iteration: 2
Blocked by: 15, 10
Feature: 10 (`tasks/features.md`)

## What the PO gets
Swimlanes: one lane per agent, time on the x-axis.

## Rules
- Timeline option 1 (swimlanes). One lane per agent; blocks coloured by state with a legend (working, waiting, blocked, idle); a block click or hover shows task, start, end in local time. Marks (hand-in, FAIL, PASS, BLOCKED, commit, merge) each with a legend entry.
- Controls: presets 1 h / Today / 3 days / All; drag on the axis zooms; Ctrl+wheel (and pinch) zooms; **the plain wheel scrolls the page** (default; the PO may change); axis has a date row and local-zone times. Idle break control (default 60 min, 15 min to 4 h): a longer gap becomes a hatched break labelled "night · 14 h 40 min", "weekend · ..." or "idle · ..."; "Show real time" turns it off; waiting and blocked blocks never collapse. The task filter stays while zooming.

## Business AC (one Given / When / Then each; a FAIL names one id)
- **T16.AC1** Given a Developer on task 03 for 2 h, then a block for 03 in that agent's lane, with a state colour from the legend; a click shows task, start and end in local time.
- **T16.AC2** Given unattributed time, then a row shows its share in hours and minutes; "approx" is on every task block and on no commit or hand-in mark.
- **T16.AC3** Given a preset (1 h / Today / 3 days / All), then the axis shows that range with a date row and local-zone times.
- **T16.AC4** Given a drag on the axis, then it zooms to that range; given Ctrl+wheel, it zooms; given the plain wheel, the page scrolls.
- **T16.AC5** Given a night gap longer than the break setting, then a hatched break labelled "night · <duration>" shows; given "Show real time", it is gone.
- **T16.AC6** Given a night spent waiting on the PO, then that block is not collapsed.
- **T16.AC7** Given a task filter and then a zoom, then the filter stays.
- **T16.AC8** Given the idle break set to 15 min and to 4 h, then the break appears at each limit.
- **T16.AC9** Given a gap across a DST change, then the label shows real elapsed time.
- **T16.AC10** Given no transcript, then "no transcript" in that agent's lane.

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox: pending confirmation (`tasks/business-ac-agreement.md`).

## Touched files
Module M14 (iteration 2).
- New: `templates/board/timeline.js`.
- Edit: `templates/board/board.js` (register the Work time view).
- Tests (new): `tests/test_squadboard_timeline.py`.
- Design: the PO's pick, timeline option 1 (swimlanes): `ui-design/proto-timeline-1.html` and `design-v5.md`.

## Comments
