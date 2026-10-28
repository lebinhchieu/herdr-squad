Status: resolved
State: done (PASS at 7f0b436; in squad/dev-board-19 at 927c5a7)
Task ID: BRD-17
Blocked by: none (17a passed at be6e604; 11 cdb0fa4, 14 c853113, 16 340bf9e passed; 15 09cf802 if missing from 17a)
Files touched: `bin/squad-board`, `bin/squad-board.html` (merge-conflict resolution only), `tests/test_board_integration2.py` (new, only if the coverage check finds a gap)

# BRD-17: integrate iteration 2 and screenshot pass

**Done when one branch holds every passed iteration 2 branch, the whole suite is green, no stub or dead code is left in the server or the page, and the Playwright screenshot set of the merged page is saved.**

Read first: BRD-09 (this ticket repeats it for iteration 2), design-iteration-2.md. Built by a Developer who wrote none of the merged tickets, on a branch from BRD-09's passed sha. **Also merge BRD-08's passed branch** (demo fixture); BRD-12 adds the `live` key to `/state`, so update `tests/fixtures/board/demo/expected-state.json` (add `"live": false`) and check by hand that nothing else in it changes. Edit only that key.

## Build
1. Branch from BRD-17a's passed sha (it holds 08, 10, 12, 13, 18 and maybe 15) and merge the remaining passed `squad/dev-board-*` branches: BRD-11, 14, 16 and 15 if missing; on conflict keep both sides and change no logic (a bug goes back to the owner through tech-board).
2. Full suite, three runs, once under `TZ=Asia/Ho_Chi_Minh LC_ALL=C`; no leaked `squad-board` or stub processes (`pgrep`).
3. Clean-up check by grep and by reading both files: no stub bodies, no `501`, no TODO, no unused function or constant, all imports in the top block, markers intact and ordered.
4. **Coverage table** in `dev-evidence.md`: every iteration 2 behaviour AC (BRD-12 to 16, B-numbers) and technical rule has a test or a named screenshot; gaps get a Seam A test.
5. **Screenshots** with the `playwright-cli` skill on `tests/fixtures/board/page` in replay mode, at 1280, 1600 and 1920 px: initial view, scrolled history, paused with ↓ live, replayed iteration, side panel open, blocked header, needs-you with 3 items, narrow stub, hostile-text row. Saved to `$SQUAD_DIR/evidence/BRD-17/`.

## Technical AC (BRD-17)
00. **Exact return counts in the page tests:** BRD-12's page fixture test asserts `returns >= 2` only, because BRD-18 was not merged on its branch; tighten it to the exact value (2) and check the done task stays done.
0. **`live` key (BRD-10 and BRD-12):** BRD-10 sets `live` true in the live branch of `handle_state`; BRD-12 adds `live` false in `build_state`. After the merge, `build_state` takes a `live` argument and `handle_state` passes it; no second assignment remains. BRD-11's `stamp_live` is the one place that sets live `now`/`live` for `/state` and `/events`; fold it into the `build_state(live)` call on both paths and test that `/state` and the first `/events` frame have the same `live` value in both modes.
00b. **Fixture stderr (from BRD-10):** `tests/board_fixture.py` `Server.stderr()` seeks the shared child stderr file to 0, so a poll while the child writes makes the child overwrite earlier lines. Fix it there (read with `os.pread` on the fd, or open the file in append mode) and let `launch()` in `test_board_recorder.py` use the shared helper again; add one test that two polls during a write lose no line.
1. **Merge:** all passed branches are in the history; no history rewrite; nothing pushed.
2. **Suite** green three times; stable under the odd TZ and locale; no leaked process.
3. **No leftovers:** grep output in `dev-evidence.md`; Python 3.9 read (`ast.parse(feature_version=(3, 9))`) of `bin/squad-board`.
4. **Page rules:** the Seam A page tests of BRD-12 pass on the merged page: no external URL, no forbidden construct, palette-only hex, CSP.
5. **Coverage table complete;** screenshots exist at all three widths and show no clipped or overlapping text.
6. **Live smoke in a fake world:** start live mode against the fake herdr and a temp squad folder, append a message and a status change, and show `/state`, the first `/events` frame and the page text mirror changing (output in the evidence).
7. **Diff hygiene:** only files the merged tickets list, plus the optional test; no `__pycache__`, no conflict markers.
8. **Baseline AC 1 to 5, 7, 9, 10** from design.md.
9. **Top-right strip (from qaw-board's BRD-16 PASS):** BRD-16's `#alerts-button` (right 258 px, width 112, top 22) overlaps BRD-14's `#bar-controls` (right 140 px, picker 100 px plus live button). After the merge the two sit side by side with no intersecting bounding boxes at 1280, 1600 and 1920 px, with the alerts button left of the controls, and neither covers a header card or the needs-you card. This is the one allowed CSS/position edit in `bin/squad-board.html`; change offsets only, no logic. One Playwright check (bounding boxes) in the evidence and one Seam A test if the page tests can assert the offsets.

## Behaviour AC (blackbox)
This ticket is the run QA blackbox performs end to end: on the merged build in replay mode with the page fixture, every B-point of BRD-12 to BRD-16 holds. QA blackbox signs off from the browser only.

**Follow re-check (qab-board, BRD-14 PASS c853113):** BRD-14's follow was checked by scroll position only, because BRD-13's rows were not on its branch. BRD-14 merges in BRD-17, not 17a, so qab-board re-checks on the BRD-17 build that new rows become visible while following, and that scrolling up pauses it.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
