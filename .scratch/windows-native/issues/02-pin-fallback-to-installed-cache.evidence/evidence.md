# Evidence: ticket 02 pin fallback

## Behaviour
- `running_pin()` outside a git repo takes the sha from the `squad@*` entry of `installed_plugins.json` whose `installPath` is the running root (compare `normcase(realpath)`); returns `(version, sha, False)`. No match: error text still names `--new-pin`. Git root path unchanged.
- `upgrade`: pinned runtime missing -> installed cache of that pin (version + sha) is the old root; `--old-root` still wins; no cache: old "pinned runtime is missing" error.
- Skills: `--new-pin` / `--old-root` described as manual fallback only.
- One shared parser `_installed_entries()` feeds `_installed_cache` and `running_pin`.
- Extra fix: `_extract` drains the tar pipe before closing it (git died of SIGPIPE, exit 141, when the archive tail was left unread; size-dependent, hit by the longer skill text).
- `installed_plugins.json` shape = this machine's `~/.claude/plugins/installed_plugins.json` (`scope`, `installPath`, `version`, `gitCommitSha`).

## Tests (Windows, `cd tests && python -m unittest <stem>`)
- `test_squadscaffold` 7 OK (new: non-git root pins from listing; no entry -> `--new-pin` error).
- `test_squadupgrade` 29 OK (new `InstalledCache` x4: no flags check+apply, `--old-root` override, missing cache error, no new-plugin entry names `--new-pin`).
- `test_squadruntime` 68 ran: new `RunningPinCacheTest` x6 pass; failure set (30 errors, 1 skip) identical to base `caf9f6e` (Windows script launch / symlink privilege, ticket 03). Base list vs after diff: empty.
- `test_instructions`, `test_sizes`, `test_team_duties`, `test_promotion_0_6_0` OK. `test_squad_spawn/start`, `test_utf8_helpers`, `test_old_language_inventory`: Windows launch errors (WinError 193 / bytes env / symlink), pre-existing, ticket 03.
- Linux not run here (Tech Lead runs Debian WSL). No test skip added.
