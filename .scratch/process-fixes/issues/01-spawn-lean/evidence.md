# Evidence: 01 spawn-lean

## Behaviour

Method: a real `bin/squad-spawn dev dev-1 --scope s` against the test fake `herdr` (tests/squadtest.py) in a temp squad; the logged `agent start` flags were then run with a real `claude -p "hi" --max-turns 1 --output-format stream-json --verbose` (claude 2.1.319) and the `init` event read with `jq`.

Flags the spawn logged (after `--`):
`--agent squad:dev --name dev-1 --permission-mode auto --settings <repo>/templates/squad/settings/dev.json --model sonnet --effort medium --setting-sources project,local --add-dir <squad>/roles/dev-1.skills --plugin-dir <repo> --append-system-prompt-file <squad>/roles/dev-1.rules.md`

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | `claude -p` with a plain start (no new flags), then with the spawn's flags; `jq '{n_skills, plugins, agents}'` of the init event | Plain: 77 skills, 17 plugins, 18 agent types (user skills, `mattpocock-skills:*`, `anthropic-skills:*`, `jira-ticket-breakdown`, ...). Lean: 26 skills (Claude's built-ins, the 5 squad skills, the 2 kept), plugins `squad` + 5 built-in `cc-plugin-*`, 16 agent types (the built-ins and `squad:*`). No user plugin, user skill or user agent left. |
| AC2 | same lean init event | `skills` contains `claude-accounts` and `playwright-cli` (loaded from `roles/dev-1.skills/.claude/skills/`, copies of `~/.claude/skills/*`); `plugins` contains `squad`; the session started as `--agent squad:dev`, so the squad plugin and `--settings` work. `tests/test_squad_spawn.py::test_lean_real_spawn_copies_only_the_two_kept_skills` checks the copy. |
| AC3 | `python3 -m unittest` in tests/: test_squad_spawn, test_squad_respawn, test_squadruntime, test_windows_safe, test_team_models, test_squad_start, test_utf8_helpers, test_crlf_squad_files, test_old_language_inventory, test_instructions, test_templates, test_squadsettings, test_squad_manager_guard, test_team_lead_perms, test_winlaunch | All pass except `test_a_failed_agent_start_leaves_the_old_overrides_file`, which fails the same way on the base commit (checked on a `git archive HEAD` copy). Flag order and settings are unchanged: the new flags sit after `--effort` and before `--plugin-dir`. |

Opt-out: `SQUAD_SPAWN_USER_CONFIG=1` gives the old start line (test `test_user_config_env_restores_the_old_start`).

Checked from the worktree as cwd (where a real Developer starts): the repo has no `.claude/settings*.json` with `enabledPlugins` and no `.claude/skills`; the same lean init event gave 26 skills, none of the user's (`mattpocock-skills`, `anthropic-skills`, `graphify`, `herdr`, `visual-answer`, `frontend-design`, `b2be-po-assistant`, `blueprint-*` all absent), 16 agent types, no `jira-*` agent.

What dropping the `user` source costs (tested, claude 2.1.319, cwd = worktree):
- User `~/.claude/CLAUDE.md`: **still loads**. Asked "what name do you call the user?" with `--setting-sources project,local`: answer "Chieu" (same as a plain start).
- User hooks, e.g. the RTK `PreToolUse` hook: **dropped**. `claude -p "Run exactly: git log --oneline -3"`: `rtk gain --history` counted 0 `git log` entries after the lean run and 1 after the plain run. A spawned role loses RTK's output shrinking.
- User permission allow rules and user `env`: dropped with the same source (inherent to the flag). The role's own `--settings` file (permissions in the template) still applies.

Opt back in with `SQUAD_SPAWN_USER_CONFIG=1`. A kept skill the user does not have is skipped without a message.
