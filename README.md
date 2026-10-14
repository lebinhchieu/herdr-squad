# squad: a self-managing Claude Code dev team

**You are the PO. For each task or goal you give it, a fresh Manager session spawns and runs a team of Claude Code sessions (BA, Team Lead, Tech Lead, QA whitebox, QA blackbox, Developers), each in its own herdr tab. They talk through Claude Code's built-in cross-session messaging and keep everything durable in a folder in your project. Work is grouped by scope: a scope starts fresh, shares nothing with other scopes, and its lasting knowledge goes into your project's own docs.**

## Quick start

```bash
# 1. Load the plugin (pick one)
claude plugin marketplace add lebinhchieu/herdr-squad && claude plugin install squad@herdr-squad
#    or, while developing the plugin:
claude --plugin-dir ~/workspace/squad

# 2. Once per project or module, in a herdr pane at your project root, inside Claude:
/squad:squad-init                              # standing squad: process, source map, permissions

# 3. For every task or goal:
/squad:squad-start "Fix SEC-04: remove the committed default bypass key"
/squad:squad-start "goal: rebuild the settings page"      # several scopes under one goal Manager
```

`squad-start` makes the scope (or goal) folder and brief and starts a fresh Manager in its own herdr tab; you talk to it there. The Manager sizes the work (**S**: Tech Lead + Developers; **M**: + BA and both QAs; **L**: + Team Lead), proposes a plan, spawns only the roles that size needs, and checks in with you at the end of each iteration. Several scopes can run side by side, each in its own tab. A Manager that is gone can be restarted with `squad-start --resume <name>`.

## The layers

| Level | Where | Lives | Holds |
|---|---|---|---|
| **Project** | your repo | for good | Domain and goal knowledge, in the project's own docs |
| **Squad** | `.claude/squads/<squad>/` | for good | How the team works: `process.md`, `project.md` (a map into your docs), `process-log.md`, `settings/` |
| **Goal** | `goals/<goal>/` | until it closes | What a goal's scopes share: `goal.md`, `shared/decisions.md`, summaries, contracts |
| **Scope** | `scopes/<scope>/` | until it closes | Everything for one piece of work: brief, roster, iterations, tasks, evidence, notes, logs |

A lone scope sees nothing of other scopes. The scopes of a goal share only `goals/<goal>/`, and may build on each other's passed branches. What a scope or goal finds that must outlive it is **promoted**: a reviewed task commits it into your project docs. The full protocol is `templates/squad/process.md`.

## What's inside

| Path | What it is |
|---|---|
| `agents/*.md` | The 8 role definitions, started as **top-level sessions** with `claude --agent squad:<role>` (not as subagents) |
| `bin/squad-start` | Makes a scope or goal folder and brief, checks that the work doesn't overlap an open scope (`--touches`), starts a fresh Manager. `--in-goal G` adds a scope to a goal; `--resume NAME` restarts a Manager; `--model M` and `--effort E` set the Manager's model and effort |
| `bin/squad-spawn` | Opens a herdr tab, makes a git worktree for Developers (`.worktrees/<squad>/<scope>/<agent>`, branch `squad/<squad>/<scope>/<agent>`; `--base` starts it from a passed branch), starts `claude --agent squad:<role> --name <agent> --permission-mode auto --settings <role settings>` |
| `bin/squad-close` | `--scope S` retires a scope's agents, removes merged worktrees and moves the folder to `scopes/_done/`. `--goal G` does the same for a goal and refuses while a scope is open or its shared decisions were never promoted. With neither it archives the whole squad. Every branch is reported; none is deleted |
| `bin/squad-respawn` | Replaces an agent's session with a fresh one from its notes; keeps its name, scope and worktree |
| `bin/squad-retire` | Asks an agent to save its notes, then closes its pane (worktree and branch are kept) |
| `bin/squad-usage` and the Stop hook | Token usage per agent, and the cost rules that tell an agent to start fresh |
| `skills/squad-init`, `skills/squad-start` | The two commands you run |
| `templates/squad/` | The standing layer: `process.md`, `project.md`, `process-log.md`, per-role `settings/*.json` |
| `templates/scope/`, `templates/goal/` | What `squad-start` copies into a new scope or goal |

`bin/` is on the Bash tool's PATH while the plugin is enabled, so the Manager runs `squad-spawn` as a plain command.

## Squad board

A live page showing each agent's state, messages and activity as a sequence of bars.

- `/squad:squad-start` opens it in a `board` herdr tab and prints the URL. `/squad:squad-board` prints the URL again or restarts the board (`squad-board-start --restart`).
- It listens on 127.0.0.1 (port 7420 by default) only. The token at the end of the URL is needed for Jump.
- Bars grow from when the recorder first runs; nothing is drawn for time before that.
- Needs Python 3, herdr, `jq` and `git`.
- `messages.jsonl` and `activity.jsonl` hold message text and are git-ignored by `squad-init`.
- The user guide is [docs/squad-board-guide.html](docs/squad-board-guide.html); the design is in `.scratch/squad-board/spec.md`.

## Requirements

- Claude Code ≥ 2.1.224 (cross-session messaging), herdr, `jq`, `git`, `python3`.
- Start everything from a herdr pane (`HERDR_ENV=1`).
- **Trust the project folder once** in Claude Code. Worktrees live under `<project>/.worktrees/<squad>/`, so they inherit that trust; a worktree outside a trusted folder stops at the trust prompt.

## Safety defaults

- Every role runs in `auto` permission mode with `.claude/squads/<squad>/settings/<role>.json`.
- **Denied for every role:** `git push`, `git rebase`, `git reset --hard`, switching to `main`/`dev`, and every Jira/Confluence write tool. **`git merge` is denied for every role except Developers**, who may merge only inside their own branch (integration tasks); the PO does every real merge.
- **QA blackbox** is also denied `Read` on the code folders, so it judges behaviour only. Shell reads aren't covered by `Read` rules; its instructions forbid them.
- Messages between sessions can't approve permissions. A `blocked` pane needs the PO.

## Known limits

- **Flat squads.** A squad created before the per-scope layout (a `roster.md` at its top, no `scopes/` folder) keeps working through the same scripts, which fall back to the flat layout and the older worktree paths. `squad-start` refuses to convert one. The fallbacks are marked `legacy flat layout` and can go once such squads finish.
- **One board per herdr workspace.** A second `squad-board-start` in the same workspace reuses the running board instead of starting another.
- **Cost:** every role is a full session, and every scope pays a fresh start (a Manager, plus a re-read of the project docs). Run `squad-usage` after real use to see what a scope costs.
- **Several Managers, several tabs.** Each running scope or goal has its own Manager tab that can block on you.
