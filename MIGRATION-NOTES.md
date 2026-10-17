# Migration notes: squad `plugin`, process v3 → v4 (plugin 0.3.1)

**To do by hand, in this order:**
1. Settings: add `squad-process show` to 5 roles and give the Team Lead 5 commands it needs. Change nothing else (table below).
2. Process: run `/squad:squad-process-update` when you're ready. It handles `process.md`, and only `## Task lifecycle` needs your choice.

Nothing here has been applied. Squad folder: `.claude/squads/plugin/`.

## 1. Settings (`.claude/squads/plugin/settings/*.json`)

| File | Add to `permissions.allow` |
|---|---|
| `team-lead.json` | `Bash(squad-spawn dev:*)`, `Bash(squad-retire:*)`, `Bash(herdr agent list:*)`, `Bash(herdr agent get:*)`, `Bash(herdr agent read:*)` |
| `dev.json`, `designer.json`, `qa-whitebox.json`, `qa-blackbox.json` | `Bash(squad-process show:*)` |

- **Team Lead entries are required in v4:** in M and L it spawns and retires the Developers and watches their panes. Without these entries every spawn raises a permission prompt.
- **Leave out the `model` / `effortLevel` keys.** `squad-spawn` already falls back to the plugin template per key, so the pins apply today (Manager opus/medium; Dev, Team Lead and Token Coach sonnet/medium; the others sonnet/high). Add a key only to override it.
- **Keep the squad's own entries.** Every squad file has `python3 tests/run_suite.py` and `python3 -m unittest` in `allow`, and `qa-blackbox.json` denies reading this repo's real `bin/`, `hooks/`, `skills/` and `tests/`. The template has a placeholder there (`CODE_PATHS_SET_BY_SQUAD_INIT`). These are this project's settings, so don't take the template's version.
- Ignore the `.dev.json.swp` in that folder: it's a leftover editor swap file. Delete it once no editor has the file open.

Check after editing (should print nothing):

```bash
cd /home/chieule/workspace/squad && for f in .claude/squads/plugin/settings/*.json; do python3 -m json.tool "$f" >/dev/null || echo "BAD $f"; done
```

## 2. Process (`process.md` v3 → v4)

Run `/squad:squad-process-update` (or say `migrate the process`). It writes nothing until you confirm. What v4 changes:
- **M gains a Team Lead.** It owns the plan, order and assignment, spawns and retires Developers within its share of the cap, steps in after 3 returns on one task, and is the pod's contact (the Manager hears only four things from it).
- **Only the Tech Lead runs the full suite.** Developers and QAs run only the test files they touched.
- **Base branch:** the Manager checks it and the Team Lead spawns with it.
- **Your two local sections stay as they are:** `Lifetimes` and `Cost rules`.
- **One conflict, `## Task lifecycle`:**
  - Your squad added "on re-hand-in a QA re-checks only the changed files and their AC".
  - v4 changes the QA `light` mode to targeted tests and gives the 3-returns step to the Team Lead.
  - Pick your own wording that keeps both. Neither "ours" nor "theirs" alone keeps them.

## Watch out

- The running scope `extractor-role` was sized under v3 (M, Tech Lead owns the plan, no Team Lead). Migrating mid-scope doesn't add a Team Lead to it. Migrate after it closes, or tell its Manager to keep v3 rules until then.
