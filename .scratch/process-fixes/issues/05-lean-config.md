# Task 05: per-squad settings/lean.json for the lean spawn

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 05`.

Status: ready
Source: Chieu E5 (2026-11-07): "okay, create the lean.json". Read lean-spawn's `tasks/01.md` Design notes (`scopes/lean-spawn/tasks/01.md`, a sibling scope's file, read only that file) for what is built.
Files: bin/squad-spawn, bin/squadruntime.py (only if needed), tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/05-lean-config.md` in your first commit.
Branch: work in the existing worktree `/home/chieule/workspace/squad/.worktrees/plugin/lean-spawn/plugin-dev-lean-spawn` (branch squad/plugin/lean-spawn/plugin-dev-lean-spawn, at 7778c9a, lean-spawn already built there). No merge, no new branch.

## AC
- AC1 Measure first, saved in evidence: with the spawn's exact flags, do user MCP servers (`~/.claude.json`, `.mcp.json`) and claude.ai connectors (Atlassian) reach a lean role? Record init-event counts or the MCP list, before and after.
- AC2 `.claude/squads/<squad>/settings/lean.json` with keys `skills` (names to copy from the user skills folder), `plugins` (user plugins to keep enabled), `mcp` (servers to keep). A key may be absent. No file = today's behaviour (skills playwright-cli and claude-accounts, no user plugins, MCP as AC1 measured).
- AC3 `squad-spawn` reads it for every role of that squad. A skill or plugin name that does not exist warns once and is skipped. Bad JSON or a wrong type refuses (exit 2) before anything starts.
- AC4 `SQUAD_SPAWN_USER_CONFIG=1` still restores the old start; dry run still builds nothing.
- AC5 If AC1 shows MCP servers leak into lean roles, `mcp` restricts them (for example `--strict-mcp-config` with a generated `--mcp-config` holding only the listed servers); if they do not leak, `mcp` lists the user servers to add back and the ticket says so.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run only touched test files plus `grep -rl` hits for touched `templates/` paths or printed strings. A change to text `bin/squad-spawn` prints needs the `grep -rl` over `tests/`.
- Do not bump the plugin version; the last scope does it once.
- Document `lean.json` in the usage text of `bin/squad-spawn` and one README or docs line where lean-spawn's `SQUAD_SPAWN_USER_CONFIG` is documented.

## Design notes
AC1 measured first (claude 2.1.319, `claude -p "hi" --output-format stream-json --verbose`, `init` event, cwd = this worktree; flags = the spawn's `--settings <merged user settings> --setting-sources project,local --add-dir <skills> --plugin-dir <runtime>`). Raw lines in evidence.md.
- Plain start: 6 MCP servers listed (user `atlassian` from `~/.claude.json`, 5 claude.ai connectors), 49 `mcp__` tools once connected.
- Lean start (`--setting-sources project,local`): 0 servers listed in 9 of 10 runs, 0 `mcp__` tools. The one other run listed the 5 claude.ai connectors as `pending` (0 tools at init). So the user `~/.claude.json` server does NOT reach a lean role, claude.ai connectors almost never do.
- Lean start with a `.mcp.json` in cwd: that project server loads (`source: project`), and the 5 claude.ai connectors show `pending` too. So MCP can reach a lean role through the project source. That is a leak.
- `--strict-mcp-config --mcp-config <file>`: only the file's servers (empty file: none, even with `.mcp.json` in cwd). `--mcp-config` alone adds the file's servers (`source: dynamic`), for example `atlassian` (`needs-auth`).
- A user plugin kept by `enabledPlugins` in the `--settings` file loads under `--setting-sources project,local` (tested: `reply-style` listed in plugins, no marketplace key needed).

Decision (AC5): MCP can leak through project `.mcp.json` and rarely claude.ai, so `mcp` restricts. Rule: key `mcp` present (even `[]`) adds `--strict-mcp-config --mcp-config <home>/roles/<agent>.mcp.json` holding exactly the listed servers; key absent adds no MCP flag (today's start, user servers already dropped). Strict also drops a project `.mcp.json`: documented in the usage text.

Design (bin/squad-spawn only; squadruntime.py needs no change):
1. File `$squad_dir/settings/lean.json`, read for every role of the squad. Read and checked early (before compose, worktree, label, herdr) when `SQUAD_SPAWN_USER_CONFIG` is not 1; one `jq` pass. Refuse (exit 2) on: not JSON, not an object, `skills`/`plugins`/`mcp` not an array of strings, a name outside `[A-Za-z0-9][A-Za-z0-9._@-]*`. An unknown key warns (a typo like `skill` would be silent otherwise). Absent key = default. Dry run reads and refuses too, builds nothing.
2. `skills`: replaces `lean_keep` (default playwright-cli, claude-accounts). From lean.json a name not found in the user skills folder warns once per spawn and is skipped; the default list stays silent (lean-spawn behaviour, tests read stderr).
3. `plugins`: names (`name` or `name@marketplace`) matched against `enabledPlugins` of the user `settings.json` (value true). Matches go back into the merged lean-settings file as `enabledPlugins`. No match warns once and is skipped. No user settings file: every name warns.
4. `mcp`: names looked up in `${CLAUDE_CONFIG_DIR:+$CLAUDE_CONFIG_DIR/}.claude.json` (else `~/.claude.json`) `mcpServers`, then `<cwd>/.mcp.json`. Found: copied into `roles/<agent>.mcp.json`. Not found: warns once, skipped (claude.ai connectors are not in a file, so they cannot be added back; they stay out).
5. `SQUAD_SPAWN_USER_CONFIG=1`: lean.json is not read, not validated, nothing added: the old start line, as in lean-spawn.
6. No lean.json: the `claude` arg list is the same as 7778c9a (test compares it).
Tests (tests/test_squad_spawn.py, extend): TAC1 no lean.json: the dry-run `claude` flag list equals the literal 7778c9a list; TAC2 three skills, lean.json lists two + one unknown: two copied, one warning, a bad file (bad JSON, wrong type) exits 2 with no worktree/herdr call and no `roles/` files; plugins re-enabled in the lean-settings file; mcp file written, `--strict-mcp-config` in the start line, absent `mcp` key adds none; `SQUAD_SPAWN_USER_CONFIG=1` ignores a bad lean.json; dry run builds nothing.

## Technical AC (QA whitebox)
- TAC1 No `lean.json` gives the same `claude` arg list as lean-spawn's 7778c9a (a test compares it).
- TAC2 A fake config dir with `lean.json` listing two of three skills copies exactly those two; an unknown name warns once, a bad file refuses before any worktree or herdr call.
- TAC3 Touched test files and `grep -rl` hits pass, nothing newly skipped; full suite once on the final sha by QA whitebox.
- TAC4 The spawn's exact flags show the kept skills/plugins/MCP in a real `init` event (QA whitebox reruns it once, read-only).
