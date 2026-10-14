Status: resolved
State: done (PASS; in the iteration-2 line merged at 7f0b436)
Task ID: BRD-13
Blocked by: 12
Files touched: `bin/squad-board.html` (sections `sequence`, `tasks`, and the matching parts of `mirror`, `layout` row geometry only)

# BRD-13: page sequence: rows, arrows, activation bars, folded gaps, task column

**Done when the page draws every row of `/state` as the live sequence diagram, with arrows, activation bars and the task column, matching the spec and the round 6 prototype.**

Read first: design-iteration-2.md (E12, E13, E15 to E17, E19, E20), spec user stories 18 to 32, 41 to 44, "Derivation rules" bar rules and the prototype block, the round 6 prototype look. Replace only the `sequence` and `tasks` sections and their mirror parts.

## Technical AC (BRD-13)
1. **Only rows in view are drawn** (E15): 300 and 5,000-row fixtures scroll smoothly; the draw call count per frame is bounded by the visible rows (Developer shows frame time in evidence at 5,000 rows built by a temporary larger fixture, not committed).
2. **Row geometry:** row `i` at `i * ROW_H` (`ROW_H = 30`); a bar spans `start_row` to `end_row` (open → to the last row, with a live timer); a blocked segment spans its rows with a hatch pattern in blocked red.
3. **Self-start** mark `⟲` at the bar start when `self_start` is true; the duration label sits at the bar end marker; an open bar's timer ticks each second (E19) without a state refresh.
4. **Arrow:** from the sender's column to the receiver's on the message row, arrowhead at the receiver, label `TYPE TASK-ID` (or `TYPE`, or `msg`), colour per spec palette and E12. A message to or from an agent with a collapsed stub column still draws to the stub.
5. **New arrows draw themselves in** (about 400 ms) only for rows that arrive after the first render; reloading does not replay the animation. The animation stops the draw loop when done (E16).
6. **Gap row** draws one thin row "⋯ N min quiet" across the width; `seconds` under 60 shows "⋯ N s quiet".
7. **Task column** (E13, E26): a card headed `TASKS`, grouped blocked, building, checking, returned, done (empty groups omitted), inside a group by first appearance, each task a chip with a coloured left edge, `↺N` chip, mango highlight at `returns >= 2`.
8. **Mirror** (E17) lists rows, bars, tasks exactly as in `/state`, same order and hooks.
9. **Look (E26):** bars 14 px wide with teal tint and border, blocked hatch, pulsing end dot and `⏱ time` pill on an open bar; status rows carry a diamond marker plus the status word (`idle · 4m 05s` at a bar end); arrows 2.2 px with a filled head and a pill label; matches the round 6 prototype side by side (Developer attaches a screenshot of both).
10. **Text never leaves the board and is cut with `…`** (tech-board ruling 2026-10-13): arrow labels and status text are centred on their arrow span or bar end as in round 6, may be drawn over neighbour rails, are at most 3 columns wide, and are cut with `…` at the left board edge and at the TASKS card; task chips and chip text are cut inside the TASKS card. Rows never show text over another row's text.
11. **Baseline AC 1 to 5, 7, 9, 10**; page technical AC 1 to 7.

