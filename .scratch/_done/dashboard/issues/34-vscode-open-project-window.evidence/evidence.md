# 34 evidence (board-dev-open-35)

PO answer: YES to `POST /api/open` (E14 a; D7 final). Code commit: b72bf19.

## Behaviour
A plain left click on a file, ticket or Where link calls `POST /api/open?squad=<key>` (body `{path}`, header `X-Board-Token`). The server runs `code --goto <abs>` (argv list, 5 s). On `ok:true` the link is not followed. On any failure (no VS Code, exit 1, refusal text with exit 0, timeout, no token) the page clicks the same `vscode://` link once. Folder rows, Ctrl/Shift/Alt click, middle and right click never call the route.

## AC table
| Row | Shown by |
|---|---|
| T34.AC1-AC2 (file, ticket, Where call; folder none) | panel_files.js `openFile`, panel_tasks.js `.wf a`; test_squadboard_open.py::Page34::test_T34_TA4_click_posts_once_and_falls_back_only_on_failure (file, folder, ctrl, middle) |
| T34.AC3-AC4 (path intact, no folder arg) | Route::test_T34_TA2_gate (log lines `--goto`, path, `--end`) |
| T34.AC5 (ctrl/middle none) | Page34 test above |
| T34.AC6 (gate a-f) | Route::test_T34_TA2_gate; AC6(d) foreign Origin: bin/squadboard.py `_origin_ok`/`_mutating`, Route::test_T34_TA8_foreign_origin_refused_before_the_route |
| T34.AC7 (20 clicks, hashes) | Route::test_T34_TA3_no_file_written (5 rounds) |
| T34.AC8 (layout unchanged) | not separately tested; the click only adds the status line as in 30. Open gap |
| T34.AC9a-d | OpenFile::test_T34_TA1 (nothing, exit 1, refusal text); Page34 fallback; timeout case in TA1. Open gap: AC9c page-side 5.8 s timer has no test |
| T34.AC15 (folder) | Page34 test (no POST) |
| T34.AC10-AC14 | PO live: **pending** (real windows) |
| T34.TA1 (9 cases) | test_squadboard_open.py::OpenFile::test_T34_TA1_pick_and_judge_table |
| T34.TA2 (gate, methods, unknown squad, 429) | Route::test_T34_TA2_gate, Route::test_T34_TA2_refusal_and_exit_code_give_ok_false_and_one_at_a_time |
| T34.TA3 | Route::test_T34_TA3_no_file_written; only `subprocess` is in squadboard_open.py |
| T34.TA4 | Page34 test; `<img onerror>` text pin: old test Panels30 still passes |
| T34.TA5, TA6 | QA whitebox / PO live: pending |
| T34.TA8 (Origin: evil/null/other port/https 403 `origin not allowed`, stub 0 calls; local 127.0.0.1/localhost 200; PUT /api/ui evil 403, route not called) | test_squadboard_open.py::Route::test_T34_TA8_foreign_origin_refused_before_the_route |
| T34.TA7 | test_windows_safe.py, test_no_bare_bash.py pass; native Windows untested |

## Old pins edited
`tests/test_squadboard_panels.py::Static14::test_T14_TU3_...` (TU.5): was "no `method:` in panel_files.js"; now exactly one `POST` and one `/api/open?squad=` fetch. Nothing else edited.

## Runs
Pass: test_squadboard_open, _panels (except below), _page, _server, _ui, test_windows_safe, test_no_bare_bash.
Red, not ours: `Panels12::test_T12_AC1_...` expects `\d+ h ago`, gets `1 d ago` (real clock; no file of mine touched).
