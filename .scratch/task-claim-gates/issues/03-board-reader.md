# 03 Board reads ticket fields first, ledger fallback

Status: ready-for-agent
Blocked by: 01

Reader folds `task-events/<slug>.jsonl` (design.md s3, s6), ledger as fallback (old tickets, s8). Shows all tickets of scope or goal; no-QA teams (`checking, 0 of 1`); `merged` from the recorded branch of the event; last active from the newest event; blocked from live `Blocked by:`; wontfix. `done` word becomes `passed` in the data only. No design change.

Files: bin/squadboard_tasks.py, bin/squadboard_active.py, bin/squadboard_list.py, tests/test_squadboard_tasks.py, test_squadboard_list.py, test_squadboard_active.py (extend)
AC: states.md AC1, AC3-AC9 (read side). Also: s2 precedence line (one word per row); s5 label table on read; ASK 1 default: `passed` when the branch tip is unknown, `ready for review` when the tip is known and matches.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
Store: append events to `$SQUAD_DIR/task-events/<ticket-folder-slug>.jsonl` (tasks/design.md s2, format frozen); NOT ticket-file lines. Warnings go back via hook `additionalContext` and are saved in the event (D4). Read design.md first.
Technical AC: T8-T11 (design.md s8).
