# Spawn overrides survive a respawn

Status: accepted (audit-token)

Amended by 0010: the role default now comes from settings/<role>.json, not the role file's frontmatter.

Amended by 0016/C2 (ticket 19, 2026-10-22): `squad-start --resume` reads `roles/<manager>.overrides`; the shown default is the recorded override and flags win.

**Decision:** `squad-spawn --model/--effort` records the override in the agent's home, `roles/<name>.overrides` (lines `model=<v>`, `effort=<v>`). `squad-respawn` reads that file and passes the values to `squad-spawn` again. A spawn with no override removes a stale file.

**Why:** a cost-rule respawn silently returned a Sonnet Manager or a medium-effort QA to its role default, so a model-per-role trial would have measured nothing.

**Consequences:**
- A value must match `^[A-Za-z0-9][][A-Za-z0-9._-]*$`: a value that starts with `-` is refused by `squad-spawn` and by `squad-respawn`.
- No migration: an agent without a file keeps its role default.
- Precedence when a role starts: flags > recorded override > `scope.md` `model <role>: <model> <effort>` line (ticket 20) > squad `settings/<role>.json` > plugin template. A value read from `scope.md` is never written to `.overrides`.

**Alternatives rejected:** editing the `agents/*.md` defaults (the PO picked measurement plus a trial first, E2 (a)); a roster column.
