---
name: squad-init
description: Set up a squad in the current project - creates the standing squad folder under .claude/squads/ from templates, fills the project source map, and tunes per-role permissions. Use when the user asks to set up, initialise or prepare a squad for a project or module.
disable-model-invocation: true
---

# Set up a squad in this project

**Result: a standing `.claude/squads/<squad>/` folder (how the team works, where the project's truth lives) with empty `scopes/` and `goals/`.** Work is not planned here: every task or goal the PO brings later gets its own scope or goal folder and a fresh Manager from `/squad:squad-start`. A project can hold several squads, for example one per module. Ask the user only what you can't find in the repo.

## 1. Copy the templates

- Project root = `git rev-parse --show-toplevel` (or the directory the user names).
- Squad name = the name the user gives, else ask for one (short, lowercase, e.g. `billing`). It becomes part of every agent name, which herdr limits to 32 characters, so keep it under 10.
- If `<root>/.claude/squads/<squad>/` already exists, stop and ask whether to refresh only the missing files. Never touch its `scopes/` or `goals/`.
- Copy everything from `${CLAUDE_PLUGIN_ROOT}/templates/squad/` to `<root>/.claude/squads/<squad>/`, then create the empty folders `scopes/` and `goals/` there. The `scopes/` folder is what marks a squad as per-scope.

## 2. Fill `<squad>/project.md`

Read the project's CLAUDE.md files, README, docs folders and repo layout. Fill every row of the source map with real paths. For each row you can't find, ask the user one batched question. This file is a map into the project's own docs, not a copy of them, so the project stays the single home of domain knowledge. Pay attention to:
- **Project instructions file:** the file teammates without the squad follow; ask the user which it is if none is found.
- **Outside decision makers** and where their questions must go (an open-points file, never a person).
- **Code repos** (submodules count: Developers get a worktree per repo).
- **Test, lint and done rules** from the repo's own instructions; quote the commands exactly.
- **Where lasting decisions and glossary changes go**, and any rule about editing those files (some projects require a skill for instruction files). The promotion task at a scope's end follows it.
- **How QA blackbox reaches the running app** (dev server URL, login, Playwright location).

## 3. Tune `<squad>/settings/*.json`

- **QA blackbox:** replace the placeholder deny rule with one `Read(//<absolute code path>/**)` per code folder, plus `Read(//<root>/.worktrees/**)`.
- **Every role:** add `allow` rules for the project's exact test and lint commands from `project.md`.
- Keep every `deny` rule from the template. Validate each file with `jq empty`.

## 4. Worktrees

Make sure `.worktrees/` is git-ignored at the project root (Developers get `<root>/.worktrees/<squad>/<scope>/<agent>`). Tell the user if you added it.

## 5. Defaults

`process.md` → Defaults holds the Developer cap (3) and the budget rule that every scope and goal starts with. Ask the user only if they want different values, and edit `process.md` and log it in `process-log.md` if so. A scope or goal can override them in its own brief.

## 6. Keep or ignore the squad folder

Ask the user once how `<root>/.claude/squads/` is tracked. A long-lived squad keeps its tuned `process.md`, source map and each scope's brief and iterations there, and an ignored folder lives only on this machine. Options:

- **Commit the durable files only (recommended).** Write `<root>/.claude/squads/.gitignore` with these lines: `*/scopes/*/roles/`, `*/scopes/*/evidence/`, `*/scopes/*/roster.md`, `*/scopes/*/escalations.md`, `*/goals/*/roles/`, `*/goals/*/roster.md`, `*/goals/*/escalations.md`, `*.jsonl` and `_done/`. Notes, evidence, rosters and logs stay local; `process.md`, `project.md`, `process-log.md`, `settings/`, and each scope's `scope.md`, `iterations/`, `tasks/` and each goal's `goal.md` and `shared/` are shared.
- **Commit everything.** Evidence and notes go into the history. Only the board logs are ignored: write `<root>/.claude/squads/.gitignore` with the single line `*.jsonl` (they hold message text) and say so.
- **Ignore everything.** Add `.claude/squads/` to the project's `.gitignore`; use it for a short-lived squad.

Do what the user picks and tell them what you wrote. If `git check-ignore .claude/squads/<squad>/process.md` already matches a rule, say which one before adding anything.

Then tell the user to run `/squad:squad-start "<what you want done>"` for the first task or goal. Don't start anything yourself.
