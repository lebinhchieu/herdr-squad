# Evidence 11 page picker and views

## Behaviour
Code sha `1ec200c`. New `templates/board/panel_scopes.js` (picker, header context line, switcher sheet, opening order, "Scopes of this goal" panel). Run on the ticket-02 fixture through a real squadboard server (routes of 04).

| Screen | Shot |
|---|---|
| Picker: Open rows (needs-you first), Done (20) collapsed, search, no task/inbox/work-time panel | ![picker](img/picker.png) |
| Search with no match: `Nothing matches 'xyz'` | ![nomatch](img/nomatch.png) |
| `#/scope/nope`: picker with "scope nope not found" | ![notfound](img/notfound.png) |
| Goal view: Scopes strip (brief, stage, needs you, blocked, tasks x of y, last active) | ![goal](img/goal.png) |
| Click a scope in the strip: `goal alpha > scope alpha-api`, link up | ![scope in goal](img/scope-in-goal.png) |
| Lone scope: "(no goal)", "1 more needs you in questions" | ![scope no goal](img/scope-no-goal.png) |
| Closed scope: read-only "closed", link to picker | ![closed](img/closed.png) |
| Switcher sheet (Esc closes) | ![switcher](img/switcher.png) |

- Opening order flag > URL > saved choice > picker (T11.AC7-AC11) is the pure `BOARD.openingOrder`; saved/URL names are checked against the picker lists, else `/api/squads?check=NAME`. Names never reach `innerHTML` (`#/scope/<img onerror>` shows "not found", `window.__x` stays undefined).
- Back returns to the picker: a user choice does `history.pushState('#/scope/S')`; a refresh never pushes (test: 3 ticks, `history.length` unchanged).
- Chosen scope closes while open: the page shows "closed: read-only. Back to the picker", no error.
- Picker row build: one DocumentFragment per list, under 300 ms measured in the harness.
- Stage column = row `status` (open/done): the API has no separate stage field.

## Tests
- New `tests/test_squadboard_panels.py` (Pure, Picker, Opening, Header, ByView, Static): 18 tests, named by AC id.
- Re-ran ticket 10's `tests/test_squadboard_page.py` after the board.js edit (DECISION 11): pass. One assertion changed there: the template file list now includes `panel_scopes.js`.
- Together 39 tests pass. Also pass: test_windows_safe, test_no_bare_bash, test_old_language_inventory, test_squadboard_list.
- TC.11 grep `grep -rl 'templates/board\|board\.js\|index\.html\|panel_scopes' tests/` hits: test_squadboard_page.py, test_squadboard_panels.py (both run), test_squadreport_rollup_ui.py, test_squadreport_rollup.py (run, pass; they match `index.html` of the report, not the board).

## board.js hunks (all approved: DECISION 11 and FINAL 11)
`BOARD.hooks` object; `#view` slot; canvas hidden with no choice; `hooks.paint`; `hooks.data` call in onOk; `hooks.flags` + `d.initial || flags()` (data.initial is gone since 04); `hooks.boot` in boot() (old first-scope fallback kept when no hook); `BOARD.ctx`; byView: renderPop filter, snapshot, resetLayout.
Touched files added by approval: `templates/board/index.html` (one script line), `tests/test_squadboard_page.py` (one assertion).

## Notes for the QAs and tickets 12/19
- The needs-you total in the picker and the tab title bridge is a client sum of open-row `needs_you` (hooks.data sets `S.needs` only when no server count is there). When 05's `count_squad` exists, board.js `needsFrom` overrides it: ticket 12/19 wires it.
- "N more need you in X" is per row from the picker rows (05's `others` will replace it).
- Static literal: one `<style id=view-css>` block in `panel_scopes.js` (tokens as `var(--x)`, no data).
- Not built, by decision: Sort segment, "Expand all" (not in AC or design-v5 scope of 11).
- Scratch: none left in /tmp (browser sessions closed, the two live servers stopped).
