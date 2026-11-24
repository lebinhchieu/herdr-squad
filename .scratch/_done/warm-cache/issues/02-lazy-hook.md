# 02: first-prompt hook: "you were respawned, read your notes first"

Status: ready-for-agent
Duties: design notes = Tech Lead (tasks/design.md, the lazy contract C1-C5, binding); technical AC = Tech Lead (this file); business AC = ticket (spec stories); code check = QA whitebox; behaviour check = QA blackbox; hand in to both QAs; suite and promote.md = Tech Lead; NO full suite (DECISION 0, Chieu): run the test files you touched, the `grep -rl` hits over tests/ for each touched path or changed string, and the SQ-10 three files tests/test_windows_safe.py, tests/test_utf8_helpers.py, tests/test_instructions.py; quote the results in `## Behaviour`
Files: bin/squad-lazy-hook, hooks/hooks.json, tests/test_lazy_hook.py
Ticket path (FILE-11): `.scratch/warm-cache/issues/02-lazy-hook.md`; evidence next to it. Test harness: stdin JSON plus a temp home, in the style of `tests/test_away_hook.py`. Depends on: nothing (contract C1, C5 in `tasks/design.md`). Spec stories 30-31, 32; seam 3.

## Problem
A lazy-respawned session (ticket 01) has been started but not prompted. Whoever messages it first does not know that, so the session must be told, once, to read its notes before it answers.

## AC
1. New `bin/squad-lazy-hook` (python3, `#!/usr/bin/env python3`, executable, `squadio.utf8_stdio()`, whole `main()` in try/except, always exit 0, modelled on `bin/squad-away-hook`). Second `UserPromptSubmit` entry in `hooks/hooks.json`; `squad-away-hook` and its entry are not edited.
2. Home = `$SCOPE_DIR`, else `$GOAL_DIR`, else `$SQUAD_DIR`; name = `$SQUAD_NAME`. Marker = `<home>/roles/<name>.lazy` (C1: one line, a session id). When the hook input's `session_id` equals that line: print `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": <text>}}` with the C5 text (names the absolute notes path `<home>/roles/<name>.notes.md` and the rules path `<home>/roles/<name>.rules.md` with "read no other process file") and delete the marker. Every role, Manager included (unlike the away hook, no role gate).
3. Silent (no output, exit 0, marker left alone) when: no marker; `session_id` differs from the marker (the old session of a respawn under the same name); `SQUAD_NAME` or home unset; stdin not JSON; unreadable or empty marker. A second prompt of the same session: silent (the marker is gone). A marker of a retired name nobody reads stays harmless.
4. If the marker cannot be deleted: still print the text once, never raise (a leftover marker then fires again at most until it is removed; note it in `## Behaviour`).
5. REV-4: the real field name of the session id in UserPromptSubmit hook input comes from a recorded real sample (e.g. the existing `tests/test_away_hook.py` input, or Claude Code's hook docs in this repo, or a capture), named in `## Behaviour`; the test uses that shape. If a real sample cannot be had, say so and ASK the Tech Lead; do not guess.
6. Tests (`tests/test_lazy_hook.py`, three behaviours, one test each): marker + matching session gives the text and removes the marker; different session or no marker gives nothing and keeps the marker; the second prompt gives nothing. `tests/test_hooks_json.py` is not edited (it pins no UserPromptSubmit entry); it is run and must stay green.
7. Technical: no network, no herdr, no subprocess; Windows-safe (path joins via `pathlib`, UTF-8, LF); `tests/test_windows_safe.py`, `tests/test_utf8_helpers.py`, `tests/test_instructions.py` green and quoted.
8. SAFETY: other squads' agents are live (guardian-* in wpw). Check only with a fake herdr on PATH or a scratch squad in a mktemp -d dir. Never run the real herdr, squad-watchdog tick/run/ensure, squad-respawn or squad-spawn against this repo's squads or any live name. (this ticket needs no herdr at all: a hook run with stdin and a temp dir.)

## Not in this ticket
Writing the marker (01), the watchdog (03), rules (04).

Rules for this ticket: CLAUDE.md surgical changes, no slop; test economy (one test per AC risk, no matrices, extend existing test files, existing tests keep passing, none newly skipped); ADR 0011 (no new shell-only dependency: the same helpers as the other tools).
