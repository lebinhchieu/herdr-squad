## Review

| AC | Test or capture | How run |
|---|---|---|
| T3.2 CONTEXT terms Next step, Commands table, Squads pane; README line for `/squads`, `squad-tree` | `git diff main -- CONTEXT.md README.md` | read |
| T3.2b ADR 0026 line 3 is `Status: accepted (...)`; six facts named; ADR 0020 line 7 has "(amended by 0026)" | `git diff -- docs/adr` (4 changed lines) | read |
| T3.3 / SQ-10 | the three files below | `python3 tests/<file>.py` |

## Behaviour

Docs only. `tests/test_windows_safe.py` 14 OK, `tests/test_utf8_helpers.py` 14 OK, `tests/test_instructions.py` 16 OK, `tests/test_promotion_0_6_0.py` 3 OK, `tests/test_templates.py` 8 OK. No full suite.
