# 11 Hooks find a resumed session in roster.md

Status: ready-for-agent (draft by the Tech Lead, 2026-11-24; committed by the Developer, FILE-11)

Spec: `.scratch/upstream-proposals/spec.md`. Base: 4e7d547. Chieu's go-ahead for A is in `iterations/1.md` ("Plan change"). Risk flag: hooks every role runs.

## Problem

herdr restores a pane with `c1 --resume <id>`. That session has no `SQUAD_*` variables, so every squad hook that reads them exits at once: `squad-log-message` stops logging, the usage and lazy hooks stop, and the path and manager guards do not apply. The Team Lead, the Tech Lead and both QAs of this scope run that way. The roster already holds the answer: the Session column of `roster.md` has the id of every agent `squad-spawn` and `squad-respawn` started.

## Decision (Tech Lead)

One shared helper reads the roster; each hook calls it only when its own variables are missing. Out of scope: the lost `--agent` flag, any change to `squad-spawn`, `squad-respawn` or the roster format.

- New `bin/squadsession.py` with `resolve(env, payload)`; returns a dict of `SQUAD_NAME`, `SQUAD_ROLE`, `SQUAD_SCOPE`, `SQUAD_DIR`, `SCOPE_DIR`, `GOAL_DIR` (the last two only when they apply, as `squad-spawn` sets them), or `None`.
  - If `SQUAD_NAME` and `SQUAD_DIR` are already set, it returns `None` and the hook does what it does today. The environment always wins; the helper never overrides a set variable.
  - No `session_id` in the payload: `None`.
  - Otherwise it finds the project (`CLAUDE_PROJECT_DIR`, the payload `cwd`, the process cwd; from a git worktree the main checkout through `git rev-parse --git-common-dir`) and reads `.claude/squads/*/scopes/*/roster.md`, `.claude/squads/*/goals/*/roster.md` and the flat `.claude/squads/*/roster.md`; never a `_done/` folder. The first row whose Session cell equals the id, as a whole string, gives name, role and scope; the folders follow from the row's own roster path (a scope roster: `SCOPE_DIR`, plus `GOAL_DIR` when its `scope.md` has a `goal:` line, as `squad-spawn` does; a goal roster: `GOAL_DIR`).
  - Every value is checked before it is returned: the name and role match `^[a-z0-9-]+$`, the folders exist. A row that fails the check, an empty Session cell or an id with no row gives `None`.
- New `bin/squad-whoami` (executable, LF, small) for the bash hooks: reads the hook payload on stdin and prints one `KEY=value` line per variable, nothing when `resolve` gives `None`. The hooks read those lines with `while IFS== read -r k v`, set only the six keys above and only when the variable is empty. Never `eval`.
- Hooks that call it when their variables are missing: `squad-log-message`, `squad-usage-hook`, `squad-lazy-hook`, `squad-notify`, `squad-path-guard`, `squad-manager-guard`, `squad-merge-record`, `squad-away-hook`. Each keeps its present behaviour for a session with the variables, and for a session with no match it stays as silent as today. A resumed Manager or Developer is now guarded like a spawned one; that is the point, and the AC cover it.

## Files (LC-9)

`bin/squadsession.py` (new), `bin/squad-whoami` (new), the eight hooks above, `tests/test_session_lookup.py` (new), `skills/squad-process-update/changelog.md` (a line in v29; no new version). No rule text, no `hooks/hooks.json` change, no `templates/`, no `hooks/po-inbox/` (so no file shared with ticket 10). Harness: the existing hook tests `tests/test_squad_log_message.py`, `test_squad_usage_hook.py`, `test_lazy_hook.py`, `test_squad_path_guard.py`, `test_squad_manager_guard.py`, `test_squad_merge_record.py`, `test_squad_notify.py`, `test_away_hook.py`, and `test_hooks_json.py`.

## AC

