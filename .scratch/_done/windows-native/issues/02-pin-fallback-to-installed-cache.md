# 02: `scaffold` and `upgrade` need the installed-cache fallback

Status: ready-for-agent
Type: task
Blocked by: none
Source: findings.md W3 (not Windows-only)

**What:** on any marketplace install `squad-process scaffold` and `upgrade` stop with `cannot pin the running plugin (… is not a git checkout); write {squad dir}/plugin.pin as <version> <sha>`. `upgrade --check` then also stops with `the pinned runtime is missing` when the old pinned runtime was never built. The PO had to pass `--new-pin "<ver> <sha from installed_plugins.json>"` and `--old-root <cache>/<old version>` by hand.

**Cause:** `bin/squadruntime.py:104` `running_pin()` needs `git rev-parse HEAD` in the plugin root; the installed cache has no `.git`. `materialise()` already falls back to `_installed_cache(version, sha)` (reads `installed_plugins.json` `gitCommitSha`); `running_pin()` does not.

## Do
- `running_pin()`: when the plugin root is not a git repo, take version and sha from the matching `squad@*` entry in `installed_plugins.json` (same lookup `_installed_cache` uses, by `installPath` equal to the running root). Keep the current error when nothing matches.
- `upgrade`: when the old pinned runtime folder is missing, use the old installed cache (match by version + sha) as the old root instead of stopping; keep `--old-root` as an override.
- `skills/squad-init/SKILL.md` and `skills/squad-process-update/SKILL.md`: mention `--new-pin` / `--old-root` only as the manual fallback.

## AC
- [ ] `scaffold` and `upgrade --check/--apply` succeed from a non-git plugin root with an `installed_plugins.json` fixture (`SQUAD_INSTALLED_PLUGINS`), no flags.
- [ ] The error text still names `--new-pin` when no installed entry matches.
- [ ] Tests for both, Linux and Windows.

## Comments
