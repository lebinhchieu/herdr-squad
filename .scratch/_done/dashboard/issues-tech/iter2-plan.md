# Iteration 2: Tech Lead plan notes (board-tl-dashboard, 2026-11-04)
Per-ticket design notes + technical AC: `25.md` .. `31.md` here. Common AC still apply: `COMMON.md` (TC.*) and `UI-COMMON.md` (TU.*). Business AC are the BA's (`tasks/issues/NN-*.md`); nothing here rewrites them. Ids: `T<NN>.TA<k>`.

## Touched files, checked against the code (LC-9). Two corrections to the plan table in `iterations/2.md`
| # | Touches (edit) | Tests (extend, no new file unless said) | Correction to the plan |
|---|---|---|---|
| 28 | `bin/squadtickets.py`, `bin/squadboard_tasks.py`, `bin/squadboard_list.py` (its `_tickets`), `templates/board/panel_tasks.js` | `test_squadtickets.py`, `test_squadboard_tasks.py`, `test_squadboard_list.py`, `test_squadreport_tasks.py` (one fixture line: `tickets: feat`), `test_squadboard_panels.py` (Tasks part) | adds `squadboard_list.py`: it has a third copy of the ticket-folder guess |
| 29 | `bin/squadboard_files.py` | `test_squadboard_files.py` | none |
| 30 | `templates/board/panel_files.js`, `bin/squadboard_files.py` (row gets `abs`, data gets `wsl_distro`) | `test_squadboard_panels.py` (Files part, line ~674 pins `_blank`), `test_squadboard_files.py` | **not `board.js`**: the click code is in `panel_files.js`. Also edits `squadboard_files.py`, so it runs after 29 (same Dev) |
| 25 | `templates/board/board.js` (`togglePop`, `renderPop`), `templates/board/board.css` (`.pop`) | `test_squadboard_page.py` or `test_squadboard_panels.py` (whichever holds the header tests) | none |
| 26 | `templates/board/layout.js` (`pack`, `autoPlan`, drag), `board.js` (pass `col`), `board.css`, **`bin/squadboard_ui.py`** (the server drops unknown panel keys: `col` must be allowed) | `test_squadboard_page.py` (layout.pack tests live there), `test_squadboard_ui.py` | test file is `test_squadboard_page.py`; adds `squadboard_ui.py` (no other ticket touches it) |
| 27 | `templates/board/timeline.js` **only** (its filter CSS is the `CSS` array at line ~542, not `board.css`) | `test_squadboard_timeline.py` | **not `board.css`**: so 27 never touches 25's or 26's files |
| 31 | `.claude-plugin/plugin.json`, docs named in `promote.md` | `test_promotion_0_6_0.py` must pass (accepts a patch bump) | none |

## Parallel, and who holds what
- `board.js`/`board.css` are touched only by 25 and 26: one Dev, 25 then 26 (26 waits for design-v7 final anyway).
- 28 (tasks, bin + panel_tasks.js), 29→30 (files, bin + panel_files.js), 27 (timeline.js) share no file with each other or with 25/26. **Three Devs can run at once:** Dev A = 28 (then 27 when design is final), Dev B = 29 then 30, Dev C = 25 then 26. No two parallel tickets touch the same file.
- Shared test file risk: `test_squadboard_panels.py` is extended by 28 (Tasks tests) and 30 (Files tests) in parallel. Different test methods, but the same file: merge conflicts are likely. Rule for both: add new tests in a new class at the END of the file, one blank-line separated; the Dev who merges second rebases. (Or the Manager serialises 28/30 on it: not needed for code.)

## QA batching (PO: related tickets checked together)
- **Pass 1, data: 28 + 29**, one session, one scratch squad built from the real layout of `accounts/cswitch-bg` (the live-data check, REV-5b) plus the dashboard scope.
- **Pass 2, UI: 25 + 26 + 27 + 30** in one browser session on the integration sha (a merge of the four passed branches), at the three text sizes. Each ticket still gets its own `PASS <NN>` on its own final sha (REV-3); the batch saves sessions, not verdicts.
- 31 last, by QA whitebox: diff is `plugin.json` + docs only.
- Full suite: me, once, on the integration sha with `--tz`, after both passes (SUITE-3).

## Risk flags (risk-owner = me)
1. **28 is the risky one.** It changes three call sites and a report helper (see 28.md). Visible effects for the PO: report titles for scopes without a ticket folder. Mitigation: one function, one test table of layouts.
2. **30 opens `vscode://`.** A browser cannot tell whether VS Code exists: if it does not, the click does nothing. Needs one visible hint (T30.TA5). Absolute paths enter `/api/files` rows: local only (127.0.0.1, Host check), acceptable, listed in the ADR note.
3. **26 rewrites the packing rule** that ticket 10/16/20 tests pin (no dead gap, 3 font sizes, saved order). Saved `board-ui.json` layouts (`order`, `span`) must still load (additive only, version unchanged).
4. **Test pins that will change on purpose:** `test_squadboard_panels.py` ~674 (`_blank`), `test_squadtickets.py` token-favour cases, `test_squadboard_tasks.py` "equal to list" case. The Dev lists each changed test in HANDIN (TC.6: none newly skipped).
