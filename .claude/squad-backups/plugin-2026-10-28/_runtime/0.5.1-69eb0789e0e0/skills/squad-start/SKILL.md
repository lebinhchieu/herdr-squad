---
name: squad-start
description: Start a task or a goal in the squad - makes its scope or goal folder and brief and starts a fresh Manager in a new herdr tab. Also restarts the Manager of an unfinished scope or goal. Use when the user asks to start, launch, kick off or resume work with the squad.
disable-model-invocation: true
---

# Start work with the squad

**Result: a new scope (a lone task) or goal (several scopes) with its own folder and brief, and a fresh Manager running in its own herdr tab.** The Manager sizes the work, proposes a plan to the PO, and spawns the pod. You only create the folder and start the Manager; `bin/squad-start` does both.

1. Check `HERDR_ENV` is `1`. If not, tell the user to open herdr and run this from a pane there.
2. Pick the squad: the name the user gives, else the only folder in `.claude/squads/` (several and none named: ask). Check it has a `scopes/` folder. A squad with a `roster.md` at its top and no `scopes/` folder is the old flat layout: stop, don't convert it, and tell the user to talk to its running Manager instead.
3. **Resuming?** If the user means unfinished work whose Manager is gone, list the open folders in `scopes/` and `goals/` (not `_done/`), then do step 5a for it, run `squad-start --resume <name> [--model M] [--effort E]` and go to step 7. A scope inside a goal is resumed through its goal.
4. **Take the request.** The text the user gave is the brief, as they wrote it. Plain text is a lone task. If it names several deliverables, or the user calls it a goal, suggest a goal and prefix it with `goal:`. Ask for what you can't tell: **what repos or paths the work touches** (propose them from `project.md` → Code repos), as a comma list for `--touches`.
5. **Name it.** Run the command below with `--dry-run` first. It prints the folder it would create; the last part is the name (a ticket id like SEC-04 becomes `sec04`, otherwise a short slug). Show it to the user in one line and let them change it with `--name`. The Manager name `<squad>-mgr-<name>` must stay within 32 characters.
   **5a. Confirm the Manager's model and effort** (also before `--resume`). The `--dry-run` output (for a resume: `squad-start --resume <name> --dry-run`) ends with `manager model: … (from …)` and `manager effort: … (from …)`. Ask the PO once, with these options: **keep** (show the default, e.g. `sonnet / high`), **change model** (`opus`, `sonnet`, `haiku`), **change effort** (`low`, `medium`, `high`, `xhigh`, `max`). Pass a change as `--model` / `--effort` on the run below; the choice is recorded in the Manager's `.overrides` (ADR 0008), so a respawn keeps it. Keep means no flags. Never start the Manager before the PO answers.
6. Run:

   ```bash
   squad-start --squad <squad> "<text>" --touches <paths> [--name <name>]
   ```

   If the plugin is loaded with `--plugin-dir` rather than installed, set `SQUAD_PLUGIN_DIR=${CLAUDE_PLUGIN_ROOT}` for the command so the Manager and everyone it spawns load it too.
   - **Exit 3 = overlap** with an open scope. Show the user each overlap line and ask whether to go ahead. Two scopes editing the same files only collide at merge. If yes, run again with `--yes`.
   - **Any other error** is printed as is (a name already used, a name too long, a Manager that wouldn't start; nothing is left behind when the Manager fails). Fix it and run again.
7. Tell the user the scope or goal name and which herdr tab the Manager is in. From now on they talk to that Manager there. Each scope or goal has its own Manager, so several can run side by side in different tabs.
   If `process_update` is not `null`, tell the user that sentence and that `/squad:squad-process-update` updates it on their word. Never run it unasked.
