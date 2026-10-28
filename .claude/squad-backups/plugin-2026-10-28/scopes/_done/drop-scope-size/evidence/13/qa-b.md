# QA blackbox, task 13 promotion (HANDIN cf3b5c0, code 4dde33e)

Method: `git clone` of the branch into a scratch dir (cf3b5c0) and `git archive`; CLI only. `tests/test_promotion_0_6_0.py` needs a git checkout (`git grep`): 10 OK in the clone, 2 failures in a bare archive (not a finding).

| AC | What I did / saw | Result |
|---|---|---|
| 25a | `CONTEXT.md`: `grep -n '\*\*Size'` 0 hits; `**Team**` (l.80), `**Duty owner**` (l.84), `**Checker**` (l.88) present; `grep -iw size CONTEXT.md` 0 hits; QA term kept, keys `qa-white`/`qa-black` | PASS |
| 25b | `docs/adr/0018-team-replaces-size.md`: accepted, "Overrides" names ADR 0016 Sizes/Duty owners and the ADR 0017 sentence; 0016 and 0017 carry an "Amended by 0018" line | PASS |
| 25c | v9 block `removed:` has 14 IDs (SIZE-3, 3a, 4, 6d, 12, 15, 19, 20, 21b, 22a, LC-20c, REV-14b, REV-14c, REV-19); `templates/squad/process/_removed.md` has a `(removed in v9)` tombstone with `replaced_by` for each of the 14; every `replaced_by` target exists (`squad-process rule`: SIZE-1, SIZE-6c, SIZE-22, TEAM-7, SIZE-21a, LC-20a, REV-14a, REV-19b, TEAM-1) | PASS |
| 25d | `skills/squad-process-update/changelog.md` starts with `## v9 — 2026-10-28`, snapshot line, added/changed/removed lists; `history/process-v9/` is identical to `templates/squad/process` (`diff -r`) | PASS |
| 25e | `.claude-plugin/plugin.json` version 0.6.0; README states 0.6.0 (breaking) with adopt/upgrade steps and ADR 0018; the version test compares all places | PASS |
| 24 | Sweep of all 128 teams x goal yes/no x qa full/light (512 composes of the Developer): 0 failures, max 5034 bytes (team-lead, tech-lead, qa-black, designer, architect; goal yes; light), 0 over 5120 | PASS |
| 29 | `squad-spawn`, `squad-start`, `squad-team`, `squad-respawn`, `squad-process who --help`: 0 whole-word "size"; new spawn refusals checked below | PASS |
| F1/F2 of 12 | Spawn refusal now: architect/designer "the PO confirms adding the architect first, then the Manager runs squad-team add"; tech-lead, team-lead, qa-blackbox "the Manager adds the X with squad-team add". Old "only the PO adds" text gone. The suggested `squad-team add qa-blackbox` and `add tech-lead` run (rc 0) | PASS |
| lint | `squad-process lint` empty, rc 0 | PASS |
| rules unchanged | `git diff 59e2741 cf3b5c0 -- templates agents hooks` empty; only `bin/squad-spawn` (refusal text) changed in code, so the ticket-12 results (AC 9, 11, 20-23, 26-28, 30) stand | PASS |
| 10 | Read Tech Lead receipt (SUITE-6) `suite-default.txt`: sha cf3b5c00 clean=yes, Ran 1760 tests, OK; `suite-tz.txt` same sha clean=yes, no time files. Covers the final sha cf3b5c0 (TL DECISION 13) | PASS |

Notes (not findings): `process-version: 6` left in the retired monolithic `templates/squad/process.md` (ADR 0016 retired the integer), as the Developer flagged.
