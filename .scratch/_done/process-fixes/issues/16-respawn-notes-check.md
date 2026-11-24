# Task 16: squad-respawn checks the notes file

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Source of the change: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task (it rides the last task of the goal's last scope, SQ-5).

Status: ready
Source: finding 4 of the review (Chieu E17 a).
Files: bin/squad-respawn, tests/test_squad_respawn.py (extend it; grep `tests/` for other hits)
Ticket: commit this file's content as `.scratch/process-fixes/issues/16-respawn-notes-check.md` in your first commit.
Base: main. No merge.

## AC
- AC1 When `roles/<name>.notes.md` is missing, `squad-respawn` prints one line naming the file and NOTE-1, exits 1 and starts nothing (no retire, no spawn).
- AC2 When the notes exist but are older than 10 minutes, it prints a warning (stderr) and goes on.
- AC3 `--force` skips both checks.
- AC4 The 100-line warning stays; fix its pointer: replace "process.md → Notes" with `squad-process rule NOTE-1` (this is finding 9b; task 20 of the next scope does not repeat it).
- AC5 One test per AC (extend `tests/test_squad_respawn.py`). `--dry-run`, if the script has it, behaves as before.
