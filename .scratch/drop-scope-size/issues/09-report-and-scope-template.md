# 09 Report and scope template

Status: ready-for-agent
Type: task
Blocked by: 02
Design task: tech 07 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Report and scope template, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`bin/squadreport.py:81,423,483`, `bin/squadreport_rollup.py:88`, `templates/report/report.js:97`, `rollup.js:103,151,178`, `templates/scope/scope.md` (`team:`, no old lines), `tests/report_fixtures.py`, `test_squadreport_*`, `test_squadreport_rollup_ui.py` (serve folder per `project.md`, stop by PID)

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

### Specific (design 07)
07: report renders a mix of old-size and team scopes without error (AC 23), including empty `size`/`team`; the old size is shown as written, nothing derives a team from it; browser test uses a served folder per `project.md`, server stopped by PID. **Amended (REV-7, C8; REV-6 payload shape):** every rollup scope row and every report `scope` object has both `team` and `size` keys (string, `""` allowed) for old, new, hand-made (no `team:` line), undecided and error rows; the rollup error rows that set `"size": None` (squadreport_rollup.py:200,206) get a matching `team` value (`None` stays consistent: test fixes one rule and asserts it on both keys). Browser test asserts the chip text for an old row (recorded size) and a new row (team).

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

## Comments
