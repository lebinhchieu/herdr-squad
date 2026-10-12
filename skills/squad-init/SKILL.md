---
name: squad-init
description: Set up a squad in the current project - creates a squad folder under .claude/squads/ from templates, fills the project source map, and tunes per-role permissions. Use when the user asks to set up, initialise or prepare a squad for a project.
disable-model-invocation: true
---

# Set up a squad in this project

**Result: a `.claude/squads/<squad>/` folder that every role session in that squad works from.** A project can hold several squads, one per goal. Ask the user only what you can't find in the repo.

## 1. Copy the templates

- Project root = `git rev-parse --show-toplevel` (or the directory the user names).
- Squad name = the name the user gives, else ask for one (short, lowercase, e.g. `billing`).
- If `<root>/.claude/squads/<squad>/` already exists, stop and ask whether to refresh only missing files.
- Copy everything from `${CLAUDE_PLUGIN_ROOT}/templates/squad/` to `<root>/.claude/squads/<squad>/`.

## 2. Fill `<squad>/project.md`

Read the project's CLAUDE.md files, README, docs folders and repo layout. Fill every row of the source map with real paths. For each row you can't find, ask the user one batched question. Pay attention to:
- **Outside decision makers** and where their questions must go (an open-points file, never a person).
- **Code repos** (submodules count: Developers get a worktree per repo).
- **Test, lint and done rules** from the repo's own instructions; quote the commands exactly.
- **How QA blackbox reaches the running app** (dev server URL, login, Playwright location).

## 3. Tune `<squad>/settings/*.json`

- **QA blackbox:** replace the placeholder deny rule with one `Read(//<absolute code path>/**)` per code folder, plus `Read(//<root>/.worktrees/**)`.
- **Every role:** add `allow` rules for the project's exact test and lint commands from `project.md`.
- Keep every `deny` rule from the template. Validate each file with `jq empty`.

## 4. Worktrees

Make sure `.worktrees/` is git-ignored at the project root (Developers get `<root>/.worktrees/<agent>`). Tell the user if you added it.

## 5. Goal

Draft `<squad>/goal.md` with the user: one-sentence goal, in/out of scope, budget, and what "done" means. Don't start the squad; tell the user to run `/squad:squad-start` when the goal is agreed.
