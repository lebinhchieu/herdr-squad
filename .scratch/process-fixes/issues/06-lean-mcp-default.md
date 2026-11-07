# Task 06: lean start drops claude.ai connectors by default (mcp default [])

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 06`.

Status: ready
Source: Chieu E9 (b), 2026-11-07: lean roles drop the claude.ai connectors by default. Builds on task 05 (`tasks/05.md`, its Design notes and `.scratch/process-fixes/issues/05-lean-config/evidence.md`; the 05 Developer's notes: `roles/plugin-dev-lean-config.notes.md`).
Files: bin/squad-spawn, the README row and usage text for `lean.json`, tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/06-lean-mcp-default.md` in your first commit.
Branch: work in the existing worktree `/home/chieule/workspace/squad/.worktrees/plugin/lean-spawn/plugin-dev-lean-spawn` (branch squad/plugin/lean-spawn/plugin-dev-lean-spawn, at 2253a92). No merge, no new branch, no version bump.

## AC
- AC1 In the lean start (no `SQUAD_SPAWN_USER_CONFIG=1`), a missing `mcp` key (and no `lean.json` at all) now means `mcp: []`: `--strict-mcp-config` with a generated `--mcp-config` holding no servers. A listed `mcp` still adds only those servers.
- AC2 `SQUAD_SPAWN_USER_CONFIG=1` still restores the old start (no strict flag). Dry run still builds nothing.
- AC3 Usage text and the README row say the new default (no `mcp` key = no MCP servers, no claude.ai connectors; list a server to keep it).
- AC4 Tests: replace the 05 test that asserted "no file = lean-spawn's arg list" to expect the strict-MCP default; one test per AC at most.

## Rules to follow
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run touched test files plus `grep -rl` hits over `tests/` for changed strings.
- Save a short evidence note: one lean role started with the final flags shows no connector tools after a 25 s wait (as 05's AC1 did).

## Design notes
Measured in 05 (evidence.md there): claude.ai connectors reach a lean role late (25 s wait: 2 of 2 runs showed `mcp__claude_ai_Atlassian_Rovo__*`); `--strict-mcp-config --mcp-config {"mcpServers":{}}` showed none. So the default `mcp: []` is the existing strict path with an empty list.
Change (bin/squad-spawn, 1 line + text): `lean_has_mcp` starts at 1 instead of 0. The MCP block sits inside the lean branch only (`SQUAD_SPAWN_USER_CONFIG != 1`), so AC2 holds with no new code; the dry run already writes nothing (`[[ $dry == 1 ]] ||` guards). A missing file, a file without `mcp`, or `mcp: []` all give `{"mcpServers":{}}`; a listed `mcp` still adds only those servers (the loop is unchanged). The generated `roles/<agent>.mcp.json` is now written for every lean role (mode 600, git-ignored).
Text: usage text `mcp` bullet and the README row say: no `mcp` key = no MCP servers and no claude.ai connectors; list a server to keep it. The `SQUAD_SPAWN_USER_CONFIG` line is unchanged.
Tests (tests/test_squad_spawn.py): AC4 replace `test_lean_without_a_lean_json_keeps_the_lean_spawn_flag_list` by `test_lean_without_a_lean_json_defaults_to_no_mcp_servers` (exact flag list now ends with `--strict-mcp-config --mcp-config <roles/x.mcp.json>`, the real run writes `{"mcpServers":{}}`; with `SQUAD_SPAWN_USER_CONFIG=1` the existing restore test already asserts no strict flag: add the assert there). In the skills test, the line "no mcp key, no MCP flag" flips to assert the strict flag. In the mcp test the last step (`{"skills": []}` drops the file) flips: the file stays and holds no servers. Then `grep -rl` over `tests/` for `mcp`, `lean.json`, `strict-mcp`.
Evidence: 06 `evidence.md` with one real lean role started with the final flags, 25 s wait, no `mcp__` tools.

## Technical AC (QA whitebox)
- TAC1 With no `lean.json`, the `claude` arg list holds `--strict-mcp-config --mcp-config <file>` and the file has `{"mcpServers":{}}`; with `SQUAD_SPAWN_USER_CONFIG=1` it does not.
- TAC2 Touched test files and `grep -rl` hits pass, nothing newly skipped; full suite once on the final sha by QA whitebox.
- TAC3 The real `init` event of a default-started role shows no `mcp__` tools (QA whitebox reruns it once, read-only).

## Review
AC trace (evidence: `.scratch/process-fixes/issues/06-lean-mcp-default/evidence.md`, branch squad/plugin/lean-spawn/plugin-dev-lean-spawn):
- AC1 | `test_lean_without_a_lean_json_defaults_to_no_mcp_servers`, `test_lean_json_mcp_restricts_the_role_to_the_listed_servers`; evidence.md AC1 (real init + 25 s wait: 0 `mcp__` tools) | `cd tests && python3 -m unittest test_squad_spawn`
- AC2 | `test_user_config_env_restores_the_old_start`; dry-run asserts in the two tests above | same command
- AC3 | `bin/squad-spawn --help`, README row | read them; `grep -n "no MCP servers" bin/squad-spawn README.md`
- AC4 | the 05 flag-list test is replaced (same test, renamed, new expected list); one test per AC at most | same command

Known: `test_a_failed_agent_start_leaves_the_old_overrides_file` fails on base too. `test_ca_launchers.HarnessTest.test_scripts_are_syntactically_valid_bash` errors only when a `tools/claude-accounts/bin/__pycache__` left by an earlier run exists (ignored dir; passes with it removed or with `python3 -B`): unrelated to this change.

