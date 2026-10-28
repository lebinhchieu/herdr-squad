Status: resolved
State: done (PASS qaw-board; in squad/dev-board-19 at 927c5a7, PO-merge candidate)
Task ID: BRD-19
Blocked by: 17 (branch from BRD-17's passed sha; it touches the recorder of BRD-10 and the notes route of BRD-15)
Files touched: `bin/squad-board` (sections: squad reader, log reader, columns, needs-you, http watcher, recorder, notes route; `build_state` one call), `tests/board_fixture.py` (new helper `make_scoped`), `tests/test_board_layout.py` (new)

# BRD-19: the board reads both squad layouts (flat and per-scope)

**Done when `squad-board` pointed at a per-scope squad (`scopes/<s>/`, `goals/<g>/`) serves the same `/state` shape as for a flat squad, with each open scope as a pod, and every flat test still passes unchanged.**

Read first: design.md "Iteration 3: layout adapter" (L1 to L14, binding), the plugin's `CONTEXT.md`, `templates/scope/`, `templates/goal/`, `bin/squad-start`, `bin/squad-close`, `bin/squad-log-message`. The layout of a per-scope squad:
```
<squad>/scopes/<s>/{scope.md, roster.md, escalations.md, iterations/<n>.md, roles/, messages.jsonl, activity.jsonl}
<squad>/goals/<g>/{goal.md, roster.md, escalations.md, roles/, messages.jsonl, shared/}   (goal Manager; no iterations/)
<squad>/scopes/_done/  <squad>/goals/_done/     closed: never read
```

## Build
1. **Home list** (`find_homes`, L1, L2) and one place that decides the layout. Flat = one home (the squad folder). Everything below loops over homes.
2. **`read_squad`** (L3, L4, L9, L10): roster rows from every home with `scope` rewritten to the pod (L3) and a `home` key; `scopes` from each `scope.md` `size:` line; escalation rows with their home; `iterations` as the union, plus per-home iteration texts for the Manager-idle check; `notes` as agent → path relative to the squad folder.
3. **`read_logs`** (L7) over all homes; `build_state` retags records (L8) in the per-scope layout only, before the timeline.
4. **`build_columns`** unknown-agent rule (L6); **`derive_needs_you`** (L9, per Manager); **`watched_signature`** (L12).
5. **Recorder** (L13) writes into the agent's home; **notes route** (L10) resolves through the roster row's home. Both are built in BRD-10 and BRD-15: change only their path lookup.
6. A shared helper `make_scoped` in `tests/board_fixture.py` builds a per-scope squad in a temp dir (goal with two scopes, a lone scope, a `_done` scope that must stay hidden).

## Merge seams with BRD-28 and BRD-29 (tech-board, 2026-10-14; BRD-19 builds from e77b69d in parallel with BRD-29)

**Rule: BRD-19 changes where records are read from and written to, never what a status means.** BRD-28 is already in the base; BRD-29 (dev-board-13, branch `squad/dev-board-13`) lands later and you merge it in before your final suite run, keeping both behaviours. Line numbers are of dev-board-13's working tree today and will move; names are what count.
1. **Recorder, one path lookup.** `Recorder.log_path` (set in `__init__`) is used in exactly two places: `sync` (`last_statuses(self.log_path)`) and `append` (the `os.open` of the log). Replace those two uses only: `append(name, status, detail=None)` keeps its signature (BRD-29 calls it with a third argument, from `handle` and `poll`) and opens `self.home_log(name)` = `<home of the agent's roster row>/activity.jsonl`; `sync` reads `last` by merging `last_statuses` of every home's log (agent names are unique across homes). Do **not** touch `handle`, `poll`, `poll_loop`, `background_of`, `last_recorded` or the `waiting`-vs-`idle` clause in `sync` (BRD-29's). `rostered(name)` already goes through `read_squad`, so it sees every home once `read_squad` does; an agent in no roster stays unrecorded (L13). The `done`-on-missing-pane loop at the end of `sync` (BRD-28) uses the merged `last`: keep it, and keep its "snapshot listed at least one agent" guard.
2. **`build_state`.** The `live_agents` set (`roster_live(r["status"])` over `squad["roster"]`, BRD-28) is passed to `derive_timeline`: with your `read_squad` the roster is all homes, so leave that line as it is. The goal Manager's row counts as live; an agent that only joins by name (L6, pod `(unlisted)`) is **not** live, so its bar closes at its last event (BRD-28 AC (iv)). Add the L8 retag between `read_logs` and `derive_timeline`; the `columns`/`derive_timeline`/`derive_tasks` calls keep their arguments.
3. **Timeline.** `TimelineBuilder`, `finish_bar`, `derive_timeline` are not yours: BRD-28 and BRD-29 own them, retagging happens on the records before they run.
4. **State keys (BRD-29 adds them).** The shape test (AC 12) must allow `agents[name].waiting_s`, a `waiting` list on each bar (segments with `start_row`, `end_row`, `start_ts`, `end_ts`, `duration_s`, `detail`) and `detail` on a status row; keep the allowed-key list in one constant of the test so the merge adds the keys in one place. `column.status` may be `waiting`.
5. **`derive_needs_you`.** You rewrite it per Manager (L9). Keep `manager_col["status"] == "idle"` as it is (a `waiting` Manager is not idle, nothing to add), and change nothing else in the Manager-idle rule.
6. **Tests.** `tests/test_board_layout.py` and the `make_scoped` helper are new files: no overlap. `tests/test_board_recorder.py`, `test_board_state.py` are edited by BRD-28 (already in your base) and BRD-29 (later): add your recorder test (AC 11) in `test_board_layout.py`, not in those files, so the merge is clean.
7. **After the merge,** one full run (the receipt) on the merged tree; if a BRD-29 fixture (`tests/fixtures/board/waiting`, `panes/`) breaks on a key you added, fix it in the merge commit and say so in `dev-evidence.md`.

