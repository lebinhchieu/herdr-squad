# Evidence 01 architecture fact

## Behaviour
- `scope.md` `architecture: yes|no`, default `no`; bad value exits 2 naming `scope.md:<line>`.
- `squad-spawn architect` refuses (exit 1, `no 'architecture: yes' in scope.md; only the PO turns the architect on`) for `no`, `maybe`, absent line, absent file, `design: yes`, commented line; `yes` passes (dry-run shows `--agent squad:architect`). `model architect: opus high` accepted.
- `when: architecture = yes|no` accepted by lint (`maybe` refused), compose keeps/drops by fact; goal home defaults to `no` (rule with `= yes` dropped).
- Header prints `architecture yes` only when on; absent/no header byte-identical (decision in Design notes). No edit to any golden.
- `templates/scope/scope.md` carries `architecture: no`. `templates/squad/process/*` untouched (T9; `arch` short is task 02).
- T7: `grep -c designer bin/*` lists 9 lines before; every list has `architect` added (ROLES, usage, 2 role cases, model regex, ROLE_FILES, label).

## Red run (new tests on base code, `git archive` of base + new tests)
squadcompose 4 fail + 1 error (architecture default/bad value/goal home/when keep-drop/header), squadrules 3 fail + 1 error, squadadopt 1 fail, squad_spawn 14 subtest fails (full output: new tests in `SpawnArchitectTest`). Label test also asserts `ROLE_NAMES` has `architect`.

## Green run (unittest, one file at a time)
Touched: test_squadcompose 51, test_squadrules 55, test_squadlabel 19, test_squadadopt 29, test_squad_spawn 71, test_processlint 31 — OK.
Every grep hit (`templates/scope|scope.md|squadcompose|squad-spawn|squadrules|squadadopt|squadlabel|designer|WHEN_KEYS|design: no|, qa full`) run: all OK, incl. test_qab_optional 13, test_dev_rules_size 7, test_sizes 36, test_squad_close, test_squad_start, test_squadruntime, test_team_models, test_squad_ledger, test_squad_migrate, test_squadupgrade and the rest.
`bash -n bin/squad-spawn` clean.

## QA whitebox review

### QA whitebox 01 — sha 67e0d05 — PASS
Checked: diff vs T1-T10; re-ran test_squadcompose 51, squadrules 55, squadlabel 19, squadadopt 29, squad_spawn 71, processlint 31, dev_rules_size 7, sizes 36, qab_optional 13: all OK. `bash -n bin/squad-spawn` clean. spec.md body identical to tasks/architect-design.md, Status `confirmed by PO`. Diff = listed files + tickets/spec/evidence; no golden, no templates/squad/process edit. `grep designer bin hooks`: only the designer guard itself left.
Guard anchored like the designer one; tests drive real bin/squad-spawn (yes/no/maybe/absent/commented/design:yes).
Note (not a finding): facts header prints `architecture yes` only when on; absent/no byte-identical. Satisfies AC1 (no change when absent) and AC4 (header shows it when on); Manager FYI only.
Full suite: not yet; runs once on the scope's final sha (SUITE-3b).

## QA blackbox review

### QA blackbox 01 — commit 67e0d05 (CLI only, no screenshots; scratch squad, dry-run spawn)
Method: scratch squad in mktemp dir, worktree's `bin/squad-spawn`, `squad-process lint|compose`; scratch copy of the plugin with 3 test rules added. No code read.

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 accepts yes\|no, default no, bad refused like design | compose with `architecture: yes/no/absent/maybe`; `design: maybe` as control | yes/no ok; absent ok; `maybe` → `scope.md:10: architecture must be yes \| no, got 'maybe'` exit 2 (same shape/exit as `design must be yes \| no, got 'maybe'`). Absent/no compose output identical to main's (diff ignoring timestamp) | PASS |
| 2 spawn guard | `squad-spawn architect X --scope S --dry-run --prompt hi` on yes/no/absent/maybe/commented `<!-- architecture: yes -->`/`design: yes` only | yes → exit 0 (dry-run plan, label `🤖 Architect`); no, absent, maybe, commented, design-only → exit 1 `scope S has no 'architecture: yes' in scope.md; only the PO turns the architect on`. Designer guard unchanged (designer on `yes` scope refused; on `design: yes` passes) | PASS |
| 3 role known everywhere | spawn usage; `model architect: opus high` in scope.md; `roles: architect, dev` rule; compose architect; label | usage lists `architect`; dry-run gets `--model opus --effort high`; lint ok; compose architect works; label `Architect`. `squad-process adopt` ROLE_FILES not observable from outside | PASS (adopt not behaviour-testable; whitebox T7) |
| 4 when: architecture | scratch rules `when: architecture = yes` / `= no`; lint; compose dev on yes/no/absent; `= maybe` | lint ok; yes scope keeps only the yes rule; no and absent keep only the no rule; header on yes: `(size M, design no, architecture yes, qa full, goal no)`; `= maybe` → `safety.md:85: unknown value 'maybe' for when key 'architecture'` exit 1; `lint --home` on maybe scope exit 1, on yes exit 0 | PASS (header prints only when yes, per Manager ruling) |
| 5 template | read templates/scope/scope.md | has `architecture: no` after `design: no` | PASS |

Notes (not findings): goal home with `architecture: yes` in goal.md does not show it in header — same as `design: yes` in goal.md (parity). Spawn of architect warns "no model/effortLevel for architect" — settings card is task 02.
Verdict: PASS.
