# 0036: Task ids, evidence folder and no-QA checkers

Status: accepted. Builds on ADR 0034 (the HANDIN evidence gate); changes no rule text.

## Context
Iteration 2 ended with the pinned plugin refusing its own branch: `squad-task` rejected `integration` and `promotion`, `squad-log-message` logged rule ids such as SQ-10 as task ids, the evidence check refused `checks.md` in a ticket's folder, and `squad-merge-check` waited for PASS from QAs retired on a scope with no QA.

## Decision
- One task-id grammar: `[0-9]+ | integration | promotion` (`squadtask.TASK_ID`, `is_task_id`). The bash test in `squad-spawn` is a copy; the jq filter in `squad-log-message` is a superset (it also matches rule ids such as SQ-10, so the message log still records them as `task`); one test runs a table of ids through all three. A rule id is never a task: `from_message` writes no event for it. The rule text MSG-3 still says `NN`; the two names are tolerated spellings.
- Evidence-only rule: a changed path is evidence when it lies under `<stem>/` with `<stem>.md` present (on disk for `squad-evidence`, in the ref for `squad-merge-check`), or under an old `<stem>.evidence/` folder (accepted without the `.md` check). The slash is part of the prefix, so `<stem>x/` and `<stem>.md` itself are refused. The board's `_evidence_only` is narrower: it accepts only the folders of the one ticket it is judging. A script under the folder would pass; the Tech Lead reads `git diff --stat` of every evidence-only commit.
- No-QA checkers: `squadtask.checkers` takes live QA rows first; when `scope.md` has a decided `team:` without a `qa-white` or `qa-black` token, the answer is none and the slot is `evidence`; only then the old fallback to retired rows. `qa: none` carries no meaning.
- Rejected: change MSG-3 text; a new evidence file whitelist per name; reading `qa:`.

## Consequences
- The HANDIN hook records an evidence PASS in no-QA scopes; `squad-merge-check` prints `[evidence=PASS]`.
- Old `SQ-10` task rows stay in stores; readers skip them.
- Follow-ups, not done here: board, plan and report code still read `tasks/NN.md` by digits (`squadtickets.NUM_FILE`, `squadplan._draft_text`, `squadreport_tasks`, `squadboard_files`, `squadtask.TICKET_FILE`, `ticket_text`), so `integration` is not listed from a draft and its `Blocked by:` is not read; `squad-respawn` does not record the new session id, so a second lazy respawn of one agent is not covered by the spawn-event fallback.
