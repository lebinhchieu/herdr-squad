# Task 14: squad-usage counts a Bash first action and shows the line

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes later); full suite: QA whitebox, only after Chieu agrees (the Manager asks him). A risk flag, user-visible change or business doubt: `BLOCKED NN`. Run `grep -rl` over `tests/` for each changed string or path and run every hit (CLAUDE.md "Running tests"). `## Review` starts with an AC trace (SQ-2), one line per AC: `AC<n> | test or capture file | how run`. Source of the change: `.claude/squads/plugin/goals/process-fixes/answers/respawn-rules-review.md`. No version bump in this task (it rides the last task of the goal's last scope, SQ-5).

Status: ready-for-agent
Source: finding 1 and 2 of the respawn rules review (Chieu E17 a).
Files: bin/squad-usage, tests/test_squad_usage.py (extend it; grep `tests/` for other hits)
Ticket: commit this file's content as `.scratch/process-fixes/issues/14-usage-first-action.md` in your first commit.
Base: main. No merge.

## AC
- AC1 First action fallback: a main-thread session with no Edit, Write, NotebookEdit or SendMessage call, but a state-changing Bash call, gets `first_action` = its context at the first such Bash call, so its line = that + 50k (cap 180k). State-changing Bash = the first word is `squad-spawn`, `squad-inbox`, `squad-start`, `squad-close`, `squad-retire`, `squad-respawn`, `squad-label` or `squad-team`, or the command is `git commit` or `git merge`. Reads (`ls`, `cat`, `grep`, `squad-usage`, `squad-ledger`) never count. Keep the list in one constant next to `ACTION_TOOLS`.
- AC2 Order: whichever of the old action tools or the Bash fallback comes first sets `first_action`. A session with only reads still has `first_action` None and line 180k.
- AC3 Table: the `squad-usage` table gets two columns, `1st act` (the first-action context, `-` when none) and `line` (the respawn line), after `last ctx`. Numbers in k like the other columns. `--check` output is unchanged.
- AC4 One test per AC (extend `tests/test_squad_usage.py`) using a small transcript fixture.

- T1-T12 agreed with QA whitebox (evidence/14/qa-w.md): T1 one constant, T2 first word only, T3 a non-string command is a read, T4 sidechain skipped, T5 single pass, T6 header and widths, T7 newest session, T8 one test per AC, T9 targeted tests plus the three SQ-10 files, T10 real-roster run, T11 no other files, T12 style.

## Design notes
- `ACTION_BASH` (8 words) and `ACTION_GIT` (`commit`, `merge`) sit next to `ACTION_TOOLS`. `is_action(block)` replaces the old name test in the single pass of `first_action_ctx`.
- T2: the basename of the first word counts (`bin/squad-spawn`, `/abs/squad-inbox`). One leading `cd DIR &&` is skipped. Everything else is a read: an env prefix (`X=1 squad-spawn`), `git -C d commit`, `ls squad-spawn`, a state-changing word after a later `&&` or `;`. The ticket says first word, so this is on purpose.
- T3: a missing or non-string `input` or `command` is a read.
- T7: `summarize_agent` keeps the newest session's `first_action`, so `line` is the newest session's line. Intended.
- `respawn_line`, `check` and `--check` are not edited.
