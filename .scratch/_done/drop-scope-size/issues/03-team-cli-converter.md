# 03 `squad-process team` CLI and converter (migration path)

Status: ready-for-agent
Type: task
Blocked by: 02
Design task: tech 02 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
`squad-process team` CLI and converter (migration path), inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`bin/squadrules_cli.py`, `bin/squad-process` dispatch, `bin/squadadopt.py`, `bin/squad-migrate:77-190`; tests `test_squadadopt.py`, `test_squad_migrate.py`, new `tests/test_team_cli.py`

## AC
Amended (REV-7) AC govern where they differ from older text. Source: `$SCOPE_DIR/tasks/tech-design.md` rev 3 (design id in the line). Business AC: `$SCOPE_DIR/tasks/spec.md`.
**I8 (`design: yes` + `qa-b: no`): written on recommendation (a): valid team, converter accepts it. PO has not answered; Manager sends `DECISION 03` if (b). Do not start 03 without the Manager's go (wave 2).**

### Global
G1 Tests for every behaviour the task changes exist and pass; the task's `grep -rl '<touched path or string>' tests/` hits all run green (CLAUDE.md).
G2 `squad-process lint` clean (no new warnings) on the task branch.
G3 Conforms to `architecture.md` (SIZE-23d): sections named in the ticket; any difference is a finding.
G4 No `size` word added to rule text; no rule block acts on a role absent for any valid team (from 04a on, enforced by the 128-set test).
G5 Rule retargets keep their ID unless the body changed; tombstones carry `why:` and `replaced_by:`; changelog v9 lists every changed ID with a reason (>10 chars).
G2b Baseline: the ticket records `squad-process lint` output on its base sha; the branch output is diffed against it, no new line (S1).
G6 Python stdlib only; no new dependency; files stay UTF-8, LF in writes, CRLF-tolerant reads (`squadio`), no shell-only path logic that breaks on Windows (tests `test_windows_safe.py`, `test_crlf_squad_files.py` pass).
G7 Security and robustness (C9): `squad-process team` prints only tokens from the fixed set (`TEAM_KEYS`, `none`, `undecided`); `--has` is validated against `ROLES` (unknown role exits 2); bash callers quote the value and never `eval` or word-split it (`read -r`/`case`, test with a hostile `team:` value such as `qa-white; touch X` and `$(...)`, asserting nothing runs); no value read from `scope.md` reaches a shell unvalidated. Test in 02 (CLI) and 03 (bash callers).

### Specific (design 02)
02: `squad-process team` output for a `team:` home and `--has` exit codes (role names mapped by `ROLE_KEY`); `--from-size` does not exist; converter (`squad-process adopt`, its dry run also lists the `scope.md` conversion beside the `process.md` one; dry run is the default) lists each `scope.md` and changes nothing and names skipped pinned scopes; a blank `size:` becomes a blank `team:`; the engine's error for an old-format home (any of the four lines, with or without `team:`) names file and line and `squad-process adopt` (constraint 11); apply writes a backup and the `team:` line (token mapping per D3: S none; M qa-white, qa-black, no qa-black when `qa-b: no`; L all but designer/architect; flags add theirs), removes the four lines, is idempotent (second run no change), covers the real samples of 01 (`size: M (confirmed ...)`, blank `size:`, `qa-b: no  (...)`) on a copy of `plugin-bk261023`; `squad-migrate` writes a `team:` from a `scopes.md` row with `S`, `M`, `L`, and none; **amended (REV-7):** (C2) the old-format error text is one shared function, tested directly here and in 03; the scaffold (D1) is not reachable from `squad-process team`: a `size:`-only home through `squad-process team --home` exits 2 with the converter pointer while the same home still composes via the scaffold parameter; the end-to-end `compose` exit 2 is task 10's. (C4) The converter takes the first token; when commentary contradicts the mapping (custom pod, `no QA roles`, `qa: none`) the dry run prints the commentary beside the proposed team and flags it `check`, never drops it; `design: yes` + `qa-b: no`: valid team if the PO answers I8(a), converter refuses with the reason if (b) (state in the ticket which one the PO chose). (C5) Rollback and safety: restoring the converter's backup gives a byte-identical `scope.md` and the 0.5.2 pinned fixture composes it; apply on a home with both `size:` and `team:` is an error naming both lines, nothing written; second apply is a no-op with no second backup; CRLF `scope.md` keeps CRLF; atomic write (a kill between backup and write leaves the original, tested by an injected failure); converter writes only inside the squad folder (a symlinked scope is refused). Dry run and apply on a copy of `plugin-bk261023` and of the blueprint squad (live data, REV-5b; QA whitebox re-runs); the byte-identity of pinned scopes: `scope.md` unchanged by the converter (dry run and apply). `size: M` + `qa-b: no` converts to `team: qa-white` (spec AC 22); a converted copy of `plugin-bk261023` composes for every role with no error and the owners per duty equal those of its old size (spec AC 28, expected table from 01).

### Ticket extras
Extra AC: spec AC 22, 28 with design AC 02: a converted copy of `plugin-bk261023` composes for every role, and owners per duty equal the old size's.

Spec AC added (BA, 1-31 agreed): AC 21/22 variants: `size: L` + `qa-b: no`, `size: S` -> `team: none`; `squad-process upgrade --check|--apply --yes`.

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

## Comments
