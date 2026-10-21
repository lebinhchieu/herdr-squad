# Evidence: 01 pinned runtime and attached rules spike

## Behaviour

No UI: no screenshots. The deliverable is `.scratch/composed-process/spike-runtime.md`; every command and output is quoted there.

### AC 1: every answer quotes command and output
Q1 (4 probes + `init` plugin list), Q2 (2 probes), Q3 (measured in a clone: worktree 0.036 s / 4.6 MB, archive 0.033 s / 4.6 MB, cache 220 KB stale), Q4 (hook probe, with and without `PATH` prefix). "Not tested" with reason: Windows, marketplace install without a repo, two `--settings` flags, Bash-tool `PATH` (auto-mode classifier denied `bypassPermissions`).

### AC 2: one option and the exact flags
Doc "Recommendation": `git archive` runtime at `$SQUAD_DIR/_runtime/<version>-<sha12>/`; `PATH="<runtime>/bin:$PATH" claude --plugin-dir <runtime> --agent squad:<role> --append-system-prompt-file <home>/roles/<agent>.rules.md --settings <home>/roles/<agent>.settings.json`.

### AC 3: no plugin file, setting or live squad changed
`git diff --stat main..HEAD` lists only the doc, this folder, and the already-committed ticket/spec files of earlier commits (see below).

### Probe spend
Haiku (`claude-haiku-5-5`), `--max-budget-usd 0.03` on each run, 15 runs. Cost per run `total_cost_usd` from the JSON: first run $0.0054, later cached runs $0.0003 to $0.0054; the five `stream-json` init probes were not summed individually and are counted at $0.0035 each. **Total about $0.042 (cap $0.10).** Log: `/tmp/spike01/cost.log` (not committed).