## Technical AC (BRD-19)
1. **Flat regression:** the whole existing suite passes with no test edited (except where a test builds the flat fixture through a function you moved, and then only that call). Nothing in a flat `/state` changes: same keys, same ids, same text.
2. **Detect:** a folder with `scopes/` is per-scope even if a stale `roster.md` sits at its root (the root file is ignored); without `scopes/` it is flat. An empty `scopes/` gives a valid empty state (200, empty lists, `iteration` null).
3. **Pods:** fixture goal `g` (goal Manager, scopes `a` and `b`), lone scope `c` with its Manager: `/state` pods are `all` (size null, the goal Manager and `c`'s Manager first, in home order), then `a`, `b`, `c` with sizes from each `scope.md` (`size: S + QA whitebox (x)` → `S + QA whitebox`; empty `size:` → null). The goal Manager's roster row has an **empty Scope cell** and still gets a column. A coach row in a goal roster lands in the pod named after the goal.
4. **Hidden:** `scopes/_done/x/` and `goals/_done/y/` with rosters, messages and escalations that must not appear anywhere in `/state`. A folder named `Bad_Name`, a plain file in `scopes/`, a symlinked scope folder → ignored, no error.
5. **Merged logs:** messages from three homes appear in time order in `rows` with the right `from` and `to`; one `msg_id` in two homes shows once; an agent that exists in no roster joins by name: `x-dev-my-scope-1` → pod `my-scope` (scope slug with a dash), `x-dev-b` → `b`, a name that fits no pod → `(unlisted)`; ambiguity rule L6 has its own tests: with pods `a` and `a-b`, `x-a-b-1` → `a-b` (same position, longest wins) and `x-b-a-1` → `b` (earlier position wins over `a`).
7. **Needs-you:** two scopes both with an unanswered row `#1` give two items with different ids and the scope in the text; an answered row in one scope does not clear the other. An idle Manager of scope `c` whose own check-in is empty gives `manager_idle:c:<n>`; the goal Manager gives none; a blocked agent in any scope is listed.
8. **Iterations (L8):** scope `a` has iterations 1 and 2, scope `b` has 1, goal `g` has none. `iterations` = [1, 2], `iteration` 2. Default view: `a`'s iteration-2 records, `b`'s iteration-1 records and the goal Manager's records are all in `rows`; `a`'s iteration-1 records are not. `?iteration=1`: `a`'s and `b`'s iteration-1 records and the goal records; none of `a`'s iteration-2. `?iteration=3` → 400. Column totals stay whole-run. Build the expected rows by hand.
9. **Notes:** `notes_path` is `scopes/c/roles/<agent>.notes.md` for a scope agent and `goals/g/roles/...` for the goal Manager; null when the file is missing. (Route tests belong to BRD-15's file; add one test that a scoped agent's notes are served, and that a notes file under another home is not reachable through a name in the wrong home.)
10. **Watch:** with an open `/events` stream, creating `scopes/d/` with a roster, and moving `scopes/c` into `scopes/_done/`, each produce a new event whose `pods` change. An edit to a `scope.md` size produces one too.
11. **Recorder:** with the fake herdr, an agent of scope `a` gets its record in `scopes/a/activity.jsonl` with `a`'s highest iteration number as the tag, the goal Manager's in `goals/g/activity.jsonl` with a null tag, an agent in no roster in no file, and nothing in the squad root.
12. **Shape:** a test walks the whole per-scope `/state` and fails on any key outside the design.md key list or on the string `home` as a key anywhere (the home tag stays inside the server).
13. **Robust:** a home with no roster, an unreadable `scope.md`, a scope folder that vanishes between listing and reading (simulate by patching nothing: remove it between two requests) → 200, no traceback.
14. **Security:** no path is built from request data; folder names come from a listing filtered by the regex above, agent names for notes from the roster. A roster agent named `../x` in a scope roster is never used in a path.
15. **Baseline AC 1 to 5, 7, 9, 10** from design.md. Python 3.9-safe. Touch only the listed files.
16. **Suite receipt (process.md Safety):** run the full suite once under the flock lock (default) and save `evidence/BRD-19/suite-default.txt`; then run the time-handling test files (timeline, state, tokens, recorder, plus any test file the ticket touches) once under `TZ=America/New_York LC_ALL=C` and save `evidence/BRD-19/suite-tz.txt`. Each file has the first line `sha <rev> clean=yes|no` and the tail `Ran N tests ... OK`. QA whitebox checks the receipt and runs only targeted tests.

### QA whitebox additions (qaw-board)

(qaw-board adds points here.)

## Comments
