# 31 Promotion and plugin 0.7.1: evidence

## Behaviour
Docs and version only. README `bin/squad-board` row: new Tasks sentence and Files sentence. ADR 0020: one "Amendment 2026-11-04" section. `plugin.json`: 0.7.0 -> 0.7.1 (own commit).

Two deviations from `promote.md`, both found by its **verify** marks:
- Source order. promote.md: `tickets:` line, then the scope's `tasks/`, then `.scratch/<scope>`. Code (`bin/squadtickets.py:15` `SOURCES = declared, scratch, scope, plan`) and ticket 28 line 24: `tickets:` line, `.scratch/<scope>/issues`, scope `tasks/`, plan table. README follows the code. The ADR text in promote.md already had the code's order.
- "nothing else is tried" is false: with a `tickets:` line whose folder has no `NN-*.md`, the reader falls through (T28.AC12). README says "the first source that has a task wins" instead.
Tech Lead: please update promote.md to match.

## AC table
| Item | Shown by |
|---|---|
| T31.TA1 diff is docs + version | `git diff --stat 61bee77..HEAD`: plugin.json, README.md, ADR 0020 only |
| T31.TA2 wording equals promote.md | ADR section verbatim (without the verify marks); README Files sentence verbatim; README Tasks sentence differs, see Behaviour |
| T31.TA3 one table row | `grep -c '^| `bin/squad-board`' README.md` = 1 |
| T31.TA4 true to code | order: `bin/squadtickets.py:15,144-176`; `abs`: `bin/squadboard_files.py:85`; `vscode://` in `templates/board/panel_files.js`; `col` 0..N check in `bin/squadboard_ui.py` |
| T31.TA5 version test | `python3 tests/test_promotion_0_6_0.py` OK (3 tests); plugin.json valid JSON, 0.7.1 |
| T31.TA6 full suite | Tech Lead, on the integration sha |
Open gap: ADR line "col (0..11)" and "span is no longer written" taken from promote.md; I checked only that `col` is range-checked in `squadboard_ui.py`, not the value 11.
