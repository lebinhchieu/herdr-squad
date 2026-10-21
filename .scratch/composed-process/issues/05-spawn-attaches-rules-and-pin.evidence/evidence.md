# Evidence 05: spawn attaches rules and pin

## Behaviour

Tests: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadruntime test_squad_spawn test_squad_respawn test_squad_start test_windows_safe test_squadprocess test_squadprocess_show test_squadprocess_apply test_squadcompose test_squadrules test_templates test_processlint`: 347 tests OK in the final run (385 with `test_templates` and `test_processlint`, run before the last small edits). `test_squadruntime` (43) builds a throwaway git copy of this plugin plus 04's fixture rule files (this branch has no converted rule files), a temp composed squad and a stub `herdr` that logs argv. The three existing spawn/respawn/start test files are unchanged and pass.

Design basis: `spike-runtime.md` (01) recommendation, `design.md §05` final decisions. Runtime = `git archive <sha>` into `$SQUAD_DIR/_runtime/<version>-<sha12>/` (via `tarfile`, no `tar` binary), temp folder then `os.rename`.

### Technical AC
1. **Argv and rules file.** `SpawnComposedTest.test_argv_has_the_rules_file_the_pinned_plugin_and_path`: `agent start … --plugin-dir <runtime> --append-system-prompt-file <home>/roles/<agent>.rules.md`, one `--plugin-dir`, one `--settings`, no `enabledPlugins`; tab env `SQUAD_PLUGIN_DIR=<runtime>` and `PATH=<runtime>/bin:…`; the file starts `# Your process rules`, header `agent: t-dev-sc1 · role: dev · scope: sc1 (size M …`, `plugin: <version> <sha>`.
2. **Legacy unchanged.** `test_legacy_layout_keeps_todays_argv_and_prompt` (no new flag, no `PATH`, prompt byte-identical, no `_runtime`); `StartComposedTest.test_the_legacy_layout_is_unchanged` (no `plugin:` line in `scope.md`). The 129 existing spawn/respawn/start/windows tests pass unchanged.
3. **Size change.** `RespawnComposedTest.test_a_size_change_…`: `size: M` → `S` → respawn gives `(size S`, back to `M` gives `(size M`, files differ; the RESPAWN prompt names `roles/<agent>.notes.md` only (no `process.md`, no `squad-process show`).
4. **Exits.** No `plugin:` line → exit 2 naming `plugin: <version> <sha>`; unparseable pin → 2; unknown commit or missing runtime → 1 naming the pin and `git -C <plugin checkout> archive <sha> | tar -x -C <runtime>`; a compose failure (`remove` of a missing ID) → 2. In each, the stub herdr log is empty, no worktree, no label file (spawn and respawn both).
5. **Live probe:** below.

### Added AC (design §05)
5. `--upload-pack=x`, `../x`, `abcdef` (6 chars), upper-case, 41 chars, and versions `../1`, `-x`, `1 2`, empty: exit 2, no `_runtime` folder (`PinTest`).
6. Two parallel builds: 4 threads behind a barrier leave one complete folder and no `.tmp-*`; a rename that loses to a pre-created target removes its temp and returns the target.
7. Commit holds plugin X, pin says Y: exit 1, nothing left. An existing runtime folder whose `plugin.json` differs: removed, exit 1.
8. No-repo fixture: `SQUAD_INSTALLED_PLUGINS` points at a fixture `installed_plugins.json` (real keys `installPath`, `version`, `gitCommitSha`, read from `~/.claude/plugins/installed_plugins.json`): matching sha returns the cache path and builds nothing; a different sha exits 1 with the restore command.
9. Live probe: below, init event shows `squad@inline`, `path` = the runtime.
10. With a materialised runtime (it holds `templates/scope/scope.md`): `squad-label`'s `homes_for_lookup` lists the squad and `sc1` only; `squadreport_build.resolve` refuses `_runtime` and finds `sc1`; `squad-start`'s overlap scan lists `sc1` only. The board was removed (ADR 0009), so there is no board scanner. `squad-inbox`/`squadinbox.py` take explicit paths and never list scopes (grep for `scopes`/`glob` finds nothing). `squad-close` and `squad-migrate` name `scopes/` but read fixed paths; `squad-close`'s whole-squad archive would carry `_runtime/` until the cleanup ticket. A static check shows no scanner script (label, report, inbox, start, usage, notify, log-message, retire, close) uses `rglob`, `os.walk` or `**` globs.

### BD1 before/after on a copy of the live squad (05-2)
The live squad folder (`$SQUAD_DIR`, `process.md`, no `process.local.md`) copied to `/tmp`, run with the plugin at 4's passed sha `7e2b83a` (`git archive`) and with this branch: `squad-spawn dev … --dry-run --prompt "Read process.md go"`, `squad-spawn manager … --goal composed-process --dry-run`, `squad-respawn <dev> --dry-run`, `squad-start "a task" --dry-run`, `squad-start "goal: g" --dry-run`, `squad-start x --in-goal composed-process --dry-run`. Session UUIDs, `prev-<pid>` and the plugin path normalised: `diff old.out new.out` = no diff (and no `--append-system-prompt-file` in either).
Respawn (`test_squadruntime`): a squad folder with neither file exits 1 `no squad folder` before any herdr call; a goal Manager (`GOAL_DIR`, `--goal`) recomposes with `scope: goal g1`, the Index and a notes-only prompt.

