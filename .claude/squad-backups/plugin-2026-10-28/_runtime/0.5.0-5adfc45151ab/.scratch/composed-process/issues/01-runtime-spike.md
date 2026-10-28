Status: ready-for-agent
Type: research
Task ID: 01
Touches: `.scratch/composed-process/spike-runtime.md` (new)
Does not touch: any file under `bin/`, `agents/`, `templates/`, `hooks/`
Harness: `claude -p --model haiku` probes in a temp dir; spend at most $0.10
Blocked by: none

# 01: Spike: pinned runtime and attached rules

**Done when `spike-runtime.md` answers the four questions below, each with the exact command run and its output, plus a recommendation that tickets 05 and 08 can build on.**

## Why
On 2026-10-21, `claude --agent squad:dev` was shown to load role cards live from the repo working tree (the plugin comes from a directory marketplace), while `~/.claude/plugins/cache/herdr-squad/squad/0.1.0` is stale and unused. Ticket 05 must pin a scope to one plugin version, so it needs these facts first.

## Questions
1. With `squad@herdr-squad` installed and enabled, does `claude --plugin-dir <snapshot>` make `--agent squad:<role>` load the snapshot's card? If both load, which wins? If needed, does `--settings` with `enabledPlugins: {"squad@herdr-squad": false}` plus `--plugin-dir` work? Probe as on 2026-10-21: put a marker phrase in the snapshot's `agents/dev.md` only, then ask a Haiku session whether its instructions contain it (YES/NO).
2. Do `--append-system-prompt-file <f>` and `--agent squad:<role>` both apply in one session? Probe with one marker in the card and another in the file.
3. How should a pinned runtime be materialised, given the pin is `scope.md` `plugin: <version> <sha>`? Compare: (a) the installed cache path for marketplace installs; (b) `git worktree add --detach <dir> <sha>` for a directory-marketplace or dev setup; (c) `git archive`. Cover where it lives (e.g. `.claude/squads/_runtime/<version>-<sha>/`), disk size, cleanup at `squad-close`, and native Windows (ADR 0011).
4. Inside a pinned session, do `${CLAUDE_PLUGIN_ROOT}` hooks resolve to the snapshot? Does `PATH` need the snapshot's `bin/` first so that `squad-*` tools also run the pinned version? Probe with a hook that echoes its path.

## Technical AC
1. Every answer quotes the command and its output. "Not tested" is written where a probe could not run, with the reason.
2. The recommendation names one materialisation option and the exact `claude` flags `squad-spawn` must pass.
3. No change to any plugin file, settings or the live squad.
