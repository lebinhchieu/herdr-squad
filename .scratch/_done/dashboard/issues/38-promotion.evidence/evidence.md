# Evidence 38: promotion and plugin bump (docs only)

## Behaviour
Docs and the version file only. README row, ADR 0020 amendment and CONTEXT.md glossary say what the merged code does. `architecture.md` (the scope's file, outside the repo) was edited in place, no commit. plugin.json is 0.7.2.

## AC table
| Item | Claim | Proof |
|---|---|---|
| T38.TA1 | grid G = 2, 4 or 6 | templates/board/layout.js:17-20 |
| T38.TA1 | tracks 1..12 on PUT /api/ui | bin/squadboard_ui.py:38, :108 |
| T38.TA1 | page reads >12 as 12, bad = default | templates/board/board.js:435; layout.js:89-91 (default 2 grid columns) |
| T38.TA1 | round half up, clamp [smallest, G] | layout.js:91-92 |
| T38.TA1 | col read only to migrate, span ignored | layout.js:65-76 migrate; board.js:421-425 |
| T38.TA1 | POST /api/open, token, Host, Origin | bin/squadboard.py:219, :346-356, :395 |
| T38.TA1 | paths under squad folder and .scratch, 5 s, argv list | bin/squadboard_open.py:19, :90, :125 |
| T38.TA1 | code --goto, vscode:// fallback | bin/squadboard_open.py:3; templates/board/panel_files.js:49-50 |
| T38.TA1 | --demo: fixture copy, HOME/USERPROFILE/CLAUDE_CONFIG_DIR, removed on exit, DEMO label | bin/squadboard_demo.py:5-6, :198, :213; board.js:290 |
| T38.TA1 | layout.js function names | layout.js:23,45,65,89,95,96 |
| T38.TA2 | version 0.7.1 -> 0.7.2, only plugin.json (as 82aa08f) | `git show 82aa08f --stat`: plugin.json only. Tests OK: test_squadupgrade, test_promotion_0_6_0, test_squad_start, test_squad_respawn, test_squadruntime |
| T38.TA3 | docs + version only | `git diff 795bee3 --stat`: plugin.json, CONTEXT.md, README.md, ADR 0020 + this file |
| T38.TAx | no "assert X" AC in 38 | n/a (docs) |

## Known
- tests/test_squad_spawn.py::test_a_failed_agent_start_leaves_the_old_overrides_file fails (returncode 0). The diff has no code or test change, so it is not from this ticket; it runs inside herdr (HERDR_ENV=1) here.
- tests/test_squadboard_demo.py RunningDemo.test_T37_TA6_AC8_AC10_read_only_and_cleaned fails on this machine (global git ignore), as the Manager said. Not run again.
- Differences from promote.md, ruled by TL (ANSWER 38): G = 2/4/6 (not 1..3), default 2 grid columns (not twelfths).
