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
