# 05 Rules: new `teams.md` + `sizes.md`

Status: ready-for-agent
Type: task
Blocked by: 02
Design task: tech 04a in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Rules: new `teams.md` + `sizes.md`, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
new `templates/squad/process/teams.md`, `sizes.md` (43 rules), `_removed.md` (append), changelog v9 IDs; tests `test_sizes.py`, `test_manager_m_l.py`, `test_qab_optional.py`

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

### Specific (design 04a)
04a: for each of 128 teams x roles, no composed Manager/Team Lead/BA text names an absent role as actor (extends `test_manager_text_names_no_absent_role_as_actor`); Done text reads "every checker on the team"; the Manager proposal rule has a row for every role (AC 1); the word "size" is absent from the composed Manager text. **Amended (REV-7):** (C7) one table-driven test over `DUTIES`: per duty fact and value, `who <rule>` lists exactly the acting roles; four named shapes (both QAs, qa-white only, qa-black only, no QA) assert the hand-in target (AC 12), who checks `## Behaviour` (AC 13), that a task with qa-white PASS and no qa-black PASS is not Done in the both-QAs text (AC 14), and that the no-QA shape has the Manager confirm `evidence.md` and `## Review`. Lives in 04a for the SIZE/TEAM files and is extended by 05 for lifecycle/review/evidence. (S3 part) PROMO-8 text, if touched, checks edits against `promote.md` and nothing undecided.

### Ticket extras
Extra AC (R9): `qa-b` -> `qa-black` in every `when:` of these files (23 lines across `sizes.md`, `review.md`, `lifecycle.md`, `evidence.md`, `spawning.md`).

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

## Comments
