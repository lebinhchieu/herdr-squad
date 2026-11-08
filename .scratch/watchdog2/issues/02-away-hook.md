# Task 02: "I am away" / "I am back" hook

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (the goal promotes in its last scope, goals/watchdog2/promote.md); full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag, user-visible change or business doubt: `BLOCKED <task>`.

Status: ready
Source: `goals/watchdog2/goal.md` (Request 3, answers of Chieu) and `shared/decisions.md`. Read only those, `hooks/hooks.json`, `bin/squad-notify` (example hook) and `bin/squad-watchdog` (`sleep`, `set_sleep`).
Files: `hooks/hooks.json`, new `bin/squad-away-hook`, new `tests/test_away_hook.py`. No README, no `bin/squad-watchdog` edit (another scope changes it).
Ticket: commit this file's content as `.scratch/watchdog2/issues/02-away-hook.md` in your first commit.
Base: main. Repo: /home/chieule/workspace/squad.

## AC
- AC1 A `UserPromptSubmit` hook in `hooks/hooks.json` runs `bin/squad-away-hook`. It is Python and works on Windows and Linux (no bash).
- AC2 It acts only when `SQUAD_ROLE` is `manager` and `SCOPE_DIR` or `GOAL_DIR` names a folder. Any other session: it prints nothing and exits 0.
- AC3 The prompt text, trimmed and case-insensitive, starting with `I am away` or `I'm away` (word end after it): it runs `squad-watchdog sleep on --home <home>` and writes `<home>/away` (one line `on`).
- AC4 The prompt starting with `I am back` or `I'm back`: `squad-watchdog sleep off --home <home>` and the `away` file is deleted. Other prompts change nothing, even when they contain the phrase later in the text.
- AC5 On a match it prints hook JSON with `additionalContext`: after away, one short instruction to the Manager (away mode is on, follow the away rule, tell Chieu in one line that sleep and away mode are on); after back, the Manager reads the parked questions and writes ONE inbox read item listing what was decided while away. The text is final in task 03's rule; keep it short and point to the rule id once task 03 names it.
- AC6 A failing `squad-watchdog` call never blocks the prompt: the hook exits 0 and says in `additionalContext` that the switch failed.
- AC7 Tests (new file): a Manager session turns both on and off; a non-Manager session and a mid-sentence phrase do nothing; the hook JSON is valid. Touched test files pass.

## Design notes (Developer fills in)
- Hook input is JSON on stdin with `prompt`. Output `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": "..."}}`.
- Use `squad-watchdog`'s own `sleep` command (call the script with `sys.executable`), not a copy of its file format.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace.
- Repo CLAUDE.md "Running tests": a diff touching `hooks/hooks.json` also needs `grep -rl 'hooks.json' tests/` hits run.
- Do not bump the plugin version.
