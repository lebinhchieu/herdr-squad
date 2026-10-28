# Settings notes: squad `plugin`

**Every settings migration so far, newest first. Only v6 is fully applied: from v4, only the Developer's `squad-process show` entry is in.** Run the commands in Still to do below to finish v4.

Files: `.claude/squads/plugin/settings/<role>.json`, key `permissions.allow`. The plugin's templates live in `templates/squad/settings/`.

## Still to do (from v4)

| File | Missing from `permissions.allow` |
|---|---|
| `team-lead.json` | `Bash(squad-spawn dev:*)`, `Bash(squad-retire:*)`, `Bash(herdr agent list:*)`, `Bash(herdr agent get:*)`, `Bash(herdr agent read:*)` |
| `designer.json`, `qa-whitebox.json`, `qa-blackbox.json` | `Bash(squad-process show:*)` |

Without the Team Lead entries, every Developer spawn and retire in an M or L scope raises a permission prompt.

## v6: evidence next to the ticket (scope evidence-inline, plugin merge 252ea3b)

**Status: applied 2026-10-19, after the PO approved it in inbox item E4.**

| File | Added to `permissions.allow` | Why |
|---|---|---|
| `dev.json` | `Bash(squad-evidence:*)` | The Developer runs `squad-evidence add` to pull each reviewer file into the ticket's `evidence.md`, and `path`/`check` on its own work |
| `dev.json` | `Bash(squad-process show:*)` | The v4 entry, missing until now |
| `tech-lead.json` | `Bash(squad-evidence check:*)`, `Bash(squad-evidence path:*)` | The Tech Lead checks the evidence sha with `squad-evidence check --base <passed sha>` |

## v4: Team Lead runs the pod (process v3 → v4, plugin 0.3.1)

**Status: partly applied. Only `dev.json` has its entry, added in v6.**

| File | Add to `permissions.allow` | Why |
|---|---|---|
| `team-lead.json` | `Bash(squad-spawn dev:*)`, `Bash(squad-retire:*)`, `Bash(herdr agent list:*)`, `Bash(herdr agent get:*)`, `Bash(herdr agent read:*)` | In M and L the Team Lead spawns and retires Developers and watches their panes |
| `dev.json`, `designer.json`, `qa-whitebox.json`, `qa-blackbox.json` | `Bash(squad-process show:*)` | These roles read only their sections of `process.md` |

- **Leave out the `model` / `effortLevel` keys.** `squad-spawn` falls back to the template per key; add one only to override it.

## Rules for every settings migration

- **Add only.** Keep the squad's own entries: every file allows `python3 tests/run_suite.py` and `python3 -m unittest`. `qa-blackbox.json` has no Read deny (E5): drop old `Read(//…/**)` code-path entries when migrating.
- **Check after editing** (prints nothing when every file parses):

```bash
cd /home/chieule/workspace/squad && for f in .claude/squads/plugin/settings/*.json; do python3 -m json.tool "$f" >/dev/null || echo "BAD $f"; done
```

- **Scratch `rm`.** dev, qa-whitebox, qa-blackbox, manager, tech-lead, team-lead allow `rm -rf`, `rm -r`, `rm`, `rmdir` of `/tmp/tmp.*` and *ask* when a second path follows (`/tmp/tmp.* *`): the glob's `*` matches spaces, so without the ask entry `rm -rf /tmp/tmp.x /etc` would be allowed (tested live). `..` paths are blocked by Claude itself.