## Behaviour AC (blackbox)
B1. **One row per event:** the number of rows drawn equals messages + status events + gap rows in the viewed iteration (the mirror's `#rows` count).
B2. **Arrow per message (label `TYPE TASK-ID`):** direction sender → receiver, labelled with its type and task ID, coloured by type: ASK blue, ANSWER light blue, DECISION dark yellow, HANDIN purple, PASS green, FAIL pink, STATUS grey, BLOCKED red.
B3. **A HANDIN → FAIL → HANDIN → PASS loop** is visible as four arrows (three colours: HANDIN purple twice, FAIL pink, PASS green) on the page fixture's task.
B4. **Activation bars:** start on the message row that woke the agent; a bar without a message is marked with the self-start symbol; the blocked part is hatched red; the end marker shows the duration; an open bar shows a ticking timer (watch it change within 3 s).
B5. **Folded gaps:** a quiet stretch over 3 minutes is one row reading "⋯ N min quiet".
B6. **Task column on the right** is a `TASKS` card grouped by state in the order blocked, building, checking, returned, done; each task shows its ID, the return count, and a highlight at 2 returns.
B7. **New events animate** (an arrow draws in when a new message is appended to the log while the page is open); reload shows it drawn already.
B8. **A 300-row history scrolls smoothly** and the sequence stays aligned with the headers while scrolling.

### QA whitebox additions (qaw-board)

Checked by running the Developer's tests plus my own scratch checks; a point I cannot run is a FAIL with the reason. Applies on top of the BRD-12 Q-points (palette, E18, E10, no external URL on the changed page).
- **Q1 Scope:** diff touches only `bin/squad-board.html`, only the `sequence`, `tasks`, matching `mirror` parts and `layout` row geometry; the other section markers and stubs are unchanged (diff the marker lines). No server change.
- **Q2 No stubs left** in `sequence` and `tasks`; every function the BRD-12 stubs named keeps its signature.
- **Q3 Mirror equals `/state`:** I compare `#rows`, `#bars`, `#tasks` in Playwright with my own reading of `/state` (count, order, every `data-*`), on the page fixture, not on the Developer's expectations. Gap rows read `⋯ N min quiet` (and `⋯ N s quiet` under 60 s); self-start bar marked `⟲`; task text `ID state ↺N`.
- **Q4 Colours:** arrow colours per type and E12 (BLOCKED red, untyped muted `msg`), task states per E13; `returns >= 2` gets the mango chip, 1 does not. I read the colour from the page source map or the pixel at a known arrow point, one per type.
- **Q5 Windowing:** only rows in view are drawn: count draw calls (or `fillText` via a canvas-context spy in an init script) at 300 rows and at a temporary 5,000-row fixture; the count does not grow with total rows. Scroll to the last row and to the middle: first/last drawn row is right, no off-by-one at `i * 30`.
- **Q6 Open bar:** the timer ticks without a `/state` refresh (count `/state` requests while it ticks); offset uses `state.now` vs the browser clock (E19), so with replay `--now` fixed it still reads a sensible positive duration and not `NaN` or a negative.
- **Q7 Animation:** an arrow appended while the page is open draws in (~400 ms), reload and the first render do not animate; after it ends the rAF loop idles (count 0 over 5 s). A message to or from a stub column (retired agent) still draws.
- **Q8 Hostile text** in a message label, agent name or task id (`<img src=x onerror=alert(1)>`, `<b>x</b>`) stays text on the canvas and in the mirror; no dialog, no `img` in the DOM. A very long task id is truncated with `…` and stays inside its column (canvas text measured, not clipped by luck).
- **Q9 Edges:** zero rows, one row, a bar with `end_row` null, `start_row == end_row`, a blocked segment at the first/last row, an agent not in the columns list: no exception in the console (I check `console` errors in Playwright) and no NaN coordinates.
- **Q10 Alignment:** sequence columns line up with the header cards at 1280, 1600, 1920 and DPR 2 while scrolling (compare column x from the layout function with header x).
- **Q11 Evidence:** screenshot of the page next to the round 6 prototype exists (AC 9); frame-time numbers at 5,000 rows exist (AC 1).
- **Q12 AC wording (sent to tech-board):** B3 says a HANDIN → FAIL → HANDIN → PASS loop shows "four arrows in four colours", but HANDIN is the same purple twice, so there are three colours. I test it as four arrows, three colours, unless tech-board changes the wording.

## Comments
- 2026-10-13 tech-board on dev-board-13's four format asks: 1 to 3 accepted as proposed (gap `Math.round(s/60)` min 1, `⋯ N s quiet` under 60; mirror row text `TYPE TASK-ID from → to`, untyped `msg from → to`, all six `data-*` ('' when null), extra `data-agent` on status rows and `data-seconds` on gap rows; bars `data-end-row` '' when open, `data-blocked-segments` count, mirror text `⟲ 4m 05s` / `4m 05s` / `⏱ 9m 05s` fixed at state receipt, while the canvas timer ticks); 4 ruled as AC 10 above. Q8 "inside its column" reads "inside the board area / TASKS card" for arrow labels.

### tech-board, after qab PASS at d848b6d
- Observation 3 (⟲ glyph drawn over an arrow start when the sender's bar starts on that row) and observation 2 (13 live columns widen the page 58 px at 1280) are not BRD-13 failures. Neither blocks. Both go on the iteration-3 live-run watch list; if the live run shows either, they become follow-up tickets (3: draw the glyph left of the arrow start; 2: decide what the page does above 12 live columns, a design question for E20a).
