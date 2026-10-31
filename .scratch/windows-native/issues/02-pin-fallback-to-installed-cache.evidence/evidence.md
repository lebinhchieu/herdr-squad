# Evidence: ticket 02 pin fallback

## Behaviour
- `running_pin()` outside a git repo takes the sha from the `squad@*` entry of `installed_plugins.json` whose `installPath` is the running root (compare `normcase(realpath)`); returns `(version, sha, False)`. No match: error text still names `--new-pin`. Git root path unchanged.
- `upgrade`: pinned runtime missing -> installed cache of that pin (version + sha) is the old root; `--old-root` still wins; no cache: old "pinned runtime is missing" error.
- Skills: `--new-pin` / `--old-root` described as manual fallback only.
- One shared parser `_installed_entries()` feeds `_installed_cache` and `running_pin`.
- Extra fix (kept, case b): `_extract` reads the tar stream to its end before closing the pipe. Cause: `git archive` pads the tar with zeros after the end marker; `tarfile` stops at the marker, so closing the pipe with padding unread kills git (SIGPIPE, exit 141) and `_extract` returns False. Whether padding is still unread depends on archive size and consumer speed (not deterministic by size alone; I could not show a size rule). With the line removed on Windows, these fail with `runtime missing ... commit is not in <plugin>`: `MaterialiseTest.test_builds_a_complete_tree_once_and_reuses_it`, `test_a_short_sha_names_the_folder_with_what_it_has`, `test_a_precreated_target_wins_the_rename_and_the_temp_folder_goes` (also seen: `test_concurrent_materialisations...`, `PruneTest.test_cli_needs_home_or_all...`, `RuntimeIsNotAScopeTest.test_scanners_read_fixed_paths_only`). The first two flipped only after my skill-text edit changed the archive; base `caf9f6e` passed them. Linux not run by me (no WSL): Tech Lead's Debian run of the same tests without the line decides. Deterministic test `ExtractDrainTest`: fake git writes a small tar plus 1 MiB padding and exits 141 on a broken pipe; fails without the line, passes with it (no timing).
- `installed_plugins.json` shape = this machine's `~/.claude/plugins/installed_plugins.json` (`scope`, `installPath`, `version`, `gitCommitSha`).

## Tests (Windows, `cd tests && python -m unittest <stem>`)
- `test_squadscaffold` 7 OK (new: non-git root pins from listing; no entry -> `--new-pin` error).
- `test_squadupgrade` 29 OK (new `InstalledCache` x4: no flags check+apply, `--old-root` override, missing cache error, no new-plugin entry names `--new-pin`).
- `test_squadruntime` 69 ran: new `RunningPinCacheTest` x6 and `ExtractDrainTest` x1 pass; failure set (30 errors, 1 skip) identical to base `caf9f6e` (Windows script launch / symlink privilege, ticket 03). Base list vs after diff: empty.
- `test_instructions`, `test_sizes`, `test_team_duties`, `test_promotion_0_6_0` OK. `test_squad_spawn/start`, `test_utf8_helpers`, `test_old_language_inventory`: Windows launch errors (WinError 193 / bytes env / symlink), pre-existing, ticket 03.
- Linux not run here (Tech Lead runs Debian WSL). No test skip added.
