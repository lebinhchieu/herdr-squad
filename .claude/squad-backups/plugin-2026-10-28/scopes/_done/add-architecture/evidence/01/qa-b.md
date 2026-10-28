# QA blackbox 01 — commit 67e0d05 (CLI only, no screenshots; scratch squad, dry-run spawn)
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