- AC1 (the failure): a hook run with no `SQUAD_*` variables and a payload whose `session_id` is in a scope's roster acts as that agent. `squad-log-message` appends its record to that scope's `messages.jsonl` with `from` set to the row's name; the test uses the real `bin/squad-log-message` through a temp project.
- AC2 (silence): the same run with an id that has no row, an empty id or a roster that cannot be read writes nothing, prints nothing and exits 0, as today.
- AC3 (environment wins): with `SQUAD_NAME` and `SQUAD_DIR` set, the result is identical to base, even when the roster names another agent for that session id.
- AC4 (helper, one test file, one test per risk): `resolve` handles a Developer row in a worktree cwd, a goal Manager row, a flat roster, a `_done/` roster that must be ignored, a Session cell that only contains the id as a substring (no match), and a name that fails the pattern (no match). No test of trivial code.
- AC5 (guards): a resumed `dev` or `qa-whitebox` session, no variables, is stopped by `squad-path-guard` for a write the guard forbids that role; a resumed Manager is covered by `squad-manager-guard`. One test each, reusing the existing test helpers.
- AC6 (every hook): one test checks that each of the eight hook files calls `squad-whoami` or `squadsession`, so a ninth hook cannot be forgotten by accident; it reads `hooks/hooks.json` for the list of squad hooks.
- AC7 (real samples, REV-4): the fixtures are two real roster files copied from this squad (this scope's `roster.md`, and one with a goal Manager row or an empty Session cell, from another scope), not hand-written tables; quote their paths and sha in the evidence.
- AC8 (cost): a session with the variables adds no process: `squad-whoami` is not started when `SQUAD_NAME` and `SQUAD_DIR` are set (test with a `squad-whoami` stub on PATH that fails the test if run). The PO's own session (no row) does one roster scan per hook call; the evidence shows the time of one call in the real project (under 100 ms).
- AC9 (SQ-10): `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` pass, quoted in `## Behaviour`, plus every `grep -rl` hit over `tests/` of each changed hook and helper name. The new Python file uses `encoding="utf-8"` and passes the T3/D11 scan; `bin/squad-whoami` has LF endings and `bin/* text eol=lf` still holds.
- AC10: `python3 bin/squad-process lint` is unchanged (exit 0); the diff lists only the files above, the ticket and its evidence; the changelog line names the eight hooks and says why.
- AC11 (live, QA blackbox): QA blackbox shows the failure fixed in a real resumed session: in a scratch squad under `/tmp` with a stub `claude` as `tests/test_squad_start.py` does, a hook run from a shell with the `SQUAD_*` variables unset and a real session id from the roster logs the message; the same run with a made-up id does not. Both QAs also run the AC8 timing.

## Duties

Evidence: `.scratch/upstream-proposals/issues/11-session-lookup/evidence.md`. Hand in to both QAs (they check every role's hooks and the SQ-10 files). The one full `--tz` then goes on the final sha that holds 10 and 11 (Tech Lead, `SQUAD_*` unset, stray `bin/*.pyc` cleared, `PYTHONDONTWRITEBYTECODE=1`).

## Comments

- 2026-11-24 Developer (plugin-dev-upstream-proposals-11): built as designed. `bin/squadsession.py` (`resolve`, `fill`), `bin/squad-whoami`, eight hooks wired, `tests/test_session_lookup.py` with two real rosters under `tests/fixtures/session_lookup/`, one changelog line in v29 (no bump).
- Python hooks call `squadsession.fill`; the bash hooks read `squad-whoami` lines with `while IFS== read -r k v`, only the six keys, only when empty, no `eval`. `squad-log-message`, `squad-usage-hook` now read stdin before the variable check (the helper needs the payload); a session with the variables still starts no extra process (AC8 test, stub `squad-whoami`).
- `squad-manager-guard` resolves only for a command it acts on (`squad-spawn`, `squad-inbox add`), and imports the helper at that point, so a `bin/` without it stays silent. `squad-notify` resolves only when `HERDR_ENV=1`; `squad-away-hook` only after the prompt matches "I am away/back".
- Real resumed-session check: `claude --resume <id>` keeps `session_id` (two payloads of one id, quoted in the evidence).
- Note for the Tech Lead's `--tz` run: `tests/test_away_hook.py` fails when `SQUAD_*` is set in the shell (`squad-process rule ITER-17` then exits 2); it passes with them unset. Not caused by this ticket.
