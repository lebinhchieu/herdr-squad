Status: resolved
State: done (PASS at 7f0b436; in squad/dev-board-19 at 927c5a7)
Task ID: BRD-27
Blocked by: none (branch `squad/dev-board-13`, on top of e74e0da)
Files touched: `bin/squad-board.html` (the frame loop only), `tests/test_board_page.py` (IdleLoopTest), `tests/test_board_sequence.py` (one open-bar test)

# BRD-27: the page redraws at ~8 fps while only pulses and timers run, full rate only for real motion

**Done when a headless tab on the default page fixture, with working and blocked agents and nothing changing, uses under 5% of a core over 6 s (about 32% today) and `window.__raf` grows by at most ~12 per second.** Found 2026-10-14 (`iterations/1.md`, CPU investigation): `wantsFrames` returns `headerAnimating(state)` (`bin/squad-board.html:171`), so while any agent works or is blocked the whole canvas is redrawn at 60 fps, forever. A live squad is almost always in that state, so every open board tab burns a core.

## Technical notes
- **Two kinds of frame request**, both in the one loop (`scheduleDraw` / `frame`, lines ~159-173; E16 stays the rule, this refines it):
  - **Motion = full rate (rAF each frame):** an arrow drawing in (`drawIn.size > 0`, 400 ms), plus every single-shot request from an event (state, scroll, resize, hover, panel). Scrolling must stay smooth: the `scroll` listener keeps calling `scheduleDraw()` directly.
  - **Ambient = capped:** the header pulses (`pulse(ts, 240)` and `pulse(ts, 300)`, a ~1.5 to 1.9 s cycle: `sin(ts / period)` is in radians) and the open-bar tip and timer (the `bars.some(b => b.open)` clause at line ~759). Redraw these at most every `AMBIENT_MS = 125` ms (8 fps).
- **Shape:** after `draw`, `frame` asks `scheduleDraw()` if motion, else if ambient and not hidden arms one `setTimeout(AMBIENT_MS)` that then calls `scheduleDraw()`. Keep one timer at most (`ambientTimer`); an event-driven `scheduleDraw()` may draw sooner and the timer still fires once, which is fine. Move the open-bar clause out of `drawSequence` into the `after draw` decision, so drawing code no longer schedules frames. `headerAnimating` stays; it becomes the ambient test (plus the open-bar check).
- **Hidden tab:** `scheduleDraw()` returns at once when `document.hidden`; `frame` arms no ambient timer when hidden; a `visibilitychange` listener calls `scheduleDraw()` when the tab becomes visible, so the page repaints current state straight away and the loop resumes.
- **Tune with data, not by guess:** if 8 fps measures over 5% in the headless run, lower the rate (`AMBIENT_MS` up to 200, 5 fps); the floor is 4 frames per second (the pulse must still look alive). Do not go below that; do not add partial redraws or dirty regions (out of scope).
- No server change, no change to what is drawn, no change to the mirror or hooks. The `window.__raf` wrapper in the tests counts every `requestAnimationFrame` call, so the timer path shows up as one rAF per ambient tick.

## Technical AC
1. **CPU (evidence, not a unit test, a CPU limit would flake on a loaded machine):** run the replay page (`bin/squad-board --replay tests/fixtures/board/page --now <fixed> --port 0`) in one headless Chromium launched by a script you keep out of the repo (put it in `evidence/BRD-27/`), tab visible, nothing changing, 2 working + 1 blocked agents (say which fixture agents these are). Sum `utime+stime` from `/proc/<pid>/stat` of the whole browser process tree (browser, renderer, GPU) at start and after 6 s, wall-clock divided. Record **before** (e74e0da code) and **after**. After < 5% of one core. Stop the browser and the server by PID and show 0 left (`pgrep -f` is not enough; list your own PIDs).
2. **Frame rate (tests):** in `tests/test_board_page.py` `IdleLoopTest`, the three "loop runs" tests measure over 2 s, assert `> 4` frames (the loop is alive) and `<= 26` (the cap holds, about 12/s with load slack). `test_loop_is_idle_on_a_quiet_squad` (`== 0` over 2 s) is unchanged. `test_many_changes_in_one_frame_ask_for_one_frame` (`<= 2`) is unchanged. These replace the `> 5` over 1 s from BRD-17a AC 2b.
3. **Open bar (test):** `tests/test_board_sequence.py::test_the_loop_runs_while_a_bar_is_open` (`> 8` in 1 s, line ~487) becomes `> 2` and `<= 14` in 1 s.
4. **Hidden tab (test):** in `IdleLoopTest`, a working-agent page: `Object.defineProperty(document, 'hidden', {value: true, configurable: true})` plus `visibilityState`, dispatch `visibilitychange`, wait 500 ms, then `__raf` over 1.5 s grows by 0 (the loop is idle while hidden, even though an agent works). Set `hidden` to false and dispatch again: within 1 s `__raf` has grown (loop resumed) and the canvas shows the current state (read a pixel of the working dot as the existing `LookTest` does, no need for a new helper).
5. **Motion not capped (test):** an arrow drawing in still uses rAF at full rate. Reuse the existing draw-in tests (`test_board_sequence.py`, "the loop stops after the draw-in" and the `DRAW_IN_JS` ones) unchanged: they must pass as they are. Add no new frame-count threshold for the draw-in (headless software painting is too slow to assert 60 fps without flaking); the code check is that the draw-in branch calls `scheduleDraw()` and not the timer.
6. Existing tests that read pulses (`test_board_page.py` ~1015: the ring changes over 8 samples 250 ms apart) must pass unchanged.
7. **Suite:** green once by default under the lock (`flock /tmp/squad-suite.lock nice -n 10 python3 -m unittest discover -s tests`); BRD-17's own two-run rule (default + TZ) is the final check, do not add a run for this ticket. Python 3.9-safe, no `.pyc` committed, touch only the listed files.

## Delivery
- One commit on `squad/dev-board-13`, message `BRD-27: ...`, so `git show` reviews it on its own. BRD-17's HANDIN then names that final sha and lists BRD-27 as included. Evidence in `evidence/BRD-27/` (the CPU table before/after, the script, PIDs closed). Reviewers: qaw-board (code, tests), qab-board (page still pulses and arrows still draw in; one screenshot).
- Rough size: about 20 lines of page code, 4 test edits, 1 new test, one measurement. Under an hour.

## Comments
- 2026-10-14 tech-board: written from the CPU investigation. The pulse cycle is 1.5 to 1.9 s (`ts / period` in radians), so 8 fps is smooth. 60 fps to 8 fps should take the measured ~32% to about 4-5%; the AC allows dropping to 5 fps if the data says so.
