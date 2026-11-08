# squad: a self-managing Claude Code dev team

**You are the PO. For each task or goal you give it, a fresh Manager session spawns and runs a team of Claude Code sessions (Developers, and the optional roles BA, Team Lead, Tech Lead, QA whitebox, QA blackbox, UI/UX Designer and Architect that the PO confirms for each scope), each in its own herdr tab. They talk through Claude Code's built-in cross-session messaging and keep everything durable in a folder in your project. Work is grouped by scope: a scope starts fresh, shares nothing with other scopes, and its lasting knowledge goes into your project's own docs.**

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

`squad-start` makes the scope (or goal) folder and brief and starts a fresh Manager in its own herdr tab; you talk to it there. The Manager proposes the scope's team, one role at a time with its signal (a risk flag or a business doubt asks for a BA, a Tech Lead or a QA); you confirm it and it is recorded as the `team:` line of `scope.md`. Any subset of the seven optional roles is valid. The Manager then proposes a plan, spawns only the roles on the team, and checks in with you at the end of each iteration. Several scopes can run side by side, each in its own tab. A Manager that is gone can be restarted with `squad-start --resume <name>`. The Designer delivers a design before build (screens, states, flows, optional HTML prototype) and no post-build check; the built UI is checked against it by the Developer's screenshots, or by QA blackbox when on the team. The Architect, confirmed the same way (`architect` on the team), delivers `architecture.md` (components, boundaries, contracts, constraints, and the irreversible choices with a recommendation) before the plan and checks no built code; the team follows it or sends the Architect an `ASK`, conformance joins the technical AC, and the PO still decides each irreversible choice.

## The process

The team's process is not a document each squad copies. It is a folder of rules, `templates/squad/process/*.md`, each tagged with an ID and the roles, duties and options it applies to. When the Manager starts a role, `squad-process compose` picks that role's rules and the session reads only them, so a Developer's start-up reads a few KB, not the whole process. A squad's own changes live in `process.local.md` as `replace`, `add` and `remove` operations on rule IDs (`squad-process rule <ID>` and `who <ID>` show any rule). Each scope records the plugin version it started on (`plugin:` in `scope.md`) and runs on that pinned runtime until it closes, so a plugin update never changes a pod mid-scope. Between scopes `squad-process upgrade` applies every rule your overlay does not touch and asks you only about the few it cannot decide. A squad that still has a `process.md` keeps working. The team decides who is in the pod, and each duty (plan, business AC, code check, suite run) goes to the first present role in its fallback chain.

**0.6.0 (breaking):** the S, M, L presets are gone. A scope made on an older version replaces its old scope lines by one `team:` line by hand; the engine rejects the old lines; a scope pinned below 0.6.0 keeps running its pinned runtime. See ADR 0018 in `docs/adr/`.

## The layers

