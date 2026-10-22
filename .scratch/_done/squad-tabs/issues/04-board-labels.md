Status: ready-for-agent
Task ID: TAB-04
Blocked by: TAB-01 (branch from TAB-01's passed sha; imports `bin/squadlabel.py` and reads its store)
Files touched: `bin/squad-board`, `bin/squad-board.html`, `tests/test_board_*.py` that assert header or needs-you text (updated), new `tests/test_board_labels.py`, `tests/board_fixture.py` (helper only)
Serves: spec story 8 (D1, B7, B8)

# TAB-04: the board shows the display label

**Done when every agent name the page shows as a name (column header, needs-you item, side panel title, agent list text, hover text) is the display label, while ids, links, roster, notes, messages and the event log keep the address name.**

Read first: TAB-01 (store and module contract), spec story 8, B7, B8. Code: `read_squad`, `make_column`, `build_columns`, `derive_needs_you`, `watched_signature` in `bin/squad-board`; in the page `fitName(... col.agent ...)` (header, around lines 422 and 453), tooltip text (~487), `panelSet(panelName, col.agent)` (~1285), the accessible list (~1486).

## Build
1. **Server.** `read_squad` also reads `<home>/labels/*.json` (match real file names, like the notes files; a file counts only for a roster agent of its home in the per-scope layout) and keeps `role`, `number`, `title` per agent. `make_column` gets a new key **`label`** (string, never empty); `agent` stays the address. `label` = `squadlabel.build_label(role, number, title)` from the store; with no stored entry (older squad, replay, retired agent, agent seen only in a log) it is built from the roster role with no title and a number only when two or more roster rows of that role share the pod, numbered in roster order (B8). A column with no role at all (log-only) shows its address name as today, never an empty header. `derive_needs_you`: `text` uses the label (`🤖 Dev 2 · TAB-04 is blocked`); `agent` and `id` keep the address.
2. **Refresh.** `watched_signature` includes `labels/*.json` of every home, so `squad-board-start`'s open page updates after `squad-label` without a restart (story 8).
3. **Page.** Column header, selected state hover text, needs-you rows and the agent list text use `col.label`; every lookup key (`byAgent`, `data-agent`, `/notes/<agent>`, `selected`) keeps `col.agent`. The side panel shows the label as its title and the address name as a second, smaller line (B7).
4. The label is **text only**: it reaches the DOM with `textContent` / canvas `fillText`, never `innerHTML`, and a label with `<script>` or `"` in the title changes nothing (a title comes from another agent).

## Technical AC
1. `/state` of a squad with stored labels: `columns[i].label` equals `build_label(...)`; `agent` unchanged; two Devs in one pod number `Dev 1`/`Dev 2` from the store.
2. Fallback (B8): a squad without `labels/` (reuse the existing fixtures) gives a label for every column; Manager `🦀 Manager`; two `dev` rows in one pod `🤖 Dev 1`, `🤖 Dev 2`; one `dev` row `🤖 Dev`; a retired agent too; a log-only agent keeps its address; no column has an empty or missing label. Replay mode (`--replay tests/fixtures/board/page`) renders the same way.
3. Needs-you text uses the label; `agent`/`id` keep the address; existing needs-you tests are updated for the text only.
4. Refresh: after rewriting `labels/<agent>.json`, the watched signature changes and the SSE stream delivers a state with the new label (use the existing watcher test pattern in `test_board_live.py`).
5. Layouts: flat and per-scope both work (`make_scoped` helper); `_done` scopes stay hidden; a label file of an agent not on the roster is ignored in the per-scope layout.
6. Page (Playwright in replay mode, one browser session, closed after; `process.md` → Safety): header shows the label; the panel shows the label and the address; selecting a column, jump, notes link and message lines still work by address; a stored title `<img src=x onerror=...>` renders as plain text and runs nothing; a 32-character label with emoji fits its header (`fitName` cut).
6b. **Header cut rule (QA blackbox F1, BA B14, story 8): the header never loses the number or the role word to a plain cut.** `fitName` (or a new `fitLabel` used for `col.label`; address names keep `fitName`) works in this order: (a) the whole label if it fits; (b) the head (everything before ` · `: emoji, role, number) plus as much of the task text as fits, ending in `…`; (c) if even the head plus ` …` does not fit, the head alone with `…` appended (`🤖 Dev 2 …`); (d) only if the head alone is wider than the header, shrink the header font down to a floor (the existing minimum, if any) and only then cut the role word's tail while keeping the number (`🤖 QA Whit… 2`). A label with no ` · ` follows (a), (d). The full label stays in the hover text, the side panel and the accessible list. Test (Playwright, replay, a fixture with real role keys and `labels/*.json` as in QA's run): at the viewport of QA's run and at a narrower one, every header's visible text starts with its head (`🤖 Dev 1`, `🤖 Dev 2`, `🤖 QA Whitebox` or the shrunk form with its number) and no two agents of one pod show the same header text; the pure cut function also has unit-style cases (head fits, head does not fit, no title, 32-char label) run in the page via `page.evaluate`.
7. Existing tests that assert address names in headers or needs-you text are updated deliberately and listed in `dev-evidence.md`; no other behaviour of the page changes.
8. The board stays stdlib-only and starts without network; `bin/squadlabel.py` is found when `squad-board` is run by a symlink or from another cwd (resolve the real path like `squad-spawn` does).
9. Targeted tests pass; full suite once on the final sha and the TZ run (`process.md` → Safety).

## Notes
- Server tests use the board's own fixture helpers; the page tests use replay mode, never a live herdr.
- Do not touch the board's browser "needs you" notification (D14).
