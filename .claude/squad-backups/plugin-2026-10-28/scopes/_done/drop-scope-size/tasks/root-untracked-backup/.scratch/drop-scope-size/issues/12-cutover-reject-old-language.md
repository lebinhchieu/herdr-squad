# 12 Cutover: engine rejects the old language

Status: ready-for-agent
Type: task
Blocked by: 04, 05-11
Design task: tech 10 in `$SCOPE_DIR/tasks/tech-design.md` (read its Decisions D1-D8 and the section for this task)

## What
Cutover: engine rejects the old language, inside `architecture.md` (Status: final; E4: keys `qa-white`/`qa-black`, no shim). One Developer session; commit to your branch, hand in to QA whitebox and QA blackbox.

## Files you touch (nobody else touches these in parallel)
`WHEN_KEYS` drop `size`, `qa-b`; compose/lint errors for `size:`, `design:`, `architecture:`, `qa-b:` in `scope.md` and old `when:` keys with converter pointer; non-Manager undecided error; delete D1 scaffold and `who_lines` size lines; `squadupgrade.py` overlay hint; delete size-keyed fixtures. Files: `bin/squadrules.py`, `bin/squadcompose.py`, `bin/squadupgrade.py`, `tests/rulesview.py`, `tests/test_squadrules.py` lint cases, `tests/fixtures/rules/*/templates/squad/process/review.md` (both use `when: qa-b = no and size = S`), `tests/test_process_conversion.py` (line 76 size sweep)

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

### Specific (design 10)
10: `size`, `qa-b` or `qa-whitebox` in a plugin rule or overlay `when:` is a lint and compose error naming the rule and the new key (AC 11); `size:`, `design:`, `architecture:` or `qa-b:` in an unpinned `scope.md` is a compose error naming the file and `squad-process adopt`, exit 2; no `read_home` path derives duty facts from `size` (test greps the module and runs a `size:` home); this test is a permanent suite test, so the final `--tz` run on the integration sha fails if the scaffold survives; lint rejects a `when:` with two role/duty keys; non-Manager compose on an undecided home exits 2; the size-keyed fixtures and size lines of `who_lines` are gone; `squad-process upgrade` lists an overlay op with `when: size = L` or `qa-b = yes` with a suggested translation and writes nothing (AC 21). **Amended (REV-7):** the scaffold test greps `bin/squadcompose.py` for the `size` path and the `legacy_scaffold` parameter and runs a `size:` home through `compose` expecting exit 2 (permanent). Single-key and value-set lint already exist since 01 (C6): 10 only adds the old-key rejections (`size`, `qa-b`, `qa-whitebox`), tested over every `when:` in plugin rules and overlays and the `team:` token rejection; `who` and `lint` help text name the new key. (S4) Reader inventory: `git grep -nE "size:|'size'|\"size\"|qa-b\b" -- bin hooks agents skills ':!skills/*/history'` returns only an allow-list in the ticket (file:line, reason: converter mapping, migrate input, report display); covers `bin/squad-spawn:111-118`, `bin/squad-log-message:43`, `bin/squadrules_cli.py:109`, `bin/squad-start:367`, `bin/squadcompose.py:190,219-227`.

### Ticket extras
Extra AC: lint rejects a `when:` with two role/duty keys; non-Manager compose on an undecided home exits 2; permanent test that no `read_home` path derives facts from `size` (Manager's condition for the scaffold).

Spec AC added (BA, 1-31 agreed): AC 21: `squad-process upgrade --check` prints `qa-b = no -> qa-black = no` and `size = L -> ba = yes` for overlay rules, files byte-identical after `--check`; `--apply --yes` is the only writer. AC 29: `grep -iw size` over PO-visible output (`squad-start`, `squad-spawn`, `squad-process who`, Manager proposal, new `scope.md`) has no hit except the legacy-squad error (AC 26), converter output (AC 22) and overlay report (AC 21); reword any other hit (e.g. "file size").

Before HANDIN: `squad-process lint` (record the base-sha baseline in this ticket, G2b); `grep -rl '<touched path or changed string>' tests/` and run every hit (CLAUDE.md). Tech Lead names the final sha; QAs verdict on it.
Changelog v9: append your changed rule IDs (D8).

Added (Tech DECISION): un-skip the two 5 KiB dev-rules tests (skip reason 'ticket 11'); no skip with that reason remains at cutover (grep).
Ticket 12 also owns the `legacy_scaffold` removal.
Mirror: at cutover `grep -rn "ticket 11" tests/` finds no skip.

## Comments
