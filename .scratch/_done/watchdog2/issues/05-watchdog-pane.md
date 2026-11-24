# Task 05: the watchdog runs in its own herdr tab

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (the goal promotes in its last scope, goals/watchdog2/promote.md); full suite: QA whitebox, once on the final sha, only after Chieu says yes through the Manager. A risk flag, user-visible change or business doubt: `BLOCKED <task>`.

Status: ready
Source: `goals/watchdog2/goal.md` (Request 2, answers of Chieu), `shared/decisions.md`, `shared/summaries/wd2-trigger.md` (its open items 2 and 3). Read only those, `bin/squad-start` (`start_watchdog`, its two callers), `bin/squad-watchdog` (`run`, `decide`, `set_sleep`, docstring), `bin/squad-spawn` lines ~470-520 (how it opens a herdr tab and falls back to `herdr pane run` on Windows).
Files: `bin/squad-start`, `bin/squad-watchdog`, `tests/test_squad_start.py`, `tests/test_squad_watchdog.py`. No README (task 06 does it).
Ticket: commit this file's content as `.scratch/watchdog2/issues/05-watchdog-pane.md` in your first commit.
Base: main. Repo: /home/chieule/workspace/squad.

## AC
- AC1 When `squad-start` (new scope or goal with a Manager, and `--resume`) runs inside herdr, the watchdog runs in its own herdr tab in the same workspace as the Manager. The tab runs only `squad-watchdog run --home <home> --manager <name>`: no Claude, no shell chatter. The tab is labelled `watchdog`.
- AC2 One watchdog tab per herdr workspace: if a tab for this home's watchdog is alive (the heartbeat guard in `run` already says so), no second tab is opened and no second process runs. A second `run` of the same home still exits 0 at once (guard unchanged).
- AC3 The tab does not take focus (the Manager's tab keeps it) and the tab's command ends when the home folder is gone (`run` already loops on `home.is_dir()`); a dead tab is not left behind with a shell prompt waiting.
- AC4 Outside herdr (no herdr, or the tab call fails) the detached process of today is the fallback, and a failure only warns on stderr: the work never depends on the watchdog. `SQUAD_WATCHDOG=off` still starts nothing.
- AC5 Windows: where a pane is a PowerShell shell and `herdr tab create` cannot run the command directly, use `herdr pane run <pane> "<cmd>"` as `squad-spawn` does. Quote the command for the shell that runs it.
- AC6 One name for the switch: `sleep-when-idle` in the CLI help, the switch file's comment, the docstring and the log (today the CLI and file say `sleep-when-done`). `squad-watchdog sleep on|off` keeps working; an existing `watchdog.sleep` file stays valid (the file holds `on`/`off`; only the comment changes).
- AC7 With no ticket at all the log line does not say "open tickets" (for example `team idle`). With open tickets it still says `team idle with open tickets`.
- AC8 Tests: the tab command is built correctly for Linux and for the Windows `pane run` path (list argv, no shell string where avoidable); fallback to the detached process when herdr fails; `SQUAD_WATCHDOG=off` starts nothing; log text for no tickets. Touched test files pass.

## Technical AC (QA whitebox, agreed with the Developer in this file)
- T1 `herdr` is called with a list argv and a timeout (at most 10 s per call); `TimeoutExpired`, `OSError` and a non-zero exit go to the AC4 fallback path and never raise out of `squad-start`.
- T2 Tests stub `herdr` (a fake script on `PATH` or a patched `subprocess.run`) and never open a real tab or start a real watchdog; they run in a temp dir and never touch the real `$SQUAD_DIR`.
- T3 The workspace is the Manager's own: take it from the herdr JSON that `squad-start` already reads (`tab` / workspace id as `name_workspace` does), not from the cwd.
- T4 REV-4 real sample: the herdr `tab create` JSON used in the tests is a real capture (`jq`-able, `.result.tab.tab_id`, `.result.root_pane.pane_id`) or copied from `tests/fixtures/`; the Developer names the source in `evidence.md`.
- T5 `bin/squad-watchdog` edits are only the name (AC6) and the log wording (AC7); `decide` logic and the heartbeat guard are unchanged (`git diff` shows it).
- T6 Targeted run: `tests/test_squad_start.py`, `tests/test_squad_watchdog.py` and every hit of `grep -rl 'squad-start' tests/`, `grep -rl 'squad-watchdog' tests/` and `grep -rl 'sleep-when' tests/`; none skipped. No full suite without Chieu's yes.
- T7 No plugin version change, no README, no `agents/` edit.

## Design notes (Developer fills in)
- `herdr tab create` takes no command, so the tab is made (label `watchdog`, `--no-focus`, `--workspace $HERDR_WORKSPACE_ID`, the same id `squad-spawn` gave the Manager's tab) and `herdr pane run <pane> "<cmd>"` types the command. POSIX line: `exec <shlex.join argv>` (the tab closes when the watchdog ends); PowerShell: `& 'a' 'b'; exit`.
- Guard: `start_watchdog` reads `watchdog.state.json` beat (3 x interval, as `run` does) and opens nothing when it is fresh. Any herdr failure (non-zero, timeout 10 s, OSError, bad JSON) warns once on stderr, closes a half-made tab, and falls back to the detached process.
- `squad-watchdog`: only the name `sleep-when-idle` and the log reason `team idle` when `snap["tickets"]` is empty; `decide` untouched.
- Fixture `tests/fixtures/herdr/tab-create.json` is a real `herdr tab create` capture (tab closed after).

## Rules to follow
- SQ-2: `## Review` starts with an AC trace.
- Do not bump the plugin version.
