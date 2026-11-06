# Evidence: 01 spawn-lean

## Behaviour

Method: a real `bin/squad-spawn dev dev-1 --scope s` against the test fake `herdr` (tests/squadtest.py) in a temp squad; the logged `agent start` flags were then run with a real `claude -p "hi" --max-turns 1 --output-format stream-json --verbose` (claude 2.1.319) and the `init` event read with `jq`. The user's own config has 9 user skills, 17 plugins, 3 user agents.

Flags the spawn logged (after `--`):
`--agent squad:dev --name dev-1 --permission-mode auto --settings <repo>/templates/squad/settings/dev.json --model sonnet --effort medium --setting-sources project,local --add-dir <squad>/roles/dev-1.skills --plugin-dir <repo> --append-system-prompt-file <squad>/roles/dev-1.rules.md`

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | `claude -p` with a plain start (no new flags), then with the spawn's flags; `jq '{n_skills, plugins, agents}'` of the init event | Plain: 77 skills, 17 plugins, 18 agent types (user skills, `mattpocock-skills:*`, `anthropic-skills:*`, `jira-ticket-breakdown`, ...). Lean: 26 skills (Claude's built-ins, the 5 squad skills, the 2 kept), plugins `squad` + 5 built-in `cc-plugin-*`, 16 agent types (the built-ins and `squad:*`). No user plugin, user skill or user agent left. |
| AC2 | same lean init event | `skills` contains `claude-accounts` and `playwright-cli` (loaded from `roles/dev-1.skills/.claude/skills/`, copies of `~/.claude/skills/*`); `plugins` contains `squad`; the session started as `--agent squad:dev`, so the squad plugin and `--settings` work. `tests/test_squad_spawn.py::test_lean_real_spawn_copies_only_the_two_kept_skills` checks the copy. |
| AC3 | `python3 -m unittest` in tests/: test_squad_spawn, test_squad_respawn, test_squadruntime, test_windows_safe, test_team_models, test_squad_start, test_utf8_helpers, test_crlf_squad_files, test_old_language_inventory, test_instructions, test_templates, test_squadsettings, test_squad_manager_guard, test_team_lead_perms, test_winlaunch | All pass except `test_a_failed_agent_start_leaves_the_old_overrides_file`, which fails the same way on the base commit (checked on a `git archive HEAD` copy). Flag order and settings are unchanged: the new flags sit after `--effort` and before `--plugin-dir`. |

Opt-out: `SQUAD_SPAWN_USER_CONFIG=1` gives the old start line (test `test_user_config_env_restores_the_old_start`).

Trade-off Chieu should know: `--setting-sources project,local` also drops the user's own `~/.claude/settings.json` for a spawned role: user hooks (e.g. the RTK rewrite hook), user permission rules and user `env`. Roles keep the squad's `--settings` file. Set `SQUAD_SPAWN_USER_CONFIG=1` to get them back.
