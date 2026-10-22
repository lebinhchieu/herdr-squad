Status: resolved
State: PASS 2026-10-13 at be6e604 (qaw-board, qab-board)
Task ID: BRD-17a
Blocked by: 13 (QA whitebox PASS and QA blackbox PASS); 15 only if it has passed by then
Files touched: `bin/squad-board`, `bin/squad-board.html` (merge-conflict resolution only), tests only where a merge forces a fixture change

# BRD-17a: early integration, a usable live board for the PO

**Done when one branch holds BRD-12, 13, 10, 18, 08 (and 15 if passed), the full suite is green, `bin/squad-board` run live against this squad folder serves the page with rows, arrows, bars, tasks and needs-you, and a replay screenshot is saved.** Tokens show "—" until BRD-11, no follow or picker until 14, no alerts until 16: expected.

Built by dev-board-13 (knows the page), on its own branch after its BRD-13 PASS. A subset of BRD-17; BRD-17 later merges what is left (11, 14, 16, and 15 if it was not in) on top of this branch's passed sha.

## Build
1. Merge into the Developer's own branch: BRD-12 (abc9e99, its base), BRD-13, BRD-10 (4d4a782), BRD-18 (e9ca502), BRD-08 (5fe6881), and BRD-15 only if it has a PASS. On conflict keep both sides and change no logic (a bug goes back to the owner through tech-board).
2. **The `live` key, minimal (BRD-17 AC 0 in full stays with BRD-17):** BRD-10 sets `live` true in `handle_state`, BRD-12 sets `live` false in `build_state`. Resolve so that `build_state` takes a `live` argument and `handle_state` passes it; no second assignment. The page must see `live: true` in live mode.
2b. **Load-sensitive frame tests (BRD-12 file, caught by dev-board-15 at 19 frames under load):** in `tests/test_board_page.py` `IdleLoopTest`, the three `assertGreater(self.frames_over(1), 20)` checks (`test_loop_runs_while_something_pulses`, `..._for_a_working_agent_alone`, `..._for_a_waiting_item_alone`) become `> 5`. The point of them is "the loop runs", the idle test (`== 0`) keeps the other side. No other change.
3. Full suite green three times, once under `TZ=Asia/Ho_Chi_Minh LC_ALL=C`; no leaked `squad-board` process (`pgrep`).
4. **One live run:** from the squad folder's environment run `bin/squad-board` with no `--replay` (needs `$SQUAD_DIR` and the herdr socket). Open the printed `http://127.0.0.1:<port>/?token=...` with `playwright-cli` and check: header cards for the roster, message rows with arrows, a bar per working agent, TASKS card, no console error. Save one screenshot at 1600 px and the page's `GET /state` first 40 lines. Do not edit `activity.jsonl` or roster files by hand.
5. One replay screenshot of `tests/fixtures/board/page` at 1600 px (same as BRD-12 evidence).
6. `dev-evidence.md` lists the merged shas and anything that did not work live, with the output.

## Not in this ticket
BRD-11 tokens, 14 follow and picker, 16 alerts, BRD-17's exact-count / fixture-stderr / screenshot-set ACs, BRD-21.

## What the PO opens
Run in a terminal inside this squad's herdr env: `cd` to the 17a worktree (`.worktrees/dev-board-13`) and `SQUAD_DIR=/home/chieule/workspace/squad/.claude/squads/squad-board bin/squad-board`, then open the printed URL (it ends in `?token=...`; a page without the token cannot Jump). Honest limits: arrows and the needs-you/tasks cards show history at once, because they come from the message log and roster. **Bars only start growing from the moment the recorder first runs**, because `activity.jsonl` does not exist for the past; leave it running to see them fill. Token columns read "—".

## Done = QA whitebox PASS (diff, suite, the live-run evidence) and QA blackbox PASS (replay mode only: the live run is the Developer's evidence).

## Comments

### 2026-10-13, tech-board (from qab-board's note on BRD-16)
Not a 17a item: 17a is a merge with no logic change. On a fixture copy where retired `dev-shop-0` still gets messages, 13 full columns give `scrollWidth` 1338 at 1280 px and the TASKS card covers the last column (the pristine fixture collapses it and fits). The scroll itself is by design (E20, above 12 columns); the cover is the defect. Ticket `26-page-many-columns.md`, droppable, after 17. If the 17a live run at 1600 px shows a covered column, note it in `dev-evidence.md`, do not fix it.
