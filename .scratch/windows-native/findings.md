# squad plugin 0.6.1 on native Windows: issue list for handoff

**Bottom line:** on this machine (Windows 11, Git for Windows bash, herdr 0.9.3, python3 3.14) `squad-start` cannot open a Manager tab (blocker W1), and the plugin's own test suite cannot verify the shell scripts on Windows (W2). Seven more issues are below, ranked. W1 to W4 should be fixed before anyone relies on the plugin here.

Plugin under test: `squad@herdr-squad` 0.6.1, commit `d8fce090c57c4931406c64b4107e22dff32f7663`, installed from the marketplace cache (not a git checkout).

How found: ran `squad-init`, `upgrade`, `squad-start` for real; reran `squad-start` in a throwaway project with a `herdr` shim that logs argv; called hooks and helper scripts directly; ran `tests/` with `python -m unittest` (1574 tests). Anything not listed was not tested.

## Blockers

### W1. `squad-start` / `squad-spawn` fail: `tab_create_failed … cannot find the file specified`
- **Where:** `bin/squad-spawn:199` `runtime_env=(--env "PATH=$runtime/bin:$PATH")`, sent at `:329` (`herdr tab create … "${env_args[@]}"`).
- **Cause:** in a composed squad `$runtime` is the Windows-form output of `squad-process runtime` (`C:\Users\…\squad\0.6.1`, backslashes, because it falls back to the installed cache). The value is `C:\…\0.6.1/bin:/c/Users/…:…`: a drive-letter path followed by a POSIX colon list. Git Bash's argument conversion does not rewrite it, so herdr (a native exe) hands `CreateProcessW` a PATH with no usable entries, and `pwsh.exe` is not found. The error text shows `\0` after the cwd; that is only the wide-string terminator, not the cause.
- **Proof:** `herdr tab create --env "PATH=/c/…/bin:$PATH"` works; `--env "PATH=C:/…/bin:$PATH"` fails every time. A shim showed argv `PATH=C:\Users\84084\.claude\plugins\cache\herdr-squad\squad\0.6.1/bin:/tmp/…`. Presetting `runtime=` in the environment does not help: the script resets `runtime=""` at line 101.
- **Fix:** build the value from a POSIX path: `rt_posix=$(cygpath -u "$runtime" 2>/dev/null || printf '%s' "$runtime")` then `--env "PATH=$rt_posix/bin:$PATH"` (let the MSYS conversion produce the `;` list). Same for any other `--env` that carries a path list.
- **Test to add:** a shim `herdr` on PATH (as above) asserting the `PATH=` value has no `C:\` or mixed form.
- **Also affects:** every later `squad-spawn` run by a Manager, since each hits line 199.

### W2. The plugin's test suite cannot run on Windows, so the shell scripts are unverified there
- **Run:** `cd tests && python -m unittest discover -p "test_*.py"` gave `Ran 1574, failures=410, errors=32, skipped=202` after I worked around the harness. `tests/run_suite.py` itself needs `fcntl`.
- **Causes (all in tests, none shown to be a product bug):**
  1. Tests call extensionless scripts directly (`subprocess.run([".../bin/squad-spawn", …])`): `WinError 193`. About 450 errors before any workaround.
  2. Tests that call bare `["bash", script]` get `C:\Windows\System32\bash.exe` (the WSL launcher): CreateProcess searches System32 before PATH. Result: `/bin/bash: C:/…/squad-spawn: No such file or directory`, exit 127. `squad-start` already avoids this with `pick_bash`; the tests do not use it.
  3. `test_squad_start.py` and `test_utf8_helpers.py` pass `bytes` argv/env to `subprocess` (`enc = lambda x: str(x).encode(...)`), which Windows rejects: `TypeError: bad argument type for built-in operation`, about 70 tests.
  4. `os.openpty`, `os.symlink` (needs privilege, `WinError 1314`), `termios` and POSIX-path fixtures: the plugin's `tests/RUNNING-ON-WINDOWS.md` lists some of these; the list is out of date and covers only the inbox files.
- **I did not get a clean signal** on `squad-spawn`, `squad-close`, `squad-respawn`, `squad-retire`, `squad-label` and the hooks from the suite. What I ran by hand: `squad-start` end to end with a shim (works apart from W1), `squad-path-guard`, `squad-usage-hook`, `squad-log-message`, `squad-notify` (exit 0), `squad-process runtime/scaffold/upgrade/lint`.
- **Fix:** one `tests/winlaunch.py` helper (`run_script(path, …)` using the same `pick_bash`/shebang logic as `squad-start`, `str` argv on `nt`), used by every test; then re-triage what is left.

### W3. `squad-process scaffold` and `upgrade` refuse on every marketplace install
- **Symptom:** `cannot pin the running plugin (…\0.6.1 is not a git checkout); write {squad dir}/plugin.pin as <version> <sha>`.
- **Cause:** `bin/squadruntime.py:104` `running_pin()` needs `git rev-parse HEAD` in the plugin root; the installed cache has no `.git`. Not Windows-only. `materialise()` already falls back to `_installed_cache()` (reads `installed_plugins.json` `gitCommitSha`); `running_pin()` does not.
- **Also:** `upgrade --check` then needs `--old-root` when the old pinned runtime was never built (`the pinned runtime is missing`), and `squad-init`'s SKILL does not mention `--new-pin` or `--old-root`.
- **Fix:** `running_pin()` falls back to `_installed_cache`'s entry (version + sha); `upgrade` uses the old installed cache as `--old-root` by default. Until then, the init/upgrade skills must say how to pass `--new-pin`.
- **Workaround used here:** `--new-pin "0.6.1 <sha from installed_plugins.json>" --old-root <cache>/0.6.0`.

## Should fix

### W4. Desktop notifications never fire on Windows
- `bin/squad-notify` finds the client tty through `/proc` (absent) and reads `~/.config/herdr/config.toml`; herdr on Windows keeps its config in `%APPDATA%\herdr\config.toml` (present here). It exits 0 quietly, so nothing signals the gap. The PO gets no "agent waiting" toast.
- **Fix:** read `%APPDATA%\herdr` first on `nt`; find a Windows way to toast (herdr CLI?) or document the gap in the README.

### W5. `flock` is missing in Git Bash
- `bin/squad-log-message:72` and `bin/squad-usage-hook:41` do `{ flock 9 2>/dev/null; printf … >&9; }`. With no `flock`, concurrent hooks append to `*.jsonl` unlocked (`command -v flock` fails here). Probably harmless for short lines, but unproven; the hook is silent either way.
- **Fix:** document, or lock from Python (`msvcrt`) as `squadinbox.py` already does.

### W6. The bare-name `bash` trap lives only in `squad-start`
- `pick_bash` (squad-start) is correct. Any other Windows entry point that spawns `bash` by name (docs, skills, the inbox mod, future code) gets the WSL launcher. Put `pick_bash` in `squadio.py` and add a test that greps `bin/` and `hooks/` for a bare `"bash"` in `subprocess` calls.

### W7. Installed cache is 33 MB, 29 MB of it the plugin's own dev state
- `git ls-files` shows 4007 tracked files under `.claude/` (`squad-backups/`, nested `_runtime/<old version>/` copies of whole old plugins) plus 88 under `.scratch/`. Every user installs them. On Windows the longest tracked path is 166 chars; under `~/.claude/plugins/cache/herdr-squad/squad/0.6.1/` (about 75) it stays near 240 of the 260 limit, and `_runtime` extraction or a deeper project root would break it (`LongPathsEnabled` could not be read here: registry access is blocked).
- **Fix:** untrack `.claude/squad-backups`, `.claude/squads`, `.scratch/_done`; keep them in a separate dev repo or release assets. Check `.claude-plugin` packaging excludes them.

## Notes and unverified

- **W8. Shell mismatch:** herdr opens the tab in `pwsh`, but every plugin script is bash. They work because Claude Code's Bash tool is Git Bash and inherits PATH. Verify `hooks/hooks.json` runs under bash (not PowerShell) on this Claude Code build: the commands are `"${CLAUDE_PLUGIN_ROOT}/bin/…"` with no `shell:` key. I ran the same command text through `bash -c` with a backslash path and it worked; the real hook runner was not exercised.
- **W9. Mixed path forms:** `squad-start` exports `SQUAD_DIR=C:/…` (from `Path.as_posix()`) while `squad-spawn` computes `/c/…` via `readlink -f`; `SQUAD_PLUGIN_DIR` is backslashes. All worked in the paths I tried, but any `[[ $a == $b ]]` comparison between them would fail. `squad-path-guard` normalises case and separators correctly (checked with `C:\`, `C:/`, relative); a POSIX `/tmp/…` target on native Python resolves to `C:\tmp` and is allowed.
- **W10. cwd case:** `~/.claude/projects` holds both `C--Users-84084-Workspace-Guardian---Learn` and `…-workspace-…` for the same folder. `squadtranscript.agent_sessions` matches project folders by name; usage/report rows may miss sessions started with a different drive-path case. Not reproduced.
- **W11. One-off:** Git Bash printed `fatal error - add_item ("\??\C:\Program Files\Git", "/", ...) failed, errno 1` once while a background test run was active. Not reproduced; likely a cygwin mount-table race when many bash processes start at once. Worth knowing for parallel `squad-spawn`.
- **Fine on Windows (checked):** `python3` via Node `spawn` (the inbox mod), `jq`, `utf8_stdio`, `squad-inbox list --help`, hook scripts under bash, `.gitattributes` (`eol=lf`), `squad-path-guard` case handling.

## Order I would fix in

1. W1 (one line, unblocks everything).
2. W3 (init/upgrade usable without hand-made pins).
3. W2 (a shared Windows launch helper; then the suite tells you what else is broken).
4. W7 (cache size and path length), W4, W5, W6.
