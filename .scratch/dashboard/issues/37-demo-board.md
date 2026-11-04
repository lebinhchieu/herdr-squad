# 37 Demo board
Duties: plan-owner=manager, design-notes=tech-lead, tech-ac=tech-lead+qa-white, business-ac=ba, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=ba, choice-owner=architect. Also conform to `architecture.md` (Status: final). Hand in to BOTH QAs (whitebox, blackbox); never self-merge. QA checks related tickets together (PO wish).
Design: the demo label is the only new screen element. The Designer places it in `ui-design/design-v8.md` (or a short note to the Manager if v8 is final first); light Mango Parrot colours only.
Status: ready-for-agent
Iteration: 3
Blocked by: BA AC (this file). No other ticket (runs in parallel with the design).
Feature: PO iteration 3, request 3 (`tasks/po-request-iter3.md`)

## What the PO gets
`squad-board --demo` opens a board full of sample data: every panel has content, the page says it is a demo, and nothing of his real squads is read or changed. He can judge the board without a real, recent squad.

## What the fixture has today (BA check, 2026-11-04)
The committed fixture (`tests/fixtures/board`, see `FIXTURE-STEPS.md`) is built for tests, not for a full page:
- Goal `alpha` (4 scopes) has no open question, no messages, no tickets and no transcripts: its Needs you, Tasks, Agents now and Work time would be empty.
- The task stages (todo to done), the open question E1 and the transcripts live in lone scopes (`checkout`, `questions`).
So "every panel full on one page" is false with the copy as it is. The Tech Lead extends the **demo copy** (or the shared fixture if its goldens allow) so the rules below hold. Which extra content goes where is the Tech Lead's call.

