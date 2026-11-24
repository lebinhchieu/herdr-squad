# Evidence 39: demo file click opens nothing

## Behaviour
In `squad-board --demo` a click on a file or folder link opens nothing and shows one toast `Demo: sample file, not opened`. One capture handler (`demoGuard`) stops the event before any panel handler, for left, Ctrl, Shift, middle click and Enter. The server also refuses `POST /api/open` in the demo (403 `disabled in the demo`). The real board is unchanged: no toast, the click still calls `openFile`. Proof is the browser run `tests/demo_click_browser.js` (driven by the demo test) and the server test. No screenshots: the toast is asserted by computed values.

## AC table
| Item | Claim | Proof |
|---|---|---|
| T39.AC1 | left click on markdown, HTML and ticket rows and the Tasks Where link: no /api/open, no vscode: navigation, no popup, toast | templates/board/board.js:295-301 (demoGuard); tests/test_squadboard_demo.py::Browser::test_T39_TA2_TA3_TA5_demo_click_opens_nothing_and_shows_one_toast |
| T39.AC2 | folder rows the same | same test, kind `folder` (count asserted >= 1) |
| T39.AC3 | Ctrl, Shift, middle click, Enter the same | board.js:940 (click + auxclick, capture); same test, 5 inputs x 3 kinds, set compared |
| T39.AC4 | toast text, tokens, inside window, apart from DEMO strip and top bar, 300 ms / 2 s / gone by 6 s, one after 3 clicks, nothing moved | board.js:288-294; templates/board/board.css:22-23; same test, windows 1440x900, 1000x700, 1000x700 Extra large |
| T39.AC5 | no `Sent to VS Code:` line; Copy path no toast, no request | same test (`sent` false; copy count 0, see gap 2) |
| T39.AC6 | demo refuses POST /api/open, code never called | bin/squadboard_open.py:104-105; tests/test_squadboard_open.py::test_T39_TA1_demo_refuses_open |
| T39.AC7 | real board: click still calls openFile, no toast | tests/test_squadboard_open.py:226 (`.toast` null, Page34 whole file green) |
| T39.AC8 | demo sealed: hash of real files equal after the click session | tests/test_squadboard_demo.py:427 (`real_hashes`) |
| T39.TA1 | server refusal, demo and not demo | tests/test_squadboard_open.py::test_T39_TA1_demo_refuses_open (l.145) |
| T39.TA2 | one guard, 5 inputs x 3 kinds, spies on fetch/XHR/open, popup/nav/request lists empty, count >= 1 | tests/test_squadboard_demo.py::Browser::test_T39_TA2_TA3_TA5_demo_click_opens_nothing_and_shows_one_toast |
| T39.TA3 | toast: one element, role, token colours, timing, rect, layout equal, no Sent line | same test (l.388-425) |
| T39.TA4 | real board unchanged | tests/test_squadboard_open.py:226; test_squadboard_open.py whole: 7 OK |
| T39.TA5 | demo sealed | tests/test_squadboard_demo.py:427; test_squadboard_demo.py whole: 13 OK |
| T39.TA6 | no other client change | `git diff --stat 06d3a77..58ae10b 8199b5b`: bin/squadboard_open.py, board.css, board.js, the 3 test files + tests/demo_click_browser.js. panel_files.js, panel_tasks.js untouched |
| T39.TA7 | pins | test_squadboard_open (7 OK), test_squadboard_demo (13 OK), test_squadboard_panels (58, 1 fail: known T12), test_squad_evidence (46 OK, run from tests/) |
| T39.TAx | every AC row has a named test, counts asserted | see TA2 (counts and the case set) and TA3 (window sizes asserted) |

## Known / open gaps
- TA3 toast checks run in `tests/demo_click_browser.js` (Node + Playwright) at 1440x900, 1000x700 and 1000x700 Extra large; the Python test reads its JSON.
- The `Copy path` button is never shown in the demo (it lives in the status line, which never shows); the test asserts count 0, so AC5 "Copy path" is covered by absence, not by a click.
- The top bar is not sticky; "no overlap" is a rectangle test only.
- test_T12 `1 d ago` in test_squadboard_panels.py fails on main too: not this ticket.
