# 01 `architecture` scope fact, spawn guard, role plumbing
Status: ready-for-agent
Type: task

Duties: put design notes in this file; technical AC are QA whitebox's (agree with it); business AC are the ticket as written; risk flag or business doubt: `BLOCKED NN` (SIZE-14). Cite [REV-13b] hand-in, [EVID-2d] evidence, [SUITE-2c] suites, [LC-19b] design. Run only the test files you touch; before HANDIN run `grep -rl '<touched path or changed string>' tests/` and run every hit (goldens included). QA whitebox runs the full suite once on the final sha. Commit this task file as the ticket at `.scratch/add-architecture/issues/NN-<slug>.md`, evidence at `.../NN-<slug>/evidence.md`. Brief: `$SCOPE_DIR/scope.md`, design `$SCOPE_DIR/tasks/architect-design.md` (the spec; PO confirmed it as written), plan `$SCOPE_DIR/iterations/1.md`. Defect class: none yet. PROMO: none. This is the scope's first task: also commit the spec at `.scratch/add-architecture/spec.md` (copy of `tasks/architect-design.md`, Status line `confirmed by PO`) and the other two task files as tickets `02-...`, `03-...` (copies from `$SCOPE_DIR/tasks/`). Base: main.

Touched files: `bin/squadcompose.py` (`_FACT_VALUES`, `_FACT_DEFAULT`, goal-home default loop ~L73, facts header ~L190), `bin/squadrules.py` (`ROLES`, `WHEN_KEYS`), `bin/squad-spawn` (role lists L9, L62, L130, L133 and a guard like L111), `bin/squadadopt.py` (`ROLE_FILES`), `bin/squadlabel.py` (label), `bin/squadrules_cli.py` (help text only if needed), `templates/scope/scope.md` (`architecture: no` line), tests `tests/test_squadcompose.py`, `tests/test_squadrules.py`, `tests/test_squad_spawn.py` (+ any golden a grep shows). Harness: the fixtures already in those files. Does not add the role card or process rules (task 02).

## Business AC
1. `scope.md` accepts `architecture: yes|no`, default `no` when absent; a bad value is refused like a bad `design:` value. A scope without the line behaves exactly as today.
2. `squad-spawn architect <name> --scope S` refuses with exit 1 and a message naming `architecture: yes` and that only the PO turns it on, unless `scope.md` has `architecture: yes`. `architecture: no`/absent refuses; `yes` passes the guard.
3. `architect` is a known role everywhere roles are listed (spawn usage and role check, model-override lines `model architect: ...`, rules `roles:` values, adopt, labels). Role-short in agent names is `arch`.
4. Rules may use `when: architecture = yes` (and `no`); `squad-process lint` accepts it; compose keeps such a rule only when the scope's fact matches; the facts header printed by compose shows `architecture`.
5. New scopes from `templates/scope/scope.md` carry `architecture: no`.

## Technical AC (QA whitebox; agreed unless the Developer counters here)
T1. Mirror the `design` handling line by line; no new parser.
T2. Tests that fail on the old code (show the red run in evidence): fact default and bad value, guard yes/no/absent, role list, `when: architecture = yes` compose keep/drop, goal-home default.
T3. Existing tests in the touched test files pass whole; every grep hit under `tests/` run.
T4. `bash -n bin/squad-spawn` clean; diff lists only the files above plus ticket/evidence/spec files.
T5 (QA-w additions). Absent-line byte-identity: composing a scope without `architecture:` yields the same facts and the same rule set as before (existing compose goldens unchanged; no golden edited unless the facts header legitimately gains `architecture no` — then list each edited golden in evidence with why).
T6. Guard tests drive the real `bin/squad-spawn` (as the existing designer guard tests do): `architecture: yes` passes, `no`, absent and `architecture: maybe` each exit 1 with a message naming `architecture: yes` and the PO; the guard's grep is anchored like L111 and does not match `design: yes` or a commented line.
T7. Role plumbing is complete: every list in the touched files that holds `designer` also holds `architect` (grep `designer` over `bin/` and show the before/after count in evidence); `model architect: ...` lines are accepted by the L130 pattern; label for `architect` tested in `tests/test_squadlabel.py`/`test_squad_label.py` (add if no test covers a role label); `squadadopt.ROLE_FILES` addition tested.
T8. Lint: `squad-process lint` accepts `when: architecture = yes|no`, and refuses `architecture = maybe` (bad value) — tests for both. The `qa-b: no` + `design: yes` cross-check is left as is (no architecture coupling).
T9. Role-short `arch` is a process-rule string (starting.md, task 02); this ticket must not touch templates/squad/process/*; say so in evidence.
T10. Evidence has the red run (new tests failing on base) and the green run of every touched test file plus every grep hit.

## Design notes
- Mirrored `design` line by line (T1): `_FACT_VALUES/_FACT_DEFAULT`, goal-home loop, `WHEN_KEYS`, spawn guard (same anchored grep as L111, new message `scope S has no 'architecture: yes' in scope.md; only the PO turns the architect on`), role lists (usage, role case, model-line regex and role case), `ROLE_FILES`, label `Architect`, scope template `architecture: no`. `ROLES` gets `architect` (rules `roles:` values). `squadrules_cli` needed no change (no role list there).
- Counter/decision on header (AC4): the facts header shows `architecture yes` only when on; `no`/absent prints the header byte-identical to today. Reason: always printing adds 17 B, which breaks the 5 KiB dev-rules budget tests (`test_dev_rules_size`, `test_sizes`) and 54 byte-identity cases in `test_qab_optional` (T5 absent-line identity). Flag for QAs/Manager: if the PO wants `architecture no` printed always, the 5 KiB limit and the qab golden must be reopened.
- Spawn of `architect` needs `agents/architect.md` and settings: task 02. Dry-run works already (tests).
- `arch` role-short is a process-rule string (starting.md, task 02); `templates/squad/process/*` untouched (T9).
- No `squad-spawn` guard for goal homes (as designer).