## Rules
- **Start.** `squad-board --demo` (with `--port N` and `--no-open` as today) copies the full fixture to a new temporary folder with message times shifted to now (`board_fixtures.py --now`), starts the board on that copy, and prints one line saying it is the demo and where the copy is. It starts from any folder, also one with no squad. Exit codes of today stay (1 port busy). `--demo` with `--squad`, `--goal` or `--scope` is refused with exit 2 and a message (the demo has its own data). A start that ends with exit 1 or 2 leaves no temporary folder.
- **First page.** The demo opens on a view where every panel has content: Needs you, Tasks, Agents now, Files, Scopes of this goal, Work time. That is a goal view (the Scopes panel exists only there). The picker still lists goals and scopes (and the second squad `other`); a scope view (`checkout`) shows the five scope panels with content. "Content" = at least one real row or entry, never an empty-state sentence.
- **Content.** "Has content" = at least one real row or entry, and no panel shows the text it shows on the empty board (QA blackbox compares with each panel's empty-board texts). Needs you: at least one open question and one blocked agent. Tasks: tasks in every stage the Tasks panel names (the stage words as the board shows them), in the scope view of `checkout`; the goal view shows at least 3 tasks. Agents now: agents in working, idle and blocked states. Files: rows of every kind (file, folder, ticket, markdown, HTML). Work time: transcripts with a working time, a night gap and a DST gap. Scopes of this goal: the four scopes of `alpha`.
- **Labelled demo.** The page shows a label that cannot be hidden, at the top, in every view: `DEMO · sample data, not your squads`; the tab title starts with `[demo]`. It does not overlap or push out the permission banner, the picker or the top bar.
- **No real data.** The demo reads no real squad folder, no real `.scratch`, no `~/.claude*` transcripts and no live `herdr`: Agents now reads the recorded herdr file of the copy and makes no `herdr` call; Work time reads the copy's Claude config folder. The demo ignores the `HOME` and `CLAUDE_CONFIG_DIR` locations of the environment. It writes nothing outside its temporary folder. The saved layout (`board-ui.json`) goes into the copy: the PO's real layout is not touched.
- **Fresh each time.** Every start copies the fixture again: a layout saved in a previous demo is gone. The temporary copy is deleted when the demo stops (Ctrl+C or `kill` of its PID).
- **Same board.** The demo is the same page and server as the real board; only the data differs. A file click works as in tickets 30 and 34 on the copy's files (the copy has no VS Code window with that project, so VS Code shows the file in its last active window).
- **Read-only** rules of the board stay (T03.AC11) inside the copy.
- Ages read as recent (fixture clock = now): "40 min", not "years".

## Business AC (one Given / When / Then each; a FAIL names one id). Window: 1440 x 900, Normal text, unless said (SQ-7).
- **T37.AC1** Rule: start. Given `squad-board --demo --no-open --port N` from a repo that has a real squad, and from a folder that has no squad, then the board answers on 127.0.0.1:N and one line of the output says it is the demo; given a busy port, then exit code 1; given `--demo --scope checkout`, `--demo --goal alpha` or `--demo --squad X`, then exit 2 with a message and nothing started; after exit 1 or 2 no temporary folder is left.
- **T37.AC2** Rule: every panel has content, goal view at 1440 x 900. Given the first page of the demo, then Needs you, Tasks, Agents now, Files, Scopes of this goal and Work time are all shown (none hidden), and each has at least one row or entry and none shows its empty-board text.
- **T37.AC3** Rule: every panel has content, scope view. Given the demo's scope `checkout` at 1440 x 900, then the five scope panels (Needs you, Tasks, Agents now, Files, Work time) each have at least one row or entry and none shows its empty-board text.
- **T37.AC4** Rule: task stages. Given the demo's scope `checkout`, then the Tasks panel shows at least one task in each stage the board names (todo, in progress, returned, blocked, checking, ready for review, sha changed after PASS, merged, done: QA compares the words with the Tasks panel's own stage words).
- **T37.AC5** Rule: states. Given the demo, then Needs you lists an open question and a blocked agent, and Agents now shows at least one working, one idle and one blocked agent; Work time shows at least one working time with a night gap (11 h or more) and one across the DST change.
- **T37.AC6** Rule: label at 1000, 1440 and 1920 px wide, the place and look of the design section the Designer names for the label (`design-v8` s??, light theme colours; QA blackbox owns the colour check). Given any view of the demo (goal, scope, each picker choice), then the label `DEMO · sample data, not your squads` is visible at 1000, 1440 and 1920 px (Normal text) and at Extra large text near 1000 px; it has no hide or close control; the tab title starts with `[demo]`; it overlaps nothing (T10 rule) and the permission banner (when shown) is still above the panels.
- **T37.AC7** Rule: no real data. Given a real scratch squad with a unique name (`REALSQUAD-<random>`) with a question, a message and a ticket in the repo the demo is started from, a fake `HOME` and a fake `CLAUDE_CONFIG_DIR` (both set) whose `.claude/projects/...` holds a transcript with the same unique name, and a stub `herdr` on PATH that logs its calls, then that name appears nowhere on any page, panel, picker choice or API answer of the demo, and the `herdr` log has no call.
- **T37.AC8** Rule: nothing real is changed. Given the same real scratch squad with its own `board-ui.json`, when a demo session ran (picker clicks, a layout change, hide, a file click, Reset layout) and was stopped, then the hash of every file under the real squad folder, the real `.scratch` and the real config folder is the same as before, including the real `board-ui.json`.
- **T37.AC9** Rule: fresh each time. Given a demo where the PO hid a panel and changed the layout, when he stops the demo and starts it again, then every panel is shown and the layout is the default.
- **T37.AC10** Rule: clean stop. Given a running demo, when its process gets SIGINT (Ctrl+C) or SIGTERM (`kill` of its PID), then the temporary folder named in the output is gone and the port is free (`kill -9` is out of scope).
- **T37.AC11** Rule: recent ages. Given the demo started now, then the task checking (stage `checking`, waiting on QA blackbox) reads about 40 min in the demo, and no age in the page is in days or years except the `_done` scopes.
- **T37.AC12** Rule: same page, at 1000, 1440 and 1920 px wide. Given the demo, then these checks give the same results as on the real board: T35.AC1, AC2, AC5, AC6a-d, T36.AC2a (when built), the picker, Panels list, Reset layout, Fit, and a T34 stub call on a click of a copy file (QA blackbox runs them against the demo).

## Agreement (REV-8)
BA: written 2026-11-04. QA blackbox review applied 2026-11-04 (37-M1..M4, S1-S5). QA blackbox: pending final confirmation (AC6 waits for the label design section)

## Fixtures
The demo copy: `tests/fixtures/board` extended by the Tech Lead as above. For AC7/AC8 QA blackbox builds the real scratch squad and the fake config folder itself.

## Touched files
Tech Lead (`tasks/issues-tech/37.md`; the Manager's plan decides): expected `bin/squad-board`, `bin/squadboard.py` (the flag), `tests/board_fixtures.py`, the fixture, the label in `templates/board/` (not `layout.js`/`board.css` while 35/36 run: the Tech Lead picks a file that is free, or the label waits).

## Comments
- BA 2026-11-04: the opening view is a goal view because "Scopes of this goal" shows only there. If the Tech Lead prefers to open on a scope view, a goal view must still show all six panels with content (AC2).
- BA 2026-11-04: `--demo` with `--squad/--goal/--scope` is refused: my choice, simple and safe.
