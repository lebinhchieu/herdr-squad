# Evidence: 01 pinned runtime and attached rules spike

## Behaviour

No UI: no screenshots. The deliverable is `.scratch/composed-process/spike-runtime.md`; every command and output is quoted there.

### AC 1: every answer quotes command and output
Q1 (4 probes + `init` plugin list), Q2 (2 probes), Q3 (measured in a clone: worktree 0.036 s / 4.6 MB, archive 0.033 s / 4.6 MB, cache 220 KB stale), Q4 (hook probe, with and without `PATH` prefix). "Not tested" with reason: Windows, marketplace install without a repo, two `--settings` flags, Bash-tool `PATH` (auto-mode classifier denied `bypassPermissions`).

### AC 2: one option and the exact flags
Doc "Recommendation": `git archive` runtime at `$SQUAD_DIR/_runtime/<version>-<sha12>/`; `PATH="<runtime>/bin:$PATH" claude --plugin-dir <runtime> --agent squad:<role> --append-system-prompt-file <home>/roles/<agent>.rules.md --settings "$settings"` (08 later swaps in its merged file).

### AC 3: no plugin file, setting or live squad changed
`git diff --stat main..HEAD` lists exactly two files: the doc and this `evidence.md`.

### Probe spend
Haiku (`claude-haiku-5-5`), `--max-budget-usd 0.03` on every run, 18 sessions. 11 have a measured `total_cost_usd`, sum **$0.026** (largest cold run $0.0054, cached runs $0.0003 to $0.0037). 7 `stream-json` runs (two cut by `head -1`, five `init` probes) printed no cost; each is counted at the largest cold run, $0.0054, so at most $0.038 more. **Total at most $0.064 (cap $0.10).**

## QA whitebox

### QA whitebox: ticket 01, sha 7d5681e

**PASS. I reran Q1, Q2 and Q4 myself and got the same answers; the diff is the two allowed files; spend is stated and under the cap.**

#### Checked
- Diff `6050951..7d5681e` (`git diff-tree`): only `.scratch/composed-process/spike-runtime.md` and `…/01-runtime-spike.evidence/evidence.md`. No plugin file, settings or live-squad change (AC3).
- Q1/Q2 rerun (Haiku, temp snapshot of 6050951 with a marker in `agents/dev.md`, file marker): A snapshot + file `ZEBRA=YES FILE=YES`; B baseline `ZEBRA=NO FILE=NO`; C snapshot + `enabledPlugins:false` `ZEBRA=YES FILE=NO`. Matches the doc. Cost per probe about $0.003.
- Q4 rerun: hook output `ROOT=<snapshot>`, `SPAWN=<snapshot>/bin/squad-spawn` with `PATH=<snap>/bin:$PATH`; without the prefix `SPAWN` resolves to the live repo. Matches the doc.
- Every answer quotes command and output; untested items are named with reasons (Windows, marketplace install without a repo, two `--settings`, Bash-tool PATH) (AC1).
- One option and exact flags named (AC2); design.md §01 additions: spend (at most $0.064, cap $0.10) and shared-per-pin runtime with cleanup rule are answered.
- Temp dirs of my probes removed.

#### Nits (non-blocking)
1. `evidence.md` AC 2 shows `--settings <home>/roles/<agent>.settings.json`; the doc's recommendation passes `$settings` (today's file) and leaves the merged file to 08. Align at the next edit; 05 follows the doc.
2. Spend is an upper bound ($0.026 measured plus $0.038 estimated), disclosed.
3. Environment quirk, not a defect: `git diff <a> <b>` printed nothing in this session; `git diff-tree` and `git show --stat` were correct. Use `diff-tree` for diff checks.

## QA blackbox

### QA blackbox 01: runtime spike (doc review + probe re-run)

**PASS** on 7d5681e (branch squad/plugin/runtime-compose/plugin-dev-runtime-compose-1; `git rev-parse HEAD` matched).

| AC | What I did | What I saw | Result |
|---|---|---|---|
| 01-1 | Read `spike-runtime.md` for Q1-Q4 | Each has a verdict (Q1 snapshot wins, installed does not load; Q2 both apply; Q3 option (c); Q4 hooks resolve to snapshot, PATH prefix needed), the exact command and its output. Untested items say "Not tested" + reason (Windows host, marketplace install w/o repo, Bash-tool PATH, two `--settings`) | pass |
| 01-2 | Read the Recommendation only | One option (`git archive` to `$SQUAD_DIR/_runtime/<version>-<sha12>/`), location, 4.6 MB, cleanup at `squad-close` (whole-squad before archive; `--scope` unpinned only; later ticket), Windows answer (git+tar, zip fallback, untested), exact launch line with `--plugin-dir`, `--agent`, `--append-system-prompt-file`, `--settings`, `PATH=<runtime>/bin:$PATH`. No TBD | pass |
| 01-3 | Re-ran the doc's Setup block (own dir /tmp/qab01, same commands, snapshot of 6050951 + markers) and probes, Haiku | A (snap+agent+file) `ZEBRA=YES FILE=YES`; B (installed only) `ZEBRA=NO FILE=NO`; C (snap + disable installed) `ZEBRA=YES FILE=NO`; file alone `ZEBRA=NO FILE=YES`. All match the doc. Spend $0.0030+0.0027+0.0030+0.0037 = **$0.012** (cap 0.10) | pass |
| 01-4 | `git diff --stat main..HEAD` | only `.scratch/composed-process/spike-runtime.md` and `issues/01-runtime-spike.evidence/evidence.md`; no plugin, settings or live-squad file | pass |

Not re-run: Q4 hook probe and `init` events (doc output taken as written; Q1/Q2 and recommendation do not depend on them beyond the PATH rule, which the doc itself marks hooks-only).
