# Spike 01: pinned runtime and attached rules

**Recommendation (for 05, 08):** materialise a pin with `git archive <sha>` into `$SQUAD_DIR/_runtime/<version>-<sha12>/` (shared per pin). Launch every role with `PATH=<runtime>/bin:$PATH claude --plugin-dir <runtime> --agent squad:<role> --append-system-prompt-file <home>/roles/<agent>.rules.md ...`. No `enabledPlugins` override is needed. Details in "Recommendation" below.

Environment: `claude 2.1.306`, model `haiku` (`claude-haiku-5-5`), Linux/WSL2, repo sha `6050951` (`git rev-parse HEAD` = `60509511f4599df96b477db2704b400e08d6d8c2`). Total probe spend: about $0.04 (cap $0.10; see evidence).

## Setup (reproduce first)

```bash
P=/tmp/spike01; mkdir -p $P/snap $P/cwd
git -C <repo-worktree> archive HEAD | tar -x -C $P/snap                  # snapshot = pinned tree
echo 'Marker phrase: SNAPSHOT-ZEBRA-41.' >> $P/snap/agents/dev.md        # in the snapshot only
echo 'Marker phrase for file: FILE-OTTER-77.' > $P/f.md
Q="Do your system instructions contain the exact phrase SNAPSHOT-ZEBRA-41? And the exact phrase FILE-OTTER-77? Reply exactly: ZEBRA=YES|NO FILE=YES|NO. No tools."
probe() { ( cd $P/cwd && claude -p --model haiku --max-budget-usd 0.03 --output-format json "$@" "$Q" </dev/null | jq -r '.result, .total_cost_usd' ); }
```

`</dev/null` is required: without it `claude -p` waits 3 s for stdin and prints a warning that corrupts the JSON. `squad@herdr-squad` is installed and `enabledPlugins` true in `~/.claude/settings.json` (it is a directory marketplace, `installLocation /home/chieule/workspace/squad`, the live working tree).

## Q1: does `--plugin-dir <snapshot>` make `--agent squad:<role>` load the snapshot card?

**Yes. The snapshot wins; the installed plugin does not load at all.**

| Probe | Command | Output |
|---|---|---|
| A snapshot (+ file, see Q2) | `probe --plugin-dir $P/snap --agent squad:dev --append-system-prompt-file $P/f.md` | `ZEBRA=YES FILE=YES` |
| B baseline (installed only) | `probe --agent squad:dev` | `ZEBRA=NO FILE=NO` |
| C snapshot + disable installed | `probe --plugin-dir $P/snap --agent squad:dev --settings '{"enabledPlugins":{"squad@herdr-squad":false}}'` | `ZEBRA=YES FILE=NO` |
| E disable only | `claude ... --settings '{"enabledPlugins":{"squad@herdr-squad":false}}'` | no `squad` plugin, no `squad:dev` agent (see init below) |

ZEBRA is the Q1 verdict (YES with `--plugin-dir`, NO without); FILE is Q2.

Which wins, from the `system`/`init` event (`--output-format stream-json --verbose`, filtered with `jq -c 'select(.type=="system" and .subtype=="init") | {squad:(.plugins|map(select(.name=="squad"))), squadagents:(.agents|map(select(test("squad:dev"))))}'`):

```
baseline           {"squad":[{"name":"squad","path":"/home/chieule/workspace/squad","source":"squad@herdr-squad","version":"0.4.1"}],"squadagents":["squad:dev"]}
--plugin-dir snap  {"squad":[{"name":"squad","path":"/tmp/spike01/snap","source":"squad@inline","version":"0.4.1"}],"squadagents":["squad:dev"]}
disable only       {"squad":[],"squadagents":[]}
```

With `--plugin-dir` the plugin list holds one `squad`, source `squad@inline`, path the snapshot, in A and in C. Both installed and inline plugins carry the name `squad`, so the inline one replaces the installed one: no double hooks, no double agents. The `enabledPlugins:false` override works too but is **not needed**, and its key `squad@herdr-squad` is install-specific.

## Q2: do `--append-system-prompt-file` and `--agent squad:<role>` both apply?

**Yes, both apply in one session.**

```
probe --plugin-dir $P/snap --agent squad:dev --append-system-prompt-file $P/f.md   ->  ZEBRA=YES FILE=YES
probe --append-system-prompt-file $P/f.md                                          ->  ZEBRA=NO  FILE=YES   (file alone)
```

ZEBRA lives only in the snapshot's card, FILE only in the file. Both YES in one session.

## Q3: how to materialise a pinned runtime

Measured in a clone (`git clone` of this branch; sha `6050951`):

| Option | Command | Result |
|---|---|---|
| (a) installed cache path | `~/.claude-2/plugins/cache/herdr-squad/squad/0.1.0` | 220 KB, version 0.1.0, gitCommitSha `c327dab`: stale. A directory marketplace does not use it (Q1 baseline path is the live repo). Exists only for marketplace installs, only for the version installed. |
| (b) `git worktree add --detach <dir> <sha>` | 0.036 s, 4.6 MB on disk | `<dir>/.git` is a file `gitdir: <repo>/.git/worktrees/<name>`: registers in the source repo (`.git/worktrees`, 84 KB), needs the source repo, and a temp-then-rename breaks the gitdir link. |
| (c) `git archive <sha> \| tar -x -C <dir>` | 0.033 s, 4.6 MB | plain tree, no `.git`, no link to the source repo, exec bits kept (`test -x bin/squad-spawn` yes), no CRLF (`grep -c $'\r' bin/squad-spawn` = 0; `.gitattributes`: `* text=auto eol=lf`, `bin/* text eol=lf`; no `export-ignore`, so the tree is complete). No symlinks in the tree (`git ls-files -s \| grep -c ^120000` = 0). |

