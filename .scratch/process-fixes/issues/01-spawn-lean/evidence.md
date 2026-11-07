# Evidence: 01 spawn-lean

## Behaviour

Method: a real `bin/squad-spawn dev dev-1 --scope s` against the test fake `herdr` (tests/squadtest.py) in a temp squad; the logged `agent start` flags were then run with a real `claude -p "hi" --max-turns 1 --output-format stream-json --verbose` (claude 2.1.319) and the `init` event read with `jq`.

Flags the spawn logged (after `--`):
`--agent squad:dev --name dev-1 --permission-mode auto --settings <squad>/roles/dev-1.lean-settings.json --model sonnet --effort medium --setting-sources project,local --add-dir <squad>/roles/dev-1.skills --plugin-dir <repo> --append-system-prompt-file <squad>/roles/dev-1.rules.md`

| AC | What I ran | What I saw |
|---|---|---|
| AC1 | `claude -p` with a plain start (no new flags), then with the spawn's flags; `jq '{n_skills, plugins, agents}'` of the init event | Plain: 77 skills, 17 plugins, 18 agent types (user skills, `mattpocock-skills:*`, `anthropic-skills:*`, `jira-ticket-breakdown`, ...). Lean: 26 skills (Claude's built-ins, the 5 squad skills, the 2 kept), plugins `squad` + 5 built-in `cc-plugin-*`, 16 agent types (the built-ins and `squad:*`). No user plugin, user skill or user agent left. |
| AC2 | same lean init event | `skills` contains `claude-accounts` and `playwright-cli` (loaded from `roles/dev-1.skills/.claude/skills/`, copies of `~/.claude/skills/*`); `plugins` contains `squad`; the session started as `--agent squad:dev`, so the squad plugin and `--settings` work (see the merged-settings section below). `tests/test_squad_spawn.py::test_lean_real_spawn_copies_only_the_two_kept_skills` checks the copy. |
| AC3 | `python3 -m unittest` in tests/: test_squad_spawn, test_squad_respawn, test_squadruntime, test_windows_safe, test_team_models, test_squad_start, test_utf8_helpers, test_crlf_squad_files, test_old_language_inventory, test_instructions, test_templates, test_squadsettings, test_squad_manager_guard, test_team_lead_perms, test_winlaunch | All pass except `test_a_failed_agent_start_leaves_the_old_overrides_file`, which fails the same way on the base commit (checked on a `git archive HEAD` copy). Flag order and settings are unchanged: the new flags sit after `--effort` and before `--plugin-dir`. |

Opt-out: `SQUAD_SPAWN_USER_CONFIG=1` gives the old start line (test `test_user_config_env_restores_the_old_start`).

Checked from the worktree as cwd (where a real Developer starts): the repo has no `.claude/settings*.json` with `enabledPlugins` and no `.claude/skills`; the same lean init event gave 26 skills, none of the user's (`mattpocock-skills`, `anthropic-skills`, `graphify`, `herdr`, `visual-answer`, `frontend-design`, `b2be-po-assistant`, `blueprint-*` all absent), 16 agent types, no `jira-*` agent.

User settings kept (Manager ruling FINAL 01: the brief drops only plugins and skills). `--setting-sources project,local` alone also dropped the user's `settings.json` (RTK hook, permission rules, env; tested). So squad-spawn now writes `<home>/roles/<agent>.lean-settings.json` = the user's `settings.json` without any key matching plugin/skill/marketplace (`enabledPlugins`, `extraKnownMarketplaces`), merged with the role's settings (objects by key, arrays joined without duplicates, the role's scalars win), and passes that as the one `--settings` (a second `--settings` replaces the first: tested with a probe env var, last wins).

Re-run with the real user settings, real spawn flags, cwd = worktree (claude 2.1.319):
- Merged file: keys include `env`, `hooks` (12 events), `permissions` (44 allow rules = 25 user + role's, deduplicated), no `enabledPlugins`.
- Init event: 24 skills (no user skills; `claude-accounts`, `playwright-cli` listed), plugins `squad` + 5 built-in `cc-plugin-*`, 16 agent types. Plugin and skill counts stay low.
- Hook back: `rtk gain --history` counted 1 `git log` entry before and 2 after a `claude -p "Run exactly: git log --oneline -3"` with the lean flags (before this change the count stayed at 0).
- User `~/.claude/CLAUDE.md` still loads (earlier test: the name "Chieu").

Opt back in to the old start (user source, no merge): `SQUAD_SPAWN_USER_CONFIG=1`. A kept skill the user lacks is skipped without a message. A user `settings.json` that is not JSON: one warning, the role's settings alone.
