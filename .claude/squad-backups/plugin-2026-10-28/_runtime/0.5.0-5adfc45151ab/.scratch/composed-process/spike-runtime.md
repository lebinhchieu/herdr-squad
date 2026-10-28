# Spike 01: pinned runtime and attached rules

**Recommendation (for 05, 08):** materialise a pin with `git archive <sha>` into `$SQUAD_DIR/_runtime/<version>-<sha12>/` (shared per pin). Launch every role with `PATH=<runtime>/bin:$PATH claude --plugin-dir <runtime> --agent squad:<role> --append-system-prompt-file <home>/roles/<agent>.rules.md ...`. No `enabledPlugins` override is needed. Details in "Recommendation" below.

Environment: `claude 2.1.306`, model `haiku` (`claude-haiku-5-5`), Linux/WSL2, repo sha `6050951` (`git rev-parse HEAD` = `60509511f4599df96b477db2704b400e08d6d8c2`). Total probe spend: measured $0.026 plus up to $0.038 unmeasured, at most $0.064 (cap $0.10; see evidence).

## Setup (reproduce first)

```bash
P=/tmp/spike01
rm -rf $P; mkdir -p $P/snap $P/cwd   # fresh dir
git -C /home/chieule/workspace/squad archive 6050951 | tar -x -C $P/snap                  # snapshot = pinned tree
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
| E disable only | init probe below, `--settings '{"enabledPlugins":{"squad@herdr-squad":false}}'` | no `squad` plugin, no `squad:dev` agent (see init below) |

ZEBRA is the Q1 verdict (YES with `--plugin-dir`, NO without); FILE is Q2.

Which wins, from the `system`/`init` event (`init() { ( cd $P/cwd && claude -p --model haiku --max-budget-usd 0.03 --output-format stream-json --verbose "$@" "Reply OK." </dev/null 2>/dev/null | jq -c 'select(.type=="system" and .subtype=="init") | {squad:(.plugins|map(select(.name=="squad"))), squadagents:(.agents|map(select(test("squad:dev"))))}' ); }`; baseline = `init --agent squad:dev`; snapshot = `init --plugin-dir $P/snap --agent squad:dev`; disable only = `init --settings '{"enabledPlugins":{"squad@herdr-squad":false}}'`):

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
- **Where:** `$SQUAD_DIR/_runtime/<version>-<sha12>/`, one `_runtime` per squad, e.g. `/home/chieule/workspace/squad/.claude/squads/plugin/_runtime/0.4.1-60509511f459/`. `<sha12>` = the first 12 hex digits of the pin's `<sha>` (the pin may hold the full 40; 05 derives the folder name from the pin, never parses it back). `.claude/squads` is already ignored (`.gitignore:3`; `git check-ignore -v` confirmed), so no ignore entry is needed. Created in a temp folder next to it (`_runtime/.tmp-<pid>`), then `mv` into place; if the target exists, use it (idempotent).
- **Shared:** one runtime per pin, shared by all scopes with that pin. "Refcount" = no counter file: `squad-close <squad> --scope S` removes a runtime only when no other open `scope.md` or `goal.md` under `$SQUAD_DIR` still carries that `plugin:` pin; `squad-close <squad>` (whole squad) deletes `_runtime/` **before** it archives the folder to `.claude/squads/_done/<squad>/` (`bin/squad-close:14`), else the archive carries 4.6 MB per pin.
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
- **`PATH` needs the snapshot's `bin/` first:** yes, in the hook environment: Claude Code did not add the plugin `bin/` to the hook's `PATH`; here `squad-spawn` resolved to the live repo because the user's own shell had `.../squad/bin` on `PATH`. Hooks inherit the launch environment.
- Not tested: the Bash tool's `PATH` inside the session. A Haiku `Bash` probe needed `--permission-mode bypassPermissions`, which the auto-mode classifier denied. The prefix is required for hooks and harmless if the Bash tool also gets the plugin `bin/`, so this gap does not change the recommendation.

## Recommendation (for tickets 05 and 08)

1. **Option:** `git archive` runtime (Q3 (c)) at `$SQUAD_DIR/_runtime/<version>-<sha12>/` (e.g. `.claude/squads/plugin/_runtime/0.4.1-60509511f459/`); temp folder then `mv`; existing folder reused; no symlinks.
2. **Exact launch** (`squad-spawn`, `squad-respawn`):

   ```bash
   PATH="<runtime>/bin:$PATH" claude --plugin-dir <runtime> \
     --agent squad:<role> \
     --append-system-prompt-file <home>/roles/<agent>.rules.md \
     --settings "$settings" ...
   ```

   `$settings` is what `bin/squad-spawn:125-126,168` already passes today (`$squad_dir/settings/$role.json`, else the plugin template), together with `--agent squad:$role --name --session-id --permission-mode auto`, `--model`, `--effort`; and `bin/squad-spawn:171` already turns `$SQUAD_PLUGIN_DIR` into `--plugin-dir`, so 05 sets that to `<runtime>` rather than adding a flag. Ticket 08 later swaps `"$settings"` for its merged `<home>/roles/<agent>.settings.json`.

   - `PATH` prefixed so `squad-*` tools and hooks run the pinned version (Q4).
   - No `enabledPlugins` override: `--plugin-dir` replaces the installed `squad` (Q1), so no double hooks.
   - **Settings (08):** spawn passes exactly one `--settings` file and no `enabledPlugins`. Keep it one file; 08 replaces its path, 05 and 08 never add a second `--settings` (two flags were not tested).
3. **Runtime source:** the repo's `git archive <sha>`; with no repo, the installed cache path only if its `gitCommitSha` equals the pin; missing: exit 1 with the restore command.
4. **Cleanup at `squad-close`:** later ticket (needs `bin/squad-close` and tests): whole-squad close deletes `_runtime/` before archiving; `--scope` close removes a runtime no other open `scope.md`/`goal.md` pins.
5. **Windows:** `git archive` + `tar` (Git for Windows); fallback `--format=zip` + `zipfile`. Not tested on Windows.
6. **Untested here:** Windows; marketplace install without a repo; two `--settings` flags; Bash-tool `PATH` inside the session.
