# Evidence 30: a file click opens VS Code

## Behaviour
- `templates/board/panel_files.js`: `BOARD.vscodeUrl(abs, distro)` is the one link function (`vscode://file/<abs>`, or `vscode://vscode-remote/wsl+<distro>/<abs>` when `data.wsl_distro` is set; each segment encoded). Every row of the Files panel is a link (no `target`, `rel=noopener noreferrer`, tooltip `<abs> — opens in VS Code`). The new-tab and markdown-window code is deleted (`openMarkdown`, `_blank`, `root.open`). A click sets a `role=status` line `Sent to VS Code: <abs>` with `Copy path`, kept 8 s (`BOARD.filesStatusMs`) and redrawn if the panel redraws. Folder rows (the `folders` list of ticket 29) come first, name in bold with the absolute path under it. Empty note: `No other files yet. Artifacts, reports and evidence appear here.`
- `bin/squadboard_files.py`: rows carry `abs`; a symlink pointing outside the allow-list is kept as a row `{kind: other, abs: null, blocked: true, what: "cannot be opened: outside the squad folders"}` (the target path is never given); data gets `wsl_distro`.
- `templates/board/panel_tasks.js`: the file name in the Where cell is a link through `BOARD.vscodeUrl`.
- **Deviation:** `bin/squadboard_tasks.py` also returns `wsl_distro` (one line) because the Tasks panel needs the distro for the link and `/api/tasks` did not carry it.
- Tests run: `test_squadboard_files.py` 13, `test_squadboard_panels.py` 52, `test_squadboard_tasks.py` 16, `test_squadboard_page.py` 22, `test_squadboard_server.py` 18, `test_windows_safe.py`, `test_old_language_inventory.py`: all OK, none skipped.
- Tests changed on purpose: `test_squadboard_panels.py` `test_T14_AC1_AC2_TA3...` (was `_blank` + `/api/file`, now `vscode://`, no target); `test_squadboard_files.py` symlink-out test (blocked row kept) and `ROW` (adds `abs`).
- Not tested here: opening VS Code (QA blackbox by hand); live headless `--dump-dom` with `WSL_DISTRO_NAME` set/unset (QA whitebox, TA10).

## AC table
| AC | Where shown |
|---|---|
| T30.AC1, AC2, AC10 | `vscodeUrl` + `fileRow` in `panel_files.js`; `test_T14_AC1_AC2_TA3...`, `test_T30_TA2_no_new_tab_code...` |
| T30.AC3, AC13 | `fileRow` (folder: bold name link + `.fpath` line); `test_T30_AC3_AC7_AC9...` |
| T30.AC4 | `panel_tasks.js` Where cell; `test_T30_TA11_AC4...` |
| T30.AC5 | `test_T30_TA1_AC5_url_function_table` |
| T30.AC6 | same test (Debian form) and `wsl_distro` in the data; PO agreed O1 (E11) |
| T30.AC7 | `squadboard_files.py` `add` (blocked row), `fileRow` (muted, no link); `test_T14_TA1_goal...` and `test_T30_AC3_AC7...` |
| T30.AC8 | no new route; no write added |
| T30.AC9 | link `title`; `test_T30_AC3_AC7_AC9...` |
| T30.AC11, AC12 | `sent`, `showStatus`, `copyPath` (status line in the Files panel only); `test_T30_AC3_AC7_AC9...` (status text, Copy path clipboard, gone after the timer) |
| T30.TA4 | `test_T30_...` blocked row name `<img onerror=x>` shown as text |
