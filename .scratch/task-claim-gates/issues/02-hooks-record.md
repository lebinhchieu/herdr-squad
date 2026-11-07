# 02 Hooks record claim, handin, FAIL, BLOCKED, PASS

Status: ready-for-agent
Blocked by: 01

`squad-spawn` for ticket NN calls the module claim. `squad-log-message` records HANDIN, FAIL, BLOCKED, PASS (checker or confirmer) through the module; warnings go to hook stderr. `squad-spawn --task NN` becomes env `SQUAD_SPAWN_TASK` before the exec (design.md s5.2). The merge hook is ticket 06.

Files: bin/squad-spawn, bin/squad-log-message, tests/test_squad_spawn.py, tests/test_squad_log_message.py (extend)
AC: states.md AC2, AC3, AC4, AC5 (record side), AC8.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
Store: append events to `$SQUAD_DIR/task-events/<ticket-folder-slug>.jsonl` (tasks/design.md s2, format frozen); NOT ticket-file lines. Warnings go back via hook `additionalContext` and are saved in the event (D4). Read design.md first.
Technical AC: T1, T5, T7, T11 (design.md s8).
