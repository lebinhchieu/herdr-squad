# 01 `bin/squadtask.py` + `squad-task` command

Status: ready-for-agent
Blocked by: none

One writer module for ticket state; appends events (design.md s2, s4). The triage label table of states.md s5 is read, not written. Commands: claim, handin, returned, blocked, passed, merged. Returns warnings W1-W8 (s6), writes the record anyway. Checker count M = QAs on roster + one confirmer (never 0).

Files: bin/squadtask.py, bin/squad-task (new), bin/squadledger.py (add `parse_handin` only), tests/test_squadtask.py (new)
AC: states.md s2, s5 (incl. the label table: needs-triage, needs-info, ready-for-agent, ready-for-human, claimed, done, wontfix), s6 (W1-W8), s4 (M never 0). AC8: a claim while `Blocked by:` is not yet passed returns the W1 warning and still records the claim.
Spec: tasks/states.md (BA, final). Gates warn, never block. Tests: targeted only (repo CLAUDE.md); one test per AC or regression risk.
Store: append events to `$SQUAD_DIR/task-events/<ticket-folder-slug>.jsonl` (tasks/design.md s2, format frozen); NOT ticket-file lines. Warnings go back via hook `additionalContext` and are saved in the event (D4). Read design.md first.
Technical AC: T1-T6, T8, T11, T12 (design.md s8).
