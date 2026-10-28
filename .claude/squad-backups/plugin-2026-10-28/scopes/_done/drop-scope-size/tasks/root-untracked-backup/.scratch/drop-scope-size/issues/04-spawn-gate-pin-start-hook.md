# 04 Spawn gate, pinned engine or hand-off, start, hook

Status: ready-for-agent
Type: task
Blocked by: 03
Design task: tech 03 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Spawn gate, pinned engine or hand-off, start, hook, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`bin/squad-spawn` (:111-118 gate, :159 pinned engine / hand-off), `bin/squad-respawn`, `bin/squad-start:367`, `bin/squad-log-message:36-70`; tests `test_squad_spawn.py`, `test_squad_respawn.py`, `test_squad_start.py`, `test_squad_log_message.py`, `test_squadruntime.py`

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

### Specific (design 03)
03: pinned test: a fixture pin below 0.6.0 whose rule files still say `when: size = S` and whose `scope.md` says `size:` is spawned and respawned from the PO shell by the pin's own `squad-spawn`/engine (D7; AC 20; when the pin's runtime lacks the file the spawn is refused with a warning and nothing is created); gate: role not on team exits 1 with the role and `scope.md` named, `qa-whitebox` gated on `qa-white` (AC 6); undecided team refuses every non-Manager role (AC 15); an unpinned scope still on `size:` is refused with the converter pointer (never composed); the 3-returns hook notice goes to Team Lead iff `team-lead` in team, to Manager otherwise and on error or a `size:` scope (AC 12); order of refusal preserved (nothing created on refusal). **Amended (REV-7):** (C2) test runs a `size:`-only home through `squad-process team` and `squad-spawn` and sees the refusal. (C3) Pin boundary table, one test each: pin `0.5.2` -> hand-off to the pin's `squad-spawn`/`squad-respawn`; pin `0.6.0` -> new gate, no hand-off; no pin line -> unpinned path; malformed `plugin:` line (`read_home` raises) -> refuse naming the line. Hand-off happens once (a pinned 0.5.x runtime hands off nothing; guard stated in code, no exec loop). Runtime missing `bin/squad-spawn`: non-zero, warning, nothing created (a stub records worktree, label and herdr calls; none made). AC 20 byte-identical: the fixture `scope.md` is unchanged by `squad-spawn`, `squad-respawn`, the converter (dry run and apply) and `squad-team`; the composed text of the pinned fixture equals a golden generated from base sha 2949573, not hand-written. Both entry points (`squad-spawn`, `squad-respawn`) from the PO shell and from an agent session (`SQUAD_NAME` set). G7 bash-caller test lives here. (S4) Reader inventory handled here for `bin/squad-spawn:111-118`, `bin/squad-log-message:43`, `bin/squad-start:367`. QA whitebox runs a live respawn on a copy of this squad (pinned 0.5.2, `size: L`) after the task (REV-5b).

### Ticket extras
Extra AC (D7, design AC 03): pinned runtime missing `squad-spawn` -> refuse with a warning, no fallback, nothing created.

Spec AC added (BA, 1-31 agreed): AC 30 (spawn side): same `team:` line makes `squad-spawn` fail non-zero naming line and token. No `squad-team set`: the Manager edits `scope.md` for the first `team:`.

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

## Comments
