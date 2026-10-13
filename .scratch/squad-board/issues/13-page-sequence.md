Status: ready-for-agent
State: ready
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
10. **Text is clipped, never overflows its column**; long task IDs/labels are truncated with `…`.
11. **Baseline AC 1 to 5, 7, 9, 10**; page technical AC 1 to 7.

## Behaviour AC (blackbox)
B1. **One row per event:** the number of rows drawn equals messages + status events + gap rows in the viewed iteration (the mirror's `#rows` count).
B2. **Arrow per message (label `TYPE TASK-ID`):** direction sender → receiver, labelled with its type and task ID, coloured by type: ASK blue, ANSWER light blue, DECISION dark yellow, HANDIN purple, PASS green, FAIL pink, STATUS grey, BLOCKED red.
B3. **A HANDIN → FAIL → HANDIN → PASS loop** is visible as four arrows in four colours on the page fixture's task.
B4. **Activation bars:** start on the message row that woke the agent; a bar without a message is marked with the self-start symbol; the blocked part is hatched red; the end marker shows the duration; an open bar shows a ticking timer (watch it change within 3 s).
B5. **Folded gaps:** a quiet stretch over 3 minutes is one row reading "⋯ N min quiet".
B6. **Task column on the right** is a `TASKS` card grouped by state in the order blocked, building, checking, returned, done; each task shows its ID, the return count, and a highlight at 2 returns.
B7. **New events animate** (an arrow draws in when a new message is appended to the log while the page is open); reload shows it drawn already.
B8. **A 300-row history scrolls smoothly** and the sequence stays aligned with the headers while scrolling.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