### Other behaviour
- **Mode** (`squad-process mode`): `process.local.md` → `composed`; `process.md` only → `legacy`; neither → `none` (`no squad folder`, as before). `squad-spawn`/`squad-respawn` decide this in bash with the same rule (existing tests use a stub plugin without `squad-process`); a `process.local.md`-only squad is found without `--squad`. `squad-process check` and squad-start's update notice are silent in composed mode.
- **Order in `squad-spawn`:** composed block (pin, runtime, compose) runs right after home resolution, before the Manager notice, worktree, `herdr agent get` and `squad-label --init`. `--dry-run` builds and writes nothing and prints the runtime path and the flag.
- **Prompt:** composed spawn appends `Your process rules are attached to this session (<file>); read no other process file.` (the string `process.md` appears nowhere in the prompt).
- **`squad-start`:** pin from the goal's `goal.md` for `--in-goal` (the squad's `plugin.pin` is ignored then), else `plugin.pin`, else running version and `git rev-parse HEAD`. A goal gets a `plugin:` line too. The line is inserted by code before the first `## ` heading, so legacy `scope.md`/`goal.md` and the templates are unchanged (Touches change: `templates/goal/goal.md` not edited, an empty `plugin:` line would make `read_home` raise). Warnings: older `plugin.pin` (`plugin.pin is 0.0.1, older than the installed plugin 0.4.1`, versions compared as numbers), dirty tree (`plugin tree has uncommitted changes, pin uses commit <sha> without them`); an unparseable `plugin.pin` exits 2; the runtime is built before anything is created, so a failure leaves no folder. `--resume` prompt in composed mode names the notes, not `process.md`.
- **Repo guard:** the plugin root counts as a repo only when `git rev-parse --show-toplevel` equals it. A runtime sits inside the project's repo; without the guard `git -C <runtime>` would find the project repo (`test_a_runtime_inside_a_repo_is_not_taken_for_the_plugin_repo`).
- **`compose --help`** (QAB nit): usage now shows `compose <role> --home D [--agent A] [--out F] …` next to the v6 form; the module doc lists `compose`, `mode`, `runtime`.
- **Not tested here:** Windows, a real marketplace install without a repo, and the Bash tool's `PATH` inside a session (as in 01). The pod's `PATH` is set with `herdr tab create --env PATH=…`; whether herdr's shell keeps it first is not verified by the stub.
- **Cleanup of `_runtime/`** is not in 05 (design §05): 4.6 MB per pin until the later `squad-close` ticket.

### Live probe (Haiku, temp squad)
Plugin copy in `/tmp/dev5probe/plugin` (git repo, fixture rule files, `CARD-PEAR-34.` appended to `agents/dev.md` and committed = the pin); squad `/tmp/dev5probe/proj/.claude/squads/t` with `process.local.md` adding rule `SQ-1` for `dev` whose body is `The marker phrase for the rules is RULES-MANGO-12.`; scope pin `0.4.1 982cb1b804cd…`. Real `squad-spawn dev t-dev-sc1 --scope sc1 --model haiku` with the stub herdr gave:

```
agent start t-dev-sc1 --kind claude --pane p1 --timeout 120000 -- --agent squad:dev --name t-dev-sc1 --session-id … --permission-mode auto --settings …/templates/squad/settings/dev.json --model haiku --effort medium --plugin-dir …/_runtime/0.4.1-982cb1b804cd --append-system-prompt-file …/scopes/sc1/roles/t-dev-sc1.rules.md
```

This is a **replay of that argv** with `claude -p` (the stub starts no session): same flags minus `--name/--session-id`, `PATH=<runtime>/bin:$PATH`, `--output-format stream-json --verbose`, `</dev/null`. Question: "Do your system instructions contain the exact phrase RULES-MANGO-12? And … CARD-PEAR-34? Reply exactly: RULES=YES|NO CARD=YES|NO. No tools."

```
init: {"squad":[{"name":"squad","path":"/tmp/dev5probe/proj/.claude/squads/t/_runtime/0.4.1-982cb1b804cd","source":"squad@inline","version":"0.4.1"}],"agents":["squad:dev"]}
result: RULES=YES CARD=YES      cost_usd=0.0036
control (same question, `--agent squad:dev` only, no pin, no rules file): RULES=NO CARD=NO   cost_usd=0.0032
```

Total spend $0.0068. The rules marker comes from the composed file, the card marker only from the pinned runtime's `agents/dev.md`; the init event names the runtime as the one `squad` plugin (`squad@inline`).