**Choice: (c) `git archive`.**
- **Where:** `$SQUAD_DIR/_runtime/<version>-<sha12>/` (project-local, inside `.claude/squads/`). Created in a temp folder next to it, then `mv` into place; if the target exists, use it (idempotent).
- **Shared:** one runtime per pin, shared by all scopes with that pin. "Refcount" = no counter file: `squad-close` removes a runtime only when no `scope.md` or `goal.md` under `$SQUAD_DIR` (open scopes, not archived) still carries that `plugin:` pin.
- **Disk:** 4.6 MB per pin.
- **Cleanup:** needs `bin/squad-close` and its tests; recommend a **later ticket**, not 05 (05 only creates and uses runtimes; a leftover 4.6 MB folder is harmless).
- **Source is a marketplace install (no git repo):** `git archive` needs the repo. Rule: if the repo is absent, use the installed cache path only when its `gitCommitSha` equals the pin; else exit 1 naming the pin and `git -C <plugin repo> archive <sha> ...` as the restore command. (Not tested: no marketplace install without a repo on this machine.)
- **Windows (ADR 0011):** Git for Windows ships `git` and `tar`, and `.gitattributes` keeps `bin/*` LF. No symlinks, no worktree metadata. Not tested on native Windows: no Windows host here. To avoid depending on `tar`, `git archive --format=zip` plus Python `zipfile` is the fallback (not run).

## Q4: do `${CLAUDE_PLUGIN_ROOT}` hooks resolve to the snapshot? does `PATH` need the snapshot's `bin/`?

Probe: added to the snapshot's `hooks/hooks.json` a `SessionStart` command hook `echo "ROOT=${CLAUDE_PLUGIN_ROOT} PATH=$PATH SPAWN=$(command -v squad-spawn)" >> /tmp/spike01/hook.out`, then ran `probe` with `Reply OK.`:

```
# no PATH change (command: claude -p ... --plugin-dir $P/snap --agent squad:dev "Reply OK.")
ROOT=/tmp/spike01/snap  PATH=...:/home/chieule/workspace/squad/bin  SPAWN=/home/chieule/workspace/squad/bin/squad-spawn

# recommended (command: PATH=$P/snap/bin:$PATH claude -p ... --plugin-dir $P/snap --agent squad:dev "Reply OK.")
ROOT=/tmp/spike01/snap  PATH=/tmp/spike01/snap/bin:/home/chieule/.claude-accounts/bin:...  SPAWN=/tmp/spike01/snap/bin/squad-spawn
```

- **Hooks resolve to the snapshot:** yes, `${CLAUDE_PLUGIN_ROOT}` = the `--plugin-dir` path.
- **`PATH` needs the snapshot's `bin/` first:** yes. Claude Code does not add the plugin `bin/` to `PATH`; here `squad-spawn` resolved to the live repo because the user's own shell had `.../squad/bin` on `PATH`. Hooks inherit the launch environment.
- Not tested: the Bash tool's `PATH` inside the session. A Haiku `Bash` probe needed `--permission-mode bypassPermissions`, which the auto-mode classifier denied. The hook environment is the launch environment, and the Bash tool inherits it as well in normal use (not verified).

## Recommendation (for tickets 05 and 08)

1. **Option:** `git archive` runtime (Q3 (c)) at `$SQUAD_DIR/_runtime/<version>-<sha12>/`; temp folder then `mv`; existing folder reused; no symlinks.
2. **Exact launch** (`squad-spawn`, `squad-respawn`):

   ```bash
   PATH="<runtime>/bin:$PATH" claude --plugin-dir <runtime> \
     --agent squad:<role> \
     --append-system-prompt-file <home>/roles/<agent>.rules.md \
     --settings <home>/roles/<agent>.settings.json ...
   ```

   - `PATH` prefixed so `squad-*` tools and hooks run the pinned version (Q4).
   - No `enabledPlugins` override: `--plugin-dir` replaces the installed `squad` (Q1), so no double hooks.
   - **Settings (08):** today's `squad-spawn` passes one settings file from `$squad_dir/settings/$role.json` or the plugin template (`bin/squad-spawn:125-126`), and passes no `enabledPlugins`. 08's merged `<home>/roles/<agent>.settings.json` stays the single `--settings` file; 05 must not add a second `--settings`. Two `--settings` flags were not tested.
3. **Runtime source:** the repo's `git archive <sha>`; with no repo, the installed cache path only if its `gitCommitSha` equals the pin; missing: exit 1 with the restore command.
4. **Cleanup at `squad-close`:** later ticket: remove a runtime when no open `scope.md`/`goal.md` carries its pin.
5. **Windows:** `git archive` + `tar` (Git for Windows); fallback `--format=zip` + `zipfile`. Not tested on Windows.
6. **Untested here:** Windows; marketplace install without a repo; two `--settings` flags; Bash-tool `PATH` inside the session.
