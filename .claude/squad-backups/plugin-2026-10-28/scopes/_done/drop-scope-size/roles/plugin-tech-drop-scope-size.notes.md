# plugin-tech-drop-scope-size notes

## Now
- Design final: tasks/tech-design.md rev 3, architecture.md final. Plan iterations/1.md, tickets .scratch/drop-scope-size/issues/NN-*.md. TL=plugin-tl-drop-scope-size, QAW=plugin-qaw-..., QAB=plugin-qab-...; Devs plugin-dev-dsz-NN.
- DONE (tech accept + both QA PASS): 01-12, 14, INT1-INT4. 12 final 59e2741 (live run L done by Manager, evidence/L/manager-run.md; F1 folded into 13, F3 follow-up in promote.md, F2 fixed by 0.6.0).
- 13 DONE: final sha cf3b5c0 (code 4dde33e), my --tz receipt evidence/13 OK, QAW + QAB PASS, PASS 13 sent to TL (relay to Manager). All tasks done; nothing open except answering fresh events from notes (COST-13b: no respawn).
- Deploy plan written: $SCOPE_DIR/tasks/deploy-plan.md (LC-13); tell Manager its path in the 13 pass message (PO runs it).

## Open threads
- My design numbers vs ticket numbers: 01a/01b=01/02, 02=03, 03=04, 04a=05, 04b=06, 05=07, 06=08, 07=09, 08=10, 09=11, 10=12, 11=13.
- Per final sha: Dev evidence-only commit, `squad-evidence check <folder> --base <code sha>` exit 0 from the Dev worktree (.worktrees/plugin/drop-scope-size/plugin-dev-dsz-NN, integration: plugin-dev-dsz-int4). Code+evidence in one commit fails the check (ask for evidence-only commit on top). INT tickets: the new ticket .md is flagged outside evidence folder only if in the evidence commit; accepted shape.
- REV-3: name the final sha (DECISION) to QAW + QAB + Dev + TL; QAB/QAW each give one verdict on that sha. Review notes in $SCOPE_DIR/evidence/NN/tl-review.md (append a line each time).
- Suite: only I run it. Integration worktree: `python3 tests/run_suite.py --receipt $SCOPE_DIR/evidence/<INT> --if-changed <prev integration sha>` via Bash run_in_background (NOT a nested `&` subshell, it dies); wait for the notice; delete stale `bin/__pycache__` first. Never pgrep -f / pkill. Rerun only after committing fixes. Final: `--tz` after 12 (scaffold gone or --tz fails).
- A tool denial: creating a /tmp worktree to test a merge was denied; don't retry or ask peers.
- ADR 0018 draft is the Architect's (tasks/adr-0018-team-replaces-size.md); I add technical consequences at 13.
- Advisor was overloaded once (LC-26 note skipped); retry before final sha / irreversible choice.
- Forward notes: 12 wires old_format_error into read_home; converter skips pinned scopes and `_done`; QAW 03 notes.
- rtk hook compacts git diff output: use `rtk proxy git diff ... > /tmp/x.diff` then Read it.

## Decisions that bind later work
- D1 no shim in release; branch-internal scaffold (size: home -> duty facts via legacy_team) approved by Manager FINAL on conditions: deleted in ticket 12 with a permanent test; merged sha has no size: path (full suite --tz).
- D2 prefix TEAM / teams.md, SIZE-n IDs stay. D3 TEAM_KEYS/ROLE_KEY/DUTIES/legacy_team in squadrules.py; tokens and duty values qa-white/qa-black. D5 team header only manager/team-lead/tech-lead. D7 pinned scope <0.6.0: hand-off to pin's squad-spawn/respawn, refuse with warning if runtime lacks it, no fallback. D8 changelog v9 block, a row per changed rule (QAW checks every changed ID has a row and "same duty" is true).
- I8 = (a) by PO: converter in 03. Converter dry run default, adopt needs --yes; skips pinned scopes; old-format home errors name file/line and `squad-process adopt`.
- Rule IDs kept live with new bodies (05): SIZE-1, SIZE-2, SIZE-13, SIZE-14, SIZE-22, SIZE-21a. Tombstoned in _removed.md: SIZE-3, 3a, 4, 6d, 12, 15 (->TEAM-7), 19, 20 (->TEAM-1), 21b, 22a (->SIZE-22).
- 11: REV-5a and EVID-5 are on demand (`roles:` empty, lint allows empty value, line must exist); AC 24: all 128 team sets <=5120 B Developer file, no pins.
- 14: qa-blackbox Read deny removed; rm/rmdir of /tmp/tmp.* allowed in role settings (team-lead too); matcher bypass asks for .., $, backtick.
- A task that makes a test stale fixes it (no known-red files left). Lesson: 14 missed test_team_lead_perms; 'grep -rl' hits must all run.
- Lesson: never rule across a business AC (spec.md) in a technical decision; check spec first. Lesson 11: read for duty loss (a "same duty" changelog claim) and check every changed rule ID has a changelog row.

## Pointers
- $SCOPE_DIR/architecture.md, tasks/spec.md (BA, AC 1-31), tasks/tech-design.md, tasks/tech-feasibility.md, iterations/1.md, roster.md, evidence/NN/tl-review.md.
- Real scope.md samples: `.claude/squads/plugin-bk261023/**/scope.md`.
