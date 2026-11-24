# 04 integration of 02 + 03 and promotion (ADR 0029)
Status: ready (waits for 02 and 03 passed)
Duties: plan-owner=team-lead, design-notes=tech-lead, tech-ac=tech-lead, business-ac=ticket, code-check=qa-white, behaviour-check=qa-black, ui-check=qa-black, handin-target=qas, suite-owner=tech-lead, promote-owner=tech-lead, risk-owner=tech-lead, doubt-owner=manager, choice-owner=tech-lead
Files: docs/adr/0029-watchdog-counts-a-background-shell-as-work.md (new), .scratch/watchdog-shell/issues/04-integration-and-promotion.md (new), merge of 02 and 03 (no other file)
Goal: `../iterations/2.md`; ADR wording `../promote.md` (the fenced block). Integration by SQ-6b / GOAL-6b: 02's hook writes the herdr token, 03's watchdog reads it; they share no file, so the risk is the contract, and this task checks it with real herdr output once.

Start: branch from 02's passed sha (`--base`), then merge 03's passed sha. First commit (FILE-11): copy `$SCOPE_DIR/tasks/04.md` to `.scratch/watchdog-shell/issues/04-integration-and-promotion.md` (02 already added 02 and 03 there). Hand in to both QAs.

## Design notes (Tech Lead)
- No code is written. The merge must be clean: `git diff --name-only <base>..<02 sha>` and `<base>..<03 sha>` share no path (expected: both empty intersection; 02 holds `hooks/` and its tests, 03 holds `bin/`, `README.md`, `plugin.json`, `changelog.md` and its tests). A conflict or an overlap is `BLOCKED 04`, not a patch.
- ADR text: take the fenced block of `promote.md` verbatim, then check every sentence of it against the merged tree and fix what the build changed (names, texts, defaults). Facts to verify: hook location and the two wirings in `hooks/hooks.json`; `TTL_MS=3600000`; `SQUAD_WATCHDOG_BG_MAX` default 60 and `0` = off; the two log lines `bg busy:` and `bg cap:`; `states_text` shows `<name> busy (bg shell)`; plugin 0.9.6 and changelog v19. A fix to the ADR is also made in `promote.md` wording by telling the Tech Lead in the HANDIN (the Tech Lead edits `promote.md`; the Developer never writes it). Use the `/domain-modeling` skill rules for ADR files (project.md): number `0029` is free on base (last is `0028`); status line, Context, Decision, Consequences.
- The ADR does not contradict 0028 or 0022 (it extends both; their text is not edited).
- No glossary change, no `CONTEXT.md` edit.

## Technical AC
1. Merge: `git log --merges -1` shows the merge of 03's sha; `git diff --stat <02 sha> HEAD` lists exactly 03's files plus the ADR and the ticket copy; nothing else.
2. Targeted tests on the merge result, outputs quoted in `## Behaviour`: `test_hooks_json`, `test_herdr_bg`, `test_squad_watchdog`, `test_squadboard_agents`, `test_squad_start`, `test_squad_log_message`, `test_squadtask`, `test_squadboard_inbox`, and the SQ-10 trio `test_windows_safe`, `test_utf8_helpers`, `test_instructions`. No new skip. (The full `--tz` run is the Tech Lead's, after Chieu says yes.)
3. Live contract check (one pass, real herdr output, no Claude session needed). From the Developer's own pane (`HERDR_ENV=1` and `HERDR_PANE_ID` are set there), with a temp state dir and a temp tasks dir:
   - a. `export HERDR_BG_STATE_DIR=<tmp>/state HERDR_BG_TASKS_GLOB='<tmp>/tasks/%s/tasks'`; create `<tmp>/tasks/s1/tasks/b1.output` empty; run `printf '{"session_id":"s1","tool_name":"Bash","tool_input":{"command":"sleep 300","run_in_background":true},"tool_response":{"backgroundTaskId":"b1"}}' | hooks/herdr-bg hook` from the merge result.
   - b. `herdr agent list > <evidence>/live-bg-present.json` shows the Developer's own row with `"tokens":{"bg":"⏵ 1 shell"}` (quote the row in `## Behaviour`).
   - c. Make a scratch home (a temp dir shaped like `scopes/s1` with `roster.md` listing the Developer's agent name live, `goals.md` one row `in progress`) and run `bin/squad-watchdog tick --home <scratch> --manager <name> --now <t>` through `--herdr-json <evidence>/live-bg-present.json` at `t` and again at `t+10min`: its `watchdog.log` has one `bg busy: <name> has a background shell (⏵ 1 shell); counted as working for at most 60 min` and no `idle start`, and no nudge was sent (`send` stub or `SQUAD_WATCHDOG` off: use `tick` with a stub that records; do not message a real Manager).
   - d. Append `[exited with code 0]` to `b1.output`, run the Stop payload `printf '{"session_id":"s1","hook_event_name":"Stop"}' | hooks/herdr-bg hook`; `herdr agent list > <evidence>/live-bg-cleared.json` shows the row without `tokens`; a tick on that file logs `idle start` listing `<name> idle`.
   - e. Cleanup (SAFE-3): the token is cleared by (d); run `herdr pane report-metadata "$HERDR_PANE_ID" --source herdr-bg --clear-token bg` once more to be sure; remove the temp dirs; unset the env vars. The saved JSON files are the evidence (REV-4: both shapes, from the real tool).
4. ADR: `docs/adr/0029-watchdog-counts-a-background-shell-as-work.md` exists; `diff` against the `promote.md` block names every change made after step "verify" above; a `grep` check of each fact in the verified list is in `## Behaviour` (command and hit).
5. `grep -rn "0\.9\.5" .claude-plugin/` is empty and `.claude-plugin/plugin.json` says `0.9.6` on the HANDIN sha (03 did the bump; this task only checks it).
6. The HANDIN names one sha. After it, the Tech Lead runs the three SQ-10 files and asks Chieu for the full suite.

## Dry-run on base 804c29c (SQ-15)
- `ls docs/adr/0029*` is empty and the last ADR is `0028` (AC 4 fails on base as it must; numbering free).
- The test files of AC 2 other than `test_herdr_bg` pass on base (71/9/4/49/25/15/12/14/14/16 tests OK; `test_herdr_bg` does not exist yet). The live check (AC 3) cannot run on base: no hook, no `bg busy:` line.
- Known failing on base: none.

## Deploy plan
Same as 02 and 03 (their tickets): merge, update plugin to 0.9.6, restart live sessions, then Chieu removes the 2 `herdr-bg hook` lines from `~/.claude/settings.json`. This task adds docs only.

## Evidence
`evidence.md` next to this ticket (EVID-1): `## Behaviour` with test output, the live-check commands and rows, the two saved JSON files (`live-bg-present.json`, `live-bg-cleared.json`) in `$SCOPE_DIR/evidence/04/`.
