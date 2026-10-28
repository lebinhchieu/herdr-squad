# The plugin drops process-version history and old-layout migration

Status: accepted (cleanup; PO accepted the plan and Q1 = drop `squad-migrate` and `squad-process adopt`, Q2 = prune tracked clutter, on 2026-10-28)

**Overrides:** ADR 0018 (team replaces size): its consequence "every existing unpinned squad migrates with the converter (`squad-process adopt`)" no longer holds; the rest of 0018 stands. ADR 0005 (process versioning): the tooling it left behind (`squad-process version|check|plan|compose --out|apply --legacy`, the v1-v9 snapshots, `templates/squad/process.md`) is retired; ADR 0016 (composed process) already superseded 0005 and is unchanged. ADR 0004 (layout detection) is unchanged.

**Decision:** plugin 0.6.0 has no live caller for the old formats, so the plugin stops shipping them:
- the `process.md` version machinery: `bin/squadprocess.py`, `squad-process version|check|plan|apply --legacy|compose --out`, `skills/squad-process-update/history/`, `templates/squad/process.md`, the `process_update` key of `squad-start` and the process-update sentence of the Manager's first prompt. The changelog stays, because `squad-process upgrade` reads its `- ID: why` lines.
- the converters: `squad-migrate` (flat to per-scope layout, `--scope-to-goal`) and `squad-process adopt`. `squad-process scaffold` moved to `bin/squadscaffold.py` and is unchanged.
- tracked clutter: `.claude/squad-backups/*.md`, `.scratch/_done/`, `handover/`, `SETTINGS-NOTES.md`. Git history keeps all of it (the squad/plugin/cleanup branch). `TODO.md` stays (open item).

**Why:** each was kept only for squads that had not moved to 0.6.0. The version history was 461 KB, the old-layout converters 1,000 lines with their tests; nothing read them but each other.

**Consequences:**
- Removed commands fail as argparse usage errors, exit 2, no stub.
- A squad older than 0.6.0 cannot be converted by the plugin: replace the old `size:`/`design:`/`architecture:`/`qa-b:` lines of `scope.md` by one `team:` line by hand, or start a composed squad with `squad-process scaffold`. An old-format `scope.md` still refuses with exit 2 and says so.
- A legacy squad (a `process.md`, no `process.local.md`) keeps spawning with the plugin's rules; nothing converts it. `squad-process mode` still says `legacy`.
- A flat-layout squad is refused by `squad-start`; nothing converts it. `squad-migrate --scope-to-goal` is gone.
- Dead pointers to `.scratch/squad-plugin-windows/` (ADR 0011) and `.scratch/composed-process/` (comments in `bin/squadupgrade.py`, `bin/squadrules.py`, `bin/squadruntime.py`) are history now (they moved to `.scratch/_done/`, since pruned); the live places are ADR 0011 (native Windows) and ADR 0016 (composed process); read the old files with `git log`.
- Plugin version stays 0.6.0 (no behaviour change for composed squads).

**Alternatives rejected:** keep the converters one more release (no squad needs them and each is code to keep green); keep `history/` as documentation (git history already holds it); stubs that print "removed" (two ways to fail).
