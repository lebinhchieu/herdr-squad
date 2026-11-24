# 06 Merge record hook

Status: ready-for-agent
Blocked by: 01

New `bin/squad-merge-record` plus one PostToolUse entry (matcher Bash) in `hooks/hooks.json`: a Manager `git merge squad/...` records `merged` through the module (design.md s5.3). `squad-task merged NN` is the manual fallback.

Files: bin/squad-merge-record (new), hooks/hooks.json, tests/test_squad_merge_record.py (new)
AC: states.md AC6 (record side), W7. Technical AC: T1, T11.
Spec: tasks/states.md, tasks/design.md. Gates warn, never block. Targeted tests only.
Store: append events to `$SQUAD_DIR/task-events/<ticket-folder-slug>.jsonl` (tasks/design.md s2, format frozen); NOT ticket-file lines. Warnings go back via hook `additionalContext` and are saved in the event (D4). Read design.md first.
