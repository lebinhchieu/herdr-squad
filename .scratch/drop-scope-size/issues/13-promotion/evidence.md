# Evidence: 13 Promotion (plugin 0.6.0)
sha: cf3b5c0
## Behaviour
- Promoted per `promote.md` (copy: `.scratch/drop-scope-size/promote.md`): ADR 0018 in `docs/adr/` (accepted; "Overrides" line names ADR 0016 Sizes/Duty owners and ADR 0017 sentence and flags; 0016 and 0017 each got an "Amended by 0018" line), `CONTEXT.md` (Size and the design/architecture flag entries gone; Team, Duty owner, Checker added; keys `qa-white`/`qa-black`, QA term kept), `README.md` (team proposal, 0.6.0 breaking note with converter path), changelog v9 header + snapshot line + text, snapshot `history/process-v9/` (byte-equal to `templates/squad/process/`), `.claude-plugin/plugin.json` 0.6.0, `_removed.md` tombstones all carry `why:` and `replaced_by:`.
- `process-version: 6` in the retired monolithic `templates/squad/process.md` is left alone (ADR 0016 retired the integer). The "version in four places" check is plugin.json, changelog v9 text, README and the snapshot line; one test compares them. Flagged for the Tech Lead in the HANDIN.
- Size-word checks (C1, `(?i)\bsize\b(?!-\d)`): `templates/squad/process` outside `_removed.md`: 0 hits; README, CONTEXT, agents, skills (outside history/changelog): 0; `bin/` and `hooks/`: per-file count allow-list in `tests/test_promotion_0_6_0.py` (same classes as ticket 12: converter, migrate, report display, pinned-runtime text, `fs.stat` size). `qa-b\b` in rules: only the reviewer file name `qa-b.md` (evidence.md 3, files.md 1, review.md 1), checked by the test.
- F1: `squad-spawn` refusal for a role not on the team now says who adds it (designer/architect: PO confirms, then `squad-team add`; others: the Manager runs `squad-team add`); old "only the PO adds the designer or architect" gone. Test `test_refusal_text_names_who_adds_the_role` (test_squad_spawn).
- F3 is listed in `promote.md` open items, no rule change, no changelog row. The `qa-b\b` needle in CutoverTest was already raw (fixed in c768b94, non-vacuous: matches lines in `bin/squadcompose.py`). Branch cut from 59e2741, merged 17b88b9 (evidence only).
- Changelog v9: this ticket changes no rule block (`git diff 59e2741 -- templates/squad/process` is empty), so no ID rows added; header, snapshot line and summary text only.
- Final `--tz` run (receipt `/tmp/tmp.Dspha7Qs23`): all files green except 2 flakes, both green on rerun alone: `test_squad_report_cli` (report.html timestamp crossed a second boundary between two builds) and `test_squadinbox.test_no_pyc` (stray `bin/__pycache__` from a parallel run; removed, 55 tests OK).
- Lint baseline (G2b): `squad-process lint` on base 59e2741 empty, exit 0; on branch empty, exit 0.
- Tests: 598 tests in every `tests/` file matching CONTEXT.md, README.md, plugin.json, changelog, docs/adr, history/, process-v, 0.5.2, "not on the team" (goldens included) green; `test_squad_spawn` 88 green; new `tests/test_promotion_0_6_0.py` 10 green. Final `--tz` suite: see receipt in HANDIN.

## QA whitebox

### 13 Promotion QA whitebox (HANDIN cf3b5c0, code 4dde33e) — pre-check CLEAN, verdict pending Tech's final sha
- PROMO-8: ADR 0018, 0016/0017 "Amended by 0018" lines, CONTEXT.md (Team/Duty owner/Checker added, Size gone, qa-white/qa-black), README 0.6.0 note, changelog v9 header + snapshot line, plugin.json 0.6.0: all match `promote.md`; nothing undecided. ADR 0018 states what it overrides (0016 Sizes/Duty owners; 0017 sentence + flags). F3 listed as open item in promote.md; no rule/changelog change.
- Snapshot `history/process-v9/` byte-equal to `templates/squad/process/` (diff -rq empty).
- AC 11 greps (`(?i)\bsize\b(?!-\d)`): rules outside _removed.md 0 hits; README/CONTEXT/agents/skills 0; bin/hooks hits are per-file-count allow-listed in tests/test_promotion_0_6_0.py (converter, migrate, report display, fs.stat false positives); `qa-b\b` in rules only `qa-b.md` file name.
- Deviation (non-blocking, Dev flagged): AC says 0.6.0 in `process-version`; `process-version: 6` left unchanged — bin/squadprocess.py:16 only accepts a positive integer and ADR 0016 retired it. Four-way check is plugin.json / changelog / README / snapshot line. Tech to confirm it accepts this.
- Allow-list lives in the test (per-file counts) with reasons in evidence.md, not file:line in the ticket as AC says; same shape Tech accepted on 12.
- F1 spawn refusal text names who adds the role (designer/architect: PO confirms first, then squad-team add); test in test_squad_spawn.
- SIZE-22 equality: duties lines of the six shapes (S, M, L, L-no-QB, M+designer, M+architect) re-composed; owners equal the base SIZE-22/22a table (code check at S = Manager per tech-design, accepted in task 01).
- Lint 0. Tests (git-initialised archive of cf3b5c0): promotion, spawn, respawn, compose, inventory, sizes, dev_rules_size, upgrade, squadrules, process_conversion, squadprocess: 380 OK, 2 skips.

## QA blackbox

### QA blackbox, task 13 promotion (HANDIN cf3b5c0, code 4dde33e)

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

## Tech Lead review

- TL final: full --tz suite on cf3b5c0 OK (suite-default.txt, suite-tz.txt; first line sha cf3b5c0 clean=yes). Accepted deviation: process-version stays integer 6 (ADR 0016 retired the line; squadprocess.py accepts only int); 0.6.0 four-way = plugin.json/changelog/README/snapshot. Final sha cf3b5c0 (code 4dde33e).