| Level | Where | Lives | Holds |
|---|---|---|---|
| **Project** | your repo | for good | Domain and goal knowledge, in the project's own docs |
| **Squad** | `.claude/squads/<squad>/` | for good | How the team works: `process.local.md` (overlay on the plugin's rules), `project.md` (a map into your docs), `process-log.md`, `settings/` |
| **Goal** | `goals/<goal>/` | until it closes | What a goal's scopes share: `goal.md`, `shared/decisions.md`, summaries, contracts |
| **Scope** | `scopes/<scope>/` | until it closes | Everything for one piece of work: brief, roster, iterations, tasks, evidence, notes, logs |

A lone scope sees nothing of other scopes. The scopes of a goal share only `goals/<goal>/`, and may build on each other's passed branches. What a scope or goal finds that must outlive it is **promoted**: a reviewed task commits it into your project docs. The full protocol is the rule files in `templates/squad/process/`.

## What's inside

| Path | What it is |
|---|---|
| `agents/*.md` | The 9 role definitions, started as **top-level sessions** with `claude --agent squad:<role>` (not as subagents) |
| `bin/squad-start` | Makes a scope or goal folder and brief, checks that the work doesn't overlap an open scope (`--touches`), starts a fresh Manager. `--in-goal G` adds a scope to a goal; `--resume NAME` restarts a Manager; `--model M` and `--effort E` set the Manager's model and effort |
| `bin/squad-watchdog` | Started by `squad-start` for every scope or goal that gets a Manager (`SQUAD_WATCHDOG=off` skips it). Inside herdr it runs in its own herdr tab, labelled `watchdog`, in the Manager's workspace; the tab opens without focus and runs only `squad-watchdog run --home <home> --manager <name>` (no Claude, no shell chatter) and closes when the home folder is gone. Outside herdr, or when the tab cannot be opened (a warning goes to stderr), it runs as a detached process. One watchdog runs per home: a second start for a live one opens no tab and `run` exits at once. Every minute it checks herdr: when no agent works and a ticket waits (ready, building, returned, handed in, checking) it logs `idle start` with every agent's state in `watchdog.log` of the scope or goal folder, and sends the Manager a message after 5 and after 15 minutes of the same idle spell. **Sleep-when-idle is off.** `squad-watchdog sleep on` (and `off`) is the switch (the file `watchdog.sleep` holds `on` or `off`); the PO turns it on, or says "I am away" (see `bin/squad-away-hook`). While it is on, the watchdog suspends the computer once, when no agent anywhere on this machine works in herdr for 5 minutes (`SQUAD_WATCHDOG_SLEEP_AFTER`, minutes), for any reason and whatever the tickets say. The log line names the reason: `all tickets passed`, `team idle with open tickets`, or `team idle` when there is no ticket. It logs `sleep pc` and then switches itself off, so a wake-up does not sleep again. `SQUAD_WATCHDOG_SLEEP_CMD` replaces the suspend command. `squad-watchdog status` shows the switch, the last pass and the log tail |
| `bin/squad-away-hook` | A `UserPromptSubmit` hook (wired in `hooks/hooks.json`) that acts only in a Manager session, for its own scope or goal. A prompt that starts with "I am away" or "I'm away" runs `squad-watchdog sleep on` and writes the file `<home>/away`; one that starts with "I am back" or "I'm back" runs `sleep off` and deletes it, and the Manager writes one inbox read item listing what was decided while away. A failing switch never blocks the prompt: it is reported to the Manager. While `<home>/away` exists, rule ITER-17 (away mode) binds the Manager and Team Lead: they keep working on clear points, the owner or Manager decides what is not an "Always goes to PO" item (advisor first), a question only the PO can settle is parked (`squad-inbox park`) while other tickets go on, and a merge, push or deploy still waits for the PO's request in chat |
| `bin/squad-board` | The PO's read-only dashboard. `squad-board [--squad NAME\|PATH]... [--goal G \| --scope S] [--port N] [--herdr-json FILE] [--no-open]` serves **one goal or one scope at a time** on 127.0.0.1 (default port 8765, `--port 0` picks a free one) and opens the browser; `--no-open` only prints the URL. `--goal` and `--scope` cannot be used together; with neither, the page opens on the choice it saved last time if that goal or scope is still open, else on a picker. `--squad` is needed when the repo has more than one squad, and takes a path to open a squad in another repo. `--herdr-json FILE` reads herdr agents from a recorded file instead of running `herdr` (for tests and demos). It reads the squad's files, git, herdr and transcripts and **writes one file only: `board-ui.json`** (font size, the last choices, panel order, width and visibility, saved by the page). Its one action is `POST /api/open`, which starts the local `code` CLI and writes nothing in the squad. The page is a grid (2, 4 or 6 grid columns by window width); panels fill holes beside or above an earlier one, can be dragged, and a panel takes 1 to N grid columns by dragging its right edge; the width is saved in `board-ui.json` as `tracks` (twelfths of the row), so a panel keeps its share when the window changes. Where the PO must act it shows the command to copy. **Parked questions:** the PO sets a question aside with `squad-inbox park --text "..." [--from E<n>[ #<p>]] [--blocks "..."] [--level scope\|goal\|squad]`, later `unpark Q<n>` or `resolve Q<n> --answer "..."`. They are kept in `open-questions.md` in the folder of their level, written only by `squad-inbox`; the Manager never waits on one, and the page only reads them. **Tasks** come from the scope's own definition, one rule for the page and `squad-report` (`bin/squadtickets.py`): the first source that has a task wins: the `tickets: <feature-slug>` line in `scope.md` if there is one (it names `.scratch/<feature-slug>/issues/`; an empty folder falls through); else `.scratch/<scope name>/issues/`; else the scope's own `tasks/NN.md` files; else a plan table. Nothing is guessed from other scopes' folders. The Tasks panel shows each task's title and the file it lives in. **Files** lists the squad folder's and the scope's `.scratch` folder's files too, and a click asks the board to run the local `code --goto <file>`, so VS Code shows the file in its own choice of window; if that fails (no VS Code, refused, 5 s timeout) the page follows the `vscode://file/<absolute path>` link instead (`vscode://vscode-remote/wsl+<distro>/<path>` when the board runs in WSL); the link's tooltip shows the path. **Demo:** `squad-board --demo [--port N] [--no-open]` runs the board on a temporary copy of the test fixture (sample data, labelled DEMO; HOME and `CLAUDE_CONFIG_DIR` point into the copy, removed on exit; nothing real is read or written). `squad-start` prints the board command and does not run it. See `docs/adr/0020-dashboard-replaces-removed-board.md`. |
| `bin/squad-spawn` | Opens a herdr tab, makes a git worktree for Developers (`.worktrees/<squad>/<scope>/<agent>`, branch `squad/<squad>/<scope>/<agent>`; `--base` starts it from a passed branch), starts `claude --agent squad:<role> --name <agent> --permission-mode auto --settings <role settings>` without the user's own plugins and skills (the lean start; `SQUAD_SPAWN_USER_CONFIG=1` restores them). Optional `.claude/squads/<squad>/settings/lean.json` `{"skills": [...], "plugins": [...], "mcp": [...]}` sets what every role of that squad keeps (default: skills playwright-cli and claude-accounts, no plugins, no MCP servers and no claude.ai connectors; list a server in `mcp` to keep it; `bin/squad-spawn --help` has the details) |
| `bin/squad-close` | `--scope S` retires a scope's agents, removes merged, clean worktrees (found by branch `squad/...`, wherever they sit) and moves the folder to `scopes/_done/`. `--goal G` does the same for a goal and refuses while a scope is open or its shared decisions were never promoted. With neither it archives the whole squad. Every branch is reported; none is deleted |
| `bin/squad-process` | `compose [role]`, `rule <ID>`, `who <ID>`, `lint`, `upgrade --check\|--apply`, `upstream` for the composed process (read-only except `upgrade --apply --yes`; `upstream` prints the proposed operations); skill `/squad:squad-process-update` drives it |
| `bin/processlint.py` | Lint the rule files against the Writing rule (`python3 bin/processlint.py`, exit 1 on a finding). |
| `bin/squad-respawn` | Replaces an agent's session with a fresh one from its notes; keeps its name, scope and worktree |
| `bin/squad-retire` | Asks an agent to save its notes, then closes its pane (worktree and branch are kept) |
| `bin/squad-usage` and the Stop hook | Token usage per agent, and the cost rules that tell an agent to start fresh. The table counts every session of an agent (matched by its `agent-name` record, so respawns are included) and its subagents' output tokens (`subagents` column); context, expiries, model/effort and `--check` read the main thread only. |
| `bin/squad-report`, `/squad:squad-report`, `/squad:squad-report-analyze` | Time and cost of a scope or goal (per task, role and bucket), derived from transcripts with no model call. `squad-report <scope>` writes `data.json` and `report.html` to `<scope>/report/` (local, git-ignored); `/squad:squad-report <scope>` builds it, `/squad:squad-report-analyze` answers questions from it. Example: `squad-report squad-report --squad plugin`. See `docs/adr/0014-squad-report-derives-from-transcripts.md`. |
| `skills/squad-init`, `skills/squad-start` | The two commands you run |
| `templates/squad/` | The standing layer: `process.local.md` (a squad's overlay), `project.md`, `process-log.md`, per-role `settings/*.json` |
| `templates/scope/`, `templates/goal/` | What `squad-start` copies into a new scope or goal |

`bin/` is on the Bash tool's PATH while the plugin is enabled, so the Manager runs `squad-spawn` as a plain command.

## Requirements

- Claude Code ≥ 2.1.224 (cross-session messaging), herdr, `jq`, `git`, `python3`.
- Start everything from a herdr pane (`HERDR_ENV=1`).
- **Trust the project folder once** in Claude Code. Worktrees live under `<project>/.worktrees/<squad>/`, so they inherit that trust; a worktree outside a trusted folder stops at the trust prompt.

## Safety defaults

- Every role runs in `auto` permission mode with `.claude/squads/<squad>/settings/<role>.json`.
- **Denied for every role:** `git push`, `git rebase`, `git reset --hard`, switching to `main`/`dev`, and every Jira/Confluence write tool. **`git merge` is denied for every role except Developers**, who may merge only inside their own branch (integration tasks), and the Manager, who merges into the PO's branch only when the PO asks.
- **QA blackbox** is also denied `Read` on the code folders, so it judges behaviour only. Shell reads aren't covered by `Read` rules; its instructions forbid them.
- Messages between sessions can't approve permissions. A `blocked` pane needs the PO.

## Known limits

- **Flat squads.** A squad created before the per-scope layout (a `roster.md` at its top, no `scopes/` folder) keeps working through the same scripts, which fall back to the flat layout and the older worktree paths. `squad-start` refuses one. The fallbacks are marked `legacy flat layout` and can go once such squads finish.
- **Desktop toasts.** `squad-notify` toasts when an agent waits, if herdr's `[ui.toast] delivery` is `"off"`. On Linux it sends an OSC 777 sequence to the herdr client terminal. On Windows it runs `herdr notification show` and reads the config from `%APPDATA%\herdr\config.toml`.
- **Cost:** every role is a full session, and every scope pays a fresh start (a Manager, plus a re-read of the project docs). Run `squad-usage` after real use to see what a scope costs.
- **Several Managers, several tabs.** Each running scope or goal has its own Manager tab that can block on you.
