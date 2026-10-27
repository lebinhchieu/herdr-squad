# 13 Promotion

Status: ready-for-agent
Type: task
Blocked by: 12
Design task: tech 11 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Promotion, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
ADR 0018 from `$SCOPE_DIR/tasks/adr-0018-team-replaces-size.md` to `docs/adr/`, `CONTEXT.md` (Size removed; Team, Duty owner chain, Checker; keys `qa-white`/`qa-black`, QA term kept), `README.md`, changelog v9 text, snapshot `history/process-v9/`, `_removed.md` tombstones final check, `.claude-plugin/plugin.json` 0.6.0, `process-version`, commit `.scratch/drop-scope-size/spec.md` and tickets. Follows PROMO-5 and `project.md` rules (`/domain-modeling`). Final `--tz` run.

## AC
Amended (REV-7) AC govern where they differ from older text. Source: `$SCOPE_DIR/tasks/tech-design.md` rev 3 (design id in the line). Business AC: `$SCOPE_DIR/tasks/spec.md`.

### Global
G1 Tests for every behaviour the task changes exist and pass; the task's `grep -rl '<touched path or string>' tests/` hits all run green (CLAUDE.md).
G2 `squad-process lint` clean (no new warnings) on the task branch.
G3 Conforms to `architecture.md` (SIZE-23d): sections named in the ticket; any difference is a finding.
G4 No `size` word added to rule text; no rule block acts on a role absent for any valid team (from 04a on, enforced by the 128-set test).
G5 Rule retargets keep their ID unless the body changed; tombstones carry `why:` and `replaced_by:`; changelog v9 lists every changed ID with a reason (>10 chars).
G2b Baseline: the ticket records `squad-process lint` output on its base sha; the branch output is diffed against it, no new line (S1).
G6 Python stdlib only; no new dependency; files stay UTF-8, LF in writes, CRLF-tolerant reads (`squadio`), no shell-only path logic that breaks on Windows (tests `test_windows_safe.py`, `test_crlf_squad_files.py` pass).
G7 Security and robustness (C9): `squad-process team` prints only tokens from the fixed set (`TEAM_KEYS`, `none`, `undecided`); `--has` is validated against `ROLES` (unknown role exits 2); bash callers quote the value and never `eval` or word-split it (`read -r`/`case`, test with a hostile `team:` value such as `qa-white; touch X` and `$(...)`, asserting nothing runs); no value read from `scope.md` reaches a shell unvalidated. Test in 02 (CLI) and 03 (bash callers).

### Specific (design 11)
11: AC 25; **(C1)** `-iw` matches the surviving `SIZE-n` IDs (288 hits today, 58 are IDs; measured on 2949573), so the check is `git grep -nP '(?i)\bsize\b(?!-\d)' -- templates/squad/process` and returns only `_removed.md`, changelog text and an explicit allow-list in the ticket (file:line, reason, non-scope use), and `git grep -n 'qa-b\b'` returns only the same; the same `\bsize\b(?!-\d)` grep over `README.md`, `CONTEXT.md` (Size entry gone; Team, Duty owner, Checker present), `agents/`, `skills/` outside `history/`, `hooks/`, and `bin/` (only converter/migrate/report-display hits, the same allow-list as 10) returns nothing else; **(S3)** PROMO-8 edits match `promote.md` and nothing undecided; version `0.6.0` identical in `plugin.json`, `process-version`, changelog header and README (one test compares the four); ADR 0018 states where it overrides ADR 0016/0017 (CLAUDE.md domain rule); snapshot equals the rule folder (if a test pins it); full suite with `--tz` passes on the integration sha.

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

### Spec AC added (BA, 1-31 agreed)
AC 29 re-checked on the final integration sha; AC 9, 10, 24, 25, 28 are proven by the `--tz` suite receipt (QA whitebox asserts exact SIZE-22/22a equality).

## Comments

Dev (13): lint baseline on base 59e2741: `squad-process lint` empty, exit 0. Branch: empty, exit 0.
