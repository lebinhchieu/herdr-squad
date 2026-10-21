Status: ready-for-agent
Type: task
Task ID: 20
Touches: `bin/squad-spawn` (scope-level role defaults), `bin/squad-start` (scope.md template comment), `templates/squad/process/starting.md` and `templates/squad/process/sizes.md` (Manager first-move rules), `tests/test_squad_spawn.py`, `tests/test_team_models.py` (new)
Does not touch: `agents/*`, settings templates
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_team_models test_squad_spawn test_model_effort_settings test_windows_safe`
Blocked by: 03, 08, 19 (19 also edits `bin/squad-start`)

# 20: The Manager proposes the team's models with the size, and the PO can change them

**Done when the Manager's size proposal includes a model and effort per role of the pod, the PO's answer is recorded in `scope.md`, and every spawn in that scope uses it.**

## What
- **Rule (Manager, first move):**
  - with the size and plan, show one table: each role the size brings, its default model and effort, and the advisor on or off;
  - in the same inbox item, offer to keep it or change any row;
  - write the confirmed rows to `scope.md`, then spawn.

  A goal Manager does this per scope.
- **`scope.md` format:** one line per changed role, `model <role>: <model> <effort>`, for example `model dev: sonnet medium`. Roles not listed use their defaults.
- **Precedence in `squad-spawn`:**
  1. `--model` / `--effort` flags;
  2. the agent's recorded overrides (ADR 0008, on respawn);
  3. `scope.md` `model <role>:`;
  4. squad settings;
  5. template.

  The Team Lead's Developer spawns pick it up with no change to the Team Lead.
- A change in the middle of a scope applies to the next spawn or respawn of that role. The Manager respawns running agents only when the PO asks.

## Technical AC
1. Precedence table tests, one per level, with a stub `claude` argv.
2. A malformed line exits 2 with the line named; an unknown role is a warning.
3. `who` shows the Manager acting on the first-move rule at every size.
4. ADR 0010's consequence about role defaults gets an amendment note (done in ticket 16).
