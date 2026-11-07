# Evidence: 05 lean-config

## Behaviour

### AC1 measure (before building)

claude 2.1.319, `claude -p "hi" --max-turns 1 --model haiku --output-format stream-json --verbose`, `init` event read with `jq`, cwd = this worktree. Lean flags = the spawn dry-run flags: `--settings <user settings.json minus plugin/skill/marketplace keys> --setting-sources project,local --add-dir <dir with the 2 kept skills> --plugin-dir <runtime>`. Only the init event is used; MCP status values are as claude printed them.

| Start | MCP servers in init (name:status:source) | `mcp__` tools |
|---|---|---|
| Plain, run 1 | atlassian:needs-auth:user, claude.ai Claude Docs:connected, claude.ai Atlassian MCP:needs-auth, claude.ai Adobe for creativity:needs-auth, claude.ai Microsoft 365:needs-auth, claude.ai Atlassian Rovo:connected | 49 |
| Plain, run 2 | same six, the two claude.ai ones `pending` | 0 at init |
| Lean, 11 runs (init only) | run 1: the five claude.ai connectors `pending`; runs 2-11: none listed | 0 at init |
| Lean, wait 25 s (`python3 time.sleep` via Bash) then list `mcp__` tools, 2 runs | init `mcp_servers` empty; after the wait the model sees `mcp__claude_ai_Atlassian_Rovo__search`, `...searchJiraIssuesUsingJql`, `...updateConfluencePage` and more | yes, late |
| Lean + `--strict-mcp-config --mcp-config {}`, same wait | init empty; no `mcp__` tool after the wait | none |
| Lean, cwd has `.mcp.json` (`projprobe`) | projprobe:failed:project + five claude.ai connectors `pending` | 0 |
| Lean + `--mcp-config` (atlassian from `~/.claude.json`) | atlassian:needs-auth:dynamic | 0 |
| Lean + `--strict-mcp-config --mcp-config` same file, cwd has `.mcp.json` | atlassian:needs-auth:dynamic only | 0 |
| Plain + `--strict-mcp-config --mcp-config {}` | none | 0 |
| Lean + `enabledPlugins` {reply-style} in the `--settings` file | plugins: squad, reply-style, 5 cc-plugin-* | n/a |

Answer: the user MCP server in `~/.claude.json` does not reach a lean role (dropped with the user source); claude.ai connectors (Atlassian Rovo) DO reach a lean role, after init (2 of 2 runs that waited 25 s); a project `.mcp.json` server does reach it. So MCP can leak: AC5 branch "restrict" (`mcp` key = `--strict-mcp-config` plus a generated `--mcp-config`).

### After building (commit f69d1ce)

Method: a real `bin/squad-spawn dev dev-1 --scope s` against the test fake `herdr` in a temp legacy squad whose `settings/lean.json` is `{"skills":["playwright-cli"],"plugins":["reply-style","nope"],"mcp":["atlassian"]}`, user config = the real `~/.claude`. The logged `agent start` flags were then run with `claude -p` (2.1.319) from the project dir.

| AC | What I ran | What I saw |
|---|---|---|
| AC2 | the spawn above; `ls roles`, `cat roles/dev-1.mcp.json`, `stat -c %a` | `roles/` holds `dev-1.skills`, `dev-1.lean-settings.json`, `dev-1.mcp.json`; mcp.json is `{"mcpServers":{"atlassian":{"type":"http","url":"https://mcp.atlassian.com/v2/mcp"}}}`, mode 600. Flags added: `--strict-mcp-config --mcp-config <roles>/dev-1.mcp.json` after `--add-dir`. No lean.json: unit test `test_lean_without_a_lean_json_keeps_the_lean_spawn_flag_list` compares the full flag list. |
| AC3 | same spawn: `plugin 'nope'` is not in the user's enabledPlugins | one warning `plugin 'nope' is not enabled in ~/.claude/settings.json; skipped`, the spawn went on. Unknown skill, unknown MCP server, bad JSON and wrong types: unit tests (exit 2, no `roles/`, no herdr call). |
| AC4 | `SQUAD_SPAWN_USER_CONFIG=1` with a bad lean.json; dry run | unit tests `test_user_config_env_does_not_read_lean_json`, `test_lean_json_mcp_restricts_the_role_to_the_listed_servers` (dry run writes nothing) |
| AC5 | the logged flags with `claude -p`, `init` event | skills kept: `playwright-cli` (23 skills, no `claude-accounts` since not listed); plugins: `squad`, `reply-style`, 5 `cc-plugin-*`; MCP: `atlassian:needs-auth:dynamic` only. Same flags, `python3 time.sleep(25)` then list `mcp__` tools: answer NONE, 0 `mcp__` lines in the stream (before: the lean run with no `mcp` key listed `mcp__claude_ai_Atlassian_Rovo__*`). |

Without an `mcp` key a lean role still gets the claude.ai connectors late (measured above). That is today's behaviour (AC2 says no file = no change); a squad that wants them out writes `"mcp": []`.
