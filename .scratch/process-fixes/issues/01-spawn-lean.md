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
2. Keep list `lean_keep=(playwright-cli claude-accounts)`. At a real spawn, build `<home>/roles/<agent>.skills/.claude/skills/<name>` as a copy (`cp -RL`, so a symlinked skill works and Windows needs no symlink right) of `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/<name>`; a skill missing there is skipped with a warning. Rebuilt every spawn, so a respawn (squad-respawn calls squad-spawn) picks up the same. Pass `--add-dir <that dir>`. Dry run builds nothing and prints the flags.
3. Escape hatch: env `SQUAD_SPAWN_USER_CONFIG=1` keeps today's behaviour (no `--setting-sources`, no `--add-dir`). Needed because dropping the user source also drops the user's own hooks, permissions and env for spawned roles; the PO can turn it back on.
4. The squad plugin is not touched: it still loads through `--plugin-dir` (composed) or the installed plugin (legacy squads: legacy spawns have no `--plugin-dir`, and `--setting-sources` without `user` would drop an installed squad plugin enabled in user settings). So for legacy mode pass `--plugin-dir $plugin_root` too, when the lean flags are on.
Tests: tests/test_squad_spawn.py: dry run has `--setting-sources project,local` and `--add-dir` ending `.skills`; real spawn builds the dir with the two skills (fake HOME holding both) and a missing one warns; `SQUAD_SPAWN_USER_CONFIG=1` has neither flag. The existing `assertNotIn("--plugin-dir")` legacy tests change to match point 4. Capture of a real claude init event with the spawn's exact flags goes in evidence (AC2).
