# Evidence: 01 pinned runtime and attached rules spike

## Behaviour

No UI: no screenshots. The deliverable is `.scratch/composed-process/spike-runtime.md`; every command and output is quoted there.

### AC 1: every answer quotes command and output
Q1 (4 probes + `init` plugin list), Q2 (2 probes), Q3 (measured in a clone: worktree 0.036 s / 4.6 MB, archive 0.033 s / 4.6 MB, cache 220 KB stale), Q4 (hook probe, with and without `PATH` prefix). "Not tested" with reason: Windows, marketplace install without a repo, two `--settings` flags, Bash-tool `PATH` (auto-mode classifier denied `bypassPermissions`).

### AC 2: one option and the exact flags
Doc "Recommendation": `git archive` runtime at `$SQUAD_DIR/_runtime/<version>-<sha12>/`; `PATH="<runtime>/bin:$PATH" claude --plugin-dir <runtime> --agent squad:<role> --append-system-prompt-file <home>/roles/<agent>.rules.md --settings <home>/roles/<agent>.settings.json`.

### AC 3: no plugin file, setting or live squad changed
`git diff --stat main..HEAD` lists exactly two files: the doc and this `evidence.md`.

### Probe spend
Haiku (`claude-haiku-5-5`), `--max-budget-usd 0.03` on every run, 18 sessions. 11 have a measured `total_cost_usd`, sum **$0.026** (largest cold run $0.0054, cached runs $0.0003 to $0.0037). 7 `stream-json` runs (two cut by `head -1`, five `init` probes) printed no cost; each is counted at the largest cold run, $0.0054, so at most $0.038 more. **Total at most $0.064 (cap $0.10).**
