# Task 01: Fix 1: squad-spawn starts role sessions without user-level plugins and skills

Duties: design notes: Developer (here, in this file); technical AC: QA whitebox with the Developer; business AC: the ticket as written; `promote.md`: none (goal promotes in its last scope); full suite: QA whitebox, once on the final sha. A risk flag, user-visible change or business doubt: `BLOCKED 01`.

Status: ready
Source: `git show squad/plugin/process-audit/plugin-dev-process-audit-6:.scratch/process-audit/report.md` (6f500f8, unmerged), section 4 finding 1. Read only that finding.
Files: bin/squad-spawn, bin/squadruntime.py, tests for them
Ticket: commit this file's content as `.scratch/process-fixes/issues/01-spawn-lean.md` in your first commit.
Base: main.

## AC
- AC1 A role session started by squad-spawn gets no user-level plugins, skills or agent-types list; only the squad plugin, playwright-cli and claude-accounts remain.
- AC2 The three kept ones still work in a spawned session (test or capture shows each loads).
- AC3 Existing spawn behaviour (flags, settings order, roster row) is unchanged; touched test files pass.

## Rules to follow
- [REV-15] report deliverable: copy any report into `$SCOPE_DIR/evidence/{n}/` at the handed-in sha.
- SQ-2: `## Review` starts with an AC trace, one line per AC: `AC<n> | test or capture file | how run`.
- Repo CLAUDE.md "Running tests": run only touched test files plus `grep -rl` hits for touched `templates/` paths or printed strings.
- Do not bump the plugin version; the last scope does it once.

## Design notes
Tested on claude 2.1.319 with `claude -p ... --output-format stream-json --verbose` (the `init` event lists skills, plugins, agents):
- Plain start: 77 skills, 17 plugins, 18 agent types. `--setting-sources project,local` (no `user`): 19 skills (Claude's built-ins), 5 built-in plugins, 6 agent types. User skills (`~/.claude/skills`) and user plugins go with the `user` source.
- `--add-dir <dir>` where `<dir>/.claude/skills/<name>` exists adds that skill by its plain name. Tested with playwright-cli and claude-accounts: both listed.
- `--plugin-dir <squad plugin>` still loads the squad plugin under `--setting-sources project,local`.

Design (bin/squad-spawn only; bin/squadruntime.py needs no change, its one `claude` mention is the plugin-install lookup):
1. Add `--setting-sources project,local` to `claude_args`. The spawn's own `--settings <role file>` still applies (a flag file is not a source).
2. Keep list `lean_keep=(playwright-cli claude-accounts)`. At a real spawn, build `<home>/roles/<agent>.skills/.claude/skills/<name>` as a copy (`cp -RL`, so a symlinked skill works and Windows needs no symlink right) of `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/<name>`; a skill missing there is skipped silently (a warning broke tests that check stderr, and a user may lack one). Rebuilt every spawn, so a respawn (squad-respawn calls squad-spawn) picks up the same. Pass `--add-dir <that dir>`. Dry run builds nothing and prints the flags.
3. Escape hatch: env `SQUAD_SPAWN_USER_CONFIG=1` keeps today's behaviour (no `--setting-sources`, no `--add-dir`, no merged settings).
3b. (Manager FINAL 01) Dropping the user source also drops the user's hooks, permission rules and env, which must stay. `--settings` takes one file (the last wins), so the spawn writes `roles/<agent>.lean-settings.json` = user `settings.json` minus plugin/skill/marketplace keys, merged with the role's settings (objects by key, arrays joined deduplicated, role scalars win), and passes it as `--settings`. No or bad user file: the role's file alone. Tests in test_squad_spawn.py; six test_squadsettings tests get an empty CLAUDE_CONFIG_DIR so `--settings` stays the role's file.
4. The squad plugin is not touched: it still loads through `--plugin-dir` (composed) or the installed plugin (legacy squads: legacy spawns have no `--plugin-dir`, and `--setting-sources` without `user` would drop an installed squad plugin enabled in user settings). So for legacy mode pass `--plugin-dir $plugin_root` too, when the lean flags are on.
Tests: tests/test_squad_spawn.py: dry run has `--setting-sources project,local` and `--add-dir` ending `.skills`; real spawn builds the dir with the two skills (fake config dir holding three, only two copied) and a missing one is skipped; `SQUAD_SPAWN_USER_CONFIG=1` has neither flag. The existing `assertNotIn("--plugin-dir")` legacy tests change to match point 4 (also tests/test_squad_respawn.py and tests/test_squadruntime.py, one assertion each). Capture of a real claude init event with the spawn's exact flags goes in evidence (AC2).

## Review
AC trace (evidence: `.scratch/process-fixes/issues/01-spawn-lean/evidence.md`):
- AC1 | evidence.md AC1 (real `claude -p` init event: 77 -> 26 skills, 17 -> 6 plugins, 18 -> 16 agent types); tests/test_squad_spawn.py `test_lean_dry_run_drops_the_user_source_and_adds_the_kept_skills_dir`, `test_lean_real_spawn_copies_only_the_two_kept_skills` | `cd tests && python3 -m unittest test_squad_spawn`
- AC2 | evidence.md AC2 (init event lists claude-accounts, playwright-cli, squad plugin); `test_lean_real_spawn_copies_only_the_two_kept_skills`, `test_lean_real_spawn_skips_a_kept_skill_the_user_lacks_without_noise` | same command
- AC3 | `test_lean_settings_file_merges_the_users_hooks_permissions_env_but_not_plugins`, `test_lean_settings_skips_an_unparsable_user_file_with_one_warning`, `test_user_config_env_restores_the_old_start`, the unchanged role/settings/roster tests; test_squad_respawn, test_squadruntime and 13 other spawn-related files pass | `cd tests && python3 -m unittest test_squad_spawn test_squad_respawn test_squadruntime ...` (list in evidence.md)

Known: `test_a_failed_agent_start_leaves_the_old_overrides_file` fails on base too (verified on a `git archive HEAD` copy). Not touched.
Resolved by Manager ruling FINAL 01: the user's hooks, permission rules and env are kept through a merged `--settings` file (evidence.md); the RTK hook is back (tested). Opt-out `SQUAD_SPAWN_USER_CONFIG=1`. A kept skill the user lacks is skipped silently, so a role can start without playwright-cli and nothing says so.

## Technical AC (QA whitebox)
- TAC1 `SQUAD_SPAWN_USER_CONFIG=1` gives the same `claude` arg list as base (a test compares it); default adds only `--setting-sources project,local`, `--add-dir <home>/roles/<agent>.skills`, and for legacy mode `--plugin-dir`.
- TAC2 Dry run writes nothing to disk; a real spawn rebuilds the `.skills` dir each time (a stale skill is removed), and only names in the keep list are copied.
- TAC3 Whatever the Developer does to keep the user's settings (hooks, permissions, env) is covered by a test and shown in `evidence.md`.
- TAC4 Touched test files and `grep -rl` hits pass, nothing newly skipped; full suite once on the final sha by QA whitebox.
- TAC5 The spawn's exact flags show the kept three in a real `init` event (QA whitebox reruns it once, read-only).
