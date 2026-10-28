# 11 Developer 5 KiB sweep and trim

Status: ready-for-agent
Type: task
Blocked by: 05, 06, 07, 08
Design task: tech 09 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Developer 5 KiB sweep and trim, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`tests/test_dev_rules_size.py` over 128 sets x goal x qa; trims in rule files touched by 05-08 (`aware:`/on demand)

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

### Specific (design 09)
09: for all 128 sets x goal x qa the Developer composed rules are <= 5120 B; the pinned exceptions table is deleted or pinned by team set and no larger than 5443 B; every duty a Developer acts on still present (existing "keeps every duty" test); on-demand rules reachable by `squad-process rule <ID>`.

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

Added (Tech DECISION): un-skip the two 5 KiB dev-rules tests (skip reason 'ticket 11'); no skip with that reason remains at cutover (grep).

Added (QAW INT3 note, Tech DECISION): four skipped tests carry "5 KiB trim is ticket 11" (`test_dev_rules_size` x3, `test_sizes` x1). Un-skip all four; today they fail (S 5196 B, M+arch 5124 B > 5120). The PINNED values are stale (real 5522/5521/5226/5225): re-pin or delete them per design 09. `grep -rn "ticket 11" tests/` returns no skip at HANDIN.

## Comments

- LC-7b (TL, 3 returns): cause = AC conflict (Tech pinned-exception ruling vs business AC 24, withdrawn) + 2 small QAW findings, not the Dev. AC stands, same Dev continues. Fix QAW F1 (changelog v9 lines LC-18, MSG-3, START-6, START-10, reason each) and F2 (restore REV-22a conformance clause), re-measure 512 combos <=5120. One more return goes to the Manager for a decision.
