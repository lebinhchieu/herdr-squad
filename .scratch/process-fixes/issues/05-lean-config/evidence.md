# Evidence: 05 lean-config

## Behaviour

### AC1 measure (before building)

claude 2.1.319, `claude -p "hi" --max-turns 1 --model haiku --output-format stream-json --verbose`, `init` event read with `jq`, cwd = this worktree. Lean flags = the spawn dry-run flags: `--settings <user settings.json minus plugin/skill/marketplace keys> --setting-sources project,local --add-dir <dir with the 2 kept skills> --plugin-dir <runtime>`. Only the init event is used; MCP status values are as claude printed them.

| Start | MCP servers in init (name:status:source) | `mcp__` tools |
|---|---|---|
| Plain, run 1 | atlassian:needs-auth:user, claude.ai Claude Docs:connected, claude.ai Atlassian MCP:needs-auth, claude.ai Adobe for creativity:needs-auth, claude.ai Microsoft 365:needs-auth, claude.ai Atlassian Rovo:connected | 49 |
| Plain, run 2 | same six, the two claude.ai ones `pending` | 0 at init |
| Lean, 10 runs | run 1: the five claude.ai connectors `pending`; runs 2-10: none listed | 0 |
| Lean, cwd has `.mcp.json` (`projprobe`) | projprobe:failed:project + five claude.ai connectors `pending` | 0 |
| Lean + `--mcp-config` (atlassian from `~/.claude.json`) | atlassian:needs-auth:dynamic | 0 |
| Lean + `--strict-mcp-config --mcp-config` same file, cwd has `.mcp.json` | atlassian:needs-auth:dynamic only | 0 |
| Plain + `--strict-mcp-config --mcp-config {}` | none | 0 |
| Lean + `enabledPlugins` {reply-style} in the `--settings` file | plugins: squad, reply-style, 5 cc-plugin-* | n/a |

Answer: the user MCP server in `~/.claude.json` does not reach a lean role (dropped with the user source); claude.ai connectors (Atlassian) showed up once in 10 lean runs, as `pending`; a project `.mcp.json` server does reach it. So MCP can leak: AC5 branch "restrict" (`mcp` key = `--strict-mcp-config` plus a generated `--mcp-config`).
