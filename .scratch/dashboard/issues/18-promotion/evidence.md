# Evidence 18 promotion

## Behaviour
Doc-only. `README.md` row for `bin/squad-board` replaced by the text of `promote.md` section 1, as one table row. `git diff --stat main`-style check: only `README.md` changed in this commit.
- Checked against code: `squad-board --help` lists `--squad NAME|PATH`, `--goal G`, `--scope S`, `--port N` (default 8765; 0 picks a free one), `--herdr-json FILE`, `--no-open`. `--goal` with `--scope` is refused ("cannot be used together"). `squad-inbox park` takes `--text --from --blocks --level {scope,goal,squad}`; `unpark` and `resolve --answer` exist.

## QA whitebox check

### QA whitebox 18: FAIL on 3744585

Checked a clone of `squad/board/dashboard/board-dev-promo-22`. `git diff --stat a3be594 HEAD`: `README.md` (1 row), the ticket file and `evidence.md`. No file under `bin/`, `templates/`, `tests/`. TA1 (row = old `promote.md` text) and TA2 pass.

The cause is mine: three phrases in the old `promote.md` section 1 are not true. TA3 fails. I fixed `promote.md` (same row, three phrases changed). Replace them in the README row; change nothing else.

- **F1 README.md:46 "with neither, the page opens on a picker".** `templates/board/panel_scopes.js:227-249` (`boot`, `openingOrder`): the page opens on the flag, then the URL hash, then the saved choice from `board-ui.json`; only when none of them is open does it show the picker. New text: "with neither, the page opens on the choice it saved last time if that goal or scope is still open, else on a picker."
- **F2 README.md:46 "(column, order and size choices, saved by the page)".** `bin/squadboard_ui.py:6-12` stores `font`, `choice`, `recent`, `auto`, `panels` (order, span, hidden, max_height) and `columns`. New text: "(font size, the last choices, panel order, width and visibility, and chosen columns, saved by the page)".
- **F3 README.md:46 "without it the page guesses".** `bin/squadboard_tasks.py:210-218` and `squadboard_list.py:138-146`: without the line the page looks for `.scratch/<scope name>/issues/`, else tickets are unknown. New text: "without it the page looks for `.scratch/<scope name>/issues/` and shows the tickets as unknown if that folder is missing."

Passed by my own run: `squad-board --help` (all flags and the default port 8765, `--port 0`, `--herdr-json`, `--no-open`), `--goal`+`--scope` refused, `squad-inbox park|unpark|resolve --help` flags, 127.0.0.1 in the code, `squad-start` prints the command.

Pass bar: the row says exactly the new phrases above. Then I run `grep -rl README tests/` and the hits (TA5).

### Re-check f26900d: PASS
README row equals promote.md section 1 (byte compare). Only README.md changed since 3744585; no bin/templates/tests. Tests that read README: test_squad_close (79), test_squad_path_guard (21), test_promotion_0_6_0 (3) all OK. F1-F3 closed.
