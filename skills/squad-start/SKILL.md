---
name: squad-start
description: Start the squad's Manager session in a new herdr tab for the current project. Use when the user asks to start, launch or kick off the squad.
disable-model-invocation: true
---

# Start the squad

**Result: a Manager session running in its own herdr tab.** It starts a new squad or resumes a long-lived one. You only start the Manager; it spawns the rest.

1. Check `HERDR_ENV` is `1`. If not, tell the user to open herdr and run this from a pane there.
2. Pick the squad: the name the user gives, else the only folder in `.claude/squads/` (several and none named → ask). Check `.claude/squads/<squad>/goal.md` is filled (no `<...>` placeholders). If not, stop and point the user at `/squad:squad-init`. If `herdr agent get manager-<squad>` finds a live Manager, stop and tell the user to continue in its tab.
3. Run:

   ```bash
   squad-spawn manager manager-<squad> --squad <squad> --prompt "Start of run. Do your start-of-session routine. If iterations/ holds a numbered iteration file, report where the squad stands and ask me what comes next; otherwise read goal.md and propose iteration 1 before spawning anyone."
   ```

   If the plugin is loaded with `--plugin-dir` rather than installed, set `SQUAD_PLUGIN_DIR=${CLAUDE_PLUGIN_ROOT}` for the command so the Manager and everyone it spawns load it too.
4. Tell the user which herdr tab the Manager is in. From now on they talk to the Manager there.
