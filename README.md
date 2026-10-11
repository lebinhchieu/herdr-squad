# squad: a self-managing Claude Code dev team

**You are the PO. A Manager session spawns and runs a team of Claude Code sessions (BA, Team Lead, Tech Lead, QA whitebox, QA blackbox, Developers), each in its own herdr tab. They talk through Claude Code's built-in cross-session messaging and keep everything durable in a `squad/` folder in your project.**

## Quick start

```bash
# 1. Load the plugin (pick one)
claude plugin marketplace add lebinhchieu/herdr-squad && claude plugin install squad@herdr-squad
#    or, while developing the plugin:
claude --plugin-dir ~/workspace/squad

# 2. In a herdr pane at your project root, inside Claude:
/squad:squad-init     # creates squad/, fills project.md, tunes permissions, drafts goal.md
/squad:squad-start    # starts the Manager in its own herdr tab
```

Then talk to the Manager in its tab. It proposes iteration 1 and a **size per scope** (S: Tech Lead + Developers; M: + BA and both QAs; L: + Team Lead; XL: several pods), spawns only the roles that size needs, and checks in with you at the end. Sizes and their rules live in `templates/squad/process.md` → Sizes.

## What's inside

| Path | What it is |
|---|---|
| `agents/*.md` | The 7 role definitions, started as **top-level sessions** with `claude --agent squad:<role>` (not as subagents) |
| `bin/squad-spawn` | Opens a herdr tab, makes a git worktree for Developers, starts `claude --agent squad:<role> --name <agent> --permission-mode auto --settings <role settings>` |
| `bin/squad-retire` | Asks an agent to save its notes, then closes its tab (worktree and branch are kept) |
| `skills/squad-init` | Sets up `squad/` in a project |
| `skills/squad-start` | Starts the Manager |
| `templates/squad/` | `process.md` (the shared protocol, incl. sizes), `scopes.md`, `contracts/`, roster, goal, source map, iteration template, per-role `settings/*.json` |

`bin/` is on the Bash tool's PATH while the plugin is enabled, so the Manager runs `squad-spawn` as a plain command.

## Requirements

- Claude Code ≥ 2.1.224 (cross-session messaging), herdr, `jq`, `git`.
- Start everything from a herdr pane (`HERDR_ENV=1`).
- **Trust the project folder once** in Claude Code. Worktrees live under `<project>/.worktrees/`, so they inherit that trust; a worktree outside a trusted folder stops at the trust prompt.

## Safety defaults

- Every role runs in `auto` permission mode with `squad/settings/<role>.json`.
- **Denied for every role:** `git push`, `git merge`, `git rebase`, `git reset --hard`, switching to `main`/`dev`, and every Jira/Confluence write tool.
- **QA blackbox** is also denied `Read` on the code folders, so it judges behaviour only. Shell reads aren't covered by `Read` rules; its instructions forbid them.
- Messages between sessions can't approve permissions. A `blocked` pane needs the PO.

## Known limits

- **Not tested yet in a full run.** Verified so far: plugin validation, `--agent squad:<role>` loading, `squad-spawn` creating a worktree + named session with `SQUAD_*` env, `ListAgents` seeing other sessions, `squad-retire`.
- **Cost:** every role is a full session. Start with one pod.
