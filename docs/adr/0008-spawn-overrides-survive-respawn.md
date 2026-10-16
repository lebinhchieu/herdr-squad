# Spawn overrides survive a respawn

Status: accepted (audit-token)

Amended by 0010: the role default now comes from settings/<role>.json, not the role file's frontmatter.

**Decision:** `squad-spawn --model/--effort` records the override in the agent's home, `roles/<name>.overrides` (lines `model=<v>`, `effort=<v>`). `squad-respawn` reads that file and passes the values to `squad-spawn` again. A spawn with no override removes a stale file. `squad-start --resume` does not read the file: the Manager's flags must be repeated on it.

**Why:** a cost-rule respawn silently returned a Sonnet Manager or a medium-effort QA to its role default, so a model-per-role trial would have measured nothing.

**Consequences:**
- `squad-start --resume <name>` must repeat the Manager's `--model`/`--effort` (trial protocol step).
- A value must match `^[A-Za-z0-9][][A-Za-z0-9._-]*$`: a value that starts with `-` is refused by `squad-spawn` and by `squad-respawn`.
- No migration: an agent without a file keeps its role default.

**Alternatives rejected:** editing the `agents/*.md` defaults (the PO picked measurement plus a trial first, E2 (a)); a roster column.
