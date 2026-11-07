# 03 Board reads ticket fields first, ledger fallback

Status: ready-for-agent
Blocked by: 07 (start from 07's passed branch)

Reader folds `task-events/<slug>.jsonl` (design.md s3, s6), ledger as fallback (old tickets, s8). Shows all tickets of scope or goal; no-QA teams (slot `evidence`: `passed` after the hook's check, never `checking, 0 of 0`); `merged` from the recorded branch of the event; last active from the newest event; blocked from live `Blocked by:`; wontfix. `done` word becomes `passed` in the data only. No design change.

Files: bin/squadboard_tasks.py, bin/squadboard_active.py, bin/squadboard_list.py, tests/test_squadboard_tasks.py, test_squadboard_list.py, test_squadboard_active.py (extend)
AC: states.md AC1, AC3-AC9 (read side). Also: s2 precedence line (one word per row); s5 label table on read; `ready for review` is dropped: unknown tip gives `passed`, known and different gives `sha changed after PASS`. Also drops `ready_for_review` data in the reader (states.md s3).
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
Store: append events to `$SQUAD_DIR/task-events/<ticket-folder-slug>.jsonl` (tasks/design.md s2, format frozen); NOT ticket-file lines. Warnings go back via hook `additionalContext` and are saved in the event (D4). Read design.md first.
Technical AC: T8-T11, T19 (design.md s8).
