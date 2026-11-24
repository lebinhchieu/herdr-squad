# 14 Evidence check accepts the whole ticket folder

Status: ready-for-agent

Spec: none (source: `tasks/plugin-proposals/07-evidence-base-folder.md`; absorbs followups 02)
Blocked by: none
Aim: Evidence-only commits may add any file in the ticket folder
Estimate: 1.5h
Depends on: none

Duties: Design and technical AC: `$SCOPE_DIR/tasks/plan-tech3.md`, sections "Design and technical AC per ticket" (this ticket) and 2 "Files per ticket"; iteration rules in `$SCOPE_DIR/tasks/14.md`. Build it; run the ticket's test files plus the `grep -rl` hits and the three whole-repo files (`test_windows_safe`, `test_utf8_helpers`, `test_instructions`); write `evidence.md` (`## Behaviour`, `## Review`, `## Checks`, `## Changelog line`); HANDIN to the Team Lead. Spawn with `--base` the sha of 12's first commit: the evidence check needs this ticket's `<stem>.md` beside its evidence folder.
Files: `bin/squadevidence.py`, `bin/squadmergecheck.py`, `tests/test_squad_evidence.py`, `tests/test_squad_merge_check.py`

## Problem
`squad-evidence check --base` flags `checks.md` and `pane-states.txt` in the ticket's evidence folder on an evidence-only commit (exit 1, two problem lines), and `squadmergecheck.evidence_only` says False for the same commit. The board's `_evidence_only` already accepts them: the two `is_evidence_path` functions disagree with it.

## Change
A changed path is evidence when it lies under `<stem>/` or `<stem>.evidence/` and `<stem>.md` exists (on disk in `squadevidence`, `git cat-file -e ref:` in `squadmergecheck`). The prefix test is `<stem>/` with the slash, so `<stem>x/` and `<stem>.md` itself are refused. The board's `_evidence_only` stays unchanged. The Tech Lead reads `git diff --stat` of every evidence-only commit (a script under the folder would pass).

## AC
- AC1: one path table asserted for both `is_evidence_path` functions. Accepted: `<stem>/evidence.md`, `<stem>/img/a.png`, `<stem>/checks.md`, `<stem>/pane-states.txt`, `<stem>/sub/x.md`, `<stem>.evidence/x`. Refused: `<stem>x/a.md`, `<stem>.md`, `<other>/checks.md`, `bin/x.py`, a stem with no ticket file.
- AC2: temp repo with a ticket and an evidence commit adding `checks.md` and `pane-states.txt`: `squad-evidence check <folder> --base <code sha>` exits 0 (base: exit 1) and `squadmergecheck.evidence_only(code, tip)` is True (base: False).
- AC3: `squad-evidence add` leaves a sibling `checks.md` in the folder (guard test; it does today).
- AC4: the followups 02 `wontfix` edit is made by 12's first commit, not here.

## Comments
