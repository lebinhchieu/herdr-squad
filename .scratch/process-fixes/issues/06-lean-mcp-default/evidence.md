# Evidence: 06 lean mcp default

## Behaviour

Method: a real `bin/squad-spawn dev dev-1 --scope s` in a scratch git project with a legacy squad (`process.md`, `scope.md`), the test fake `herdr`, and **no `settings/lean.json`** (user config = the real `~/.claude`, which has the `atlassian` server and five claude.ai connectors). The logged `agent start` flags were then run with `claude -p` (2.1.319, haiku, `--output-format stream-json --verbose`) from the project dir, with `python3 time.sleep(25)` first, then "list every `mcp__` tool".

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | the spawn above; `cat roles/dev-1.mcp.json`; the logged flags | `roles/dev-1.mcp.json` = `{"mcpServers":{}}`; flags hold `--strict-mcp-config --mcp-config <roles>/dev-1.mcp.json` between `--add-dir` and `--plugin-dir`. Unit test `test_lean_without_a_lean_json_defaults_to_no_mcp_servers`. A listed `mcp` still adds only those servers: `test_lean_json_mcp_restricts_the_role_to_the_listed_servers` (unchanged asserts). |
| AC1 (real role) | `claude -p` with the logged flags; wait 25 s (the Bash call ran, 28.5 s total); `jq` of the `init` event and the stream | init: `mcp_servers` `[]`, 0 `mcp__` tools; model answer after the wait: `NONE`; `grep -c mcp__` over the whole stream: 0. (05 measured the same wait WITHOUT strict: `mcp__claude_ai_Atlassian_Rovo__*` appeared.) |
| AC2 | `test_user_config_env_restores_the_old_start` (now also asserts no `--strict-mcp-config` and no `roles/dev-1.mcp.json`); dry run in `test_lean_without_a_lean_json_defaults_to_no_mcp_servers` and `..._mcp_restricts...` | old start has no strict flag; dry run writes no `roles/` file |
| AC3 | `bin/squad-spawn --help` (the `mcp` bullet); README row | both say: no `mcp` key = no MCP servers and no claude.ai connectors; list a server to keep it |
| AC4 | `cd tests && python3 -m unittest test_squad_spawn test_ca_launchers test_squadsettings` | see the ticket's Review |
