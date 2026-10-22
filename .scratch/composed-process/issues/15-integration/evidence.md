# Evidence 15: integration (final check of the stacked chain)

## Behaviour

### AC 1: chain proof
`git merge-base --is-ancestor <sha> HEAD` exit codes: A `b66036b` 0, B `4901cab` 0, C1 `2e81e5e` 0, C2 `853b0a4` 0, 32 `3dcc7b2` 0.
`git log --oneline 853b0a4..HEAD` (taken after the ticket-file commit): `15: ticket file`, then 32's four commits `3dcc7b2 32: evidence with TL review`, `0e58ca5 32: evidence path`, `cfcd99c 32: S review subagent runs on Sonnet at high effort; …`, `17e525b 32: ticket file`. Only 32's commits plus this ticket's.

### AC 2: mop-up
Commit `7bd2b09` (pure `git mv`, nothing else): `20-manager-confirms-team-models.evidence` → `20-manager-confirms-team-models`, `28-integration.evidence` → `28-integration` (orphan, stays without a `28-*.md`), `32-s-review-subagent-sonnet-high.evidence` → `32-s-review-subagent-sonnet-high`. `git show --stat -M`: three renames, `evidence.md | 0` each (100% similarity).
`find .scratch -name '*.evidence'`: empty. `git ls-files | grep '\.evidence/'`: empty.
`squad-evidence check` on each moved `evidence.md`: 20 exit 0, 28 exit 0 (check only), 32 exit 0.
Link grep (`grep -rnE '(20-manager-confirms-team-models|28-integration|32-s-review-subagent-sonnet-high)\.evidence'` over the repo minus `.git` and `skills/**/history`): no match, so no link needed a fix. The other `.evidence` mentions are historical prose in closed tickets (13, 25, 26 notes, 01, 02, 21, 27, `evidence-inline` scope), left as they are.

### AC 3: lint and tests
`bin/squad-process lint`: exit 0.
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squad_evidence test_process_conversion test_sizes test_dev_rules_size test_squadcompose test_templates`: 162 tests OK.
Composed Developer rules, largest over size x design x goal (the `test_dev_rules_size` fixture, live-length names): **5119 B** (S, design yes, goal yes), limit 5120. Unchanged.

### AC 4: diff scope
`git diff --stat 3dcc7b2..HEAD` before this evidence: `issues/15-integration.md` (new ticket text, replaces the old one) and the three renamed `evidence.md` files. No link fixes were needed. With this commit: plus `issues/15-integration/evidence.md`.

### AC 5: live probe (two roles read only their own composed rules)
Temp dir `/tmp/p15` (nothing in the repo or the real squad folders). Followed ticket 05's probe: scratch plugin repo (`git archive HEAD` of this branch, committed; pin `0.4.1 e4fc1508be80c99a1ec7ec8207a9a87e7b05c517`), scratch project and squad `t` with `process.local.md`, scope `sc1` size M with the pin, stub `herdr` that logs argv, real `squad-spawn`.
`process.local.md`:
```
## add PROBE-DEV Probe marker for dev
roles: dev … The marker phrase for the developer is DEVMARKER-MANGO-41.
## add PROBE-QAW Probe marker for qa whitebox
roles: qa-whitebox … The marker phrase for the whitebox reviewer is QAWMARKER-PEAR-77.
```
Commands: `squad-spawn dev t-dev-sc1 --scope sc1 --model haiku` and `squad-spawn qa-whitebox t-qaw-sc1 --scope sc1 --model haiku`. Argv the stub logged (each its own file):
```
agent start t-dev-sc1 … --agent squad:dev … --settings …/_runtime/0.4.1-e4fc1508be80/templates/squad/settings/dev.json --model haiku --effort medium --plugin-dir …/_runtime/0.4.1-e4fc1508be80 --append-system-prompt-file …/scopes/sc1/roles/t-dev-sc1.rules.md
agent start t-qaw-sc1 … --agent squad:qa-whitebox … --settings …/qa-whitebox.json --model haiku --effort high --plugin-dir …/_runtime/0.4.1-e4fc1508be80 --append-system-prompt-file …/scopes/sc1/roles/t-qaw-sc1.rules.md
```
Files: `grep -c DEVMARKER` dev file 1, qaw file 0; `grep -c QAWMARKER` dev file 0, qaw file 1. The dev file's `rules:` line ends `… SUITE-2c PROBE-DEV`.
Replay of each argv with `claude -p --model haiku` (same flags, `PATH=<runtime>/bin:$PATH`, `</dev/null`, stream-json, no tools). Question: "Do your system instructions contain the exact phrase DEVMARKER-MANGO-41? And the exact phrase QAWMARKER-PEAR-77? Reply exactly: DEV=YES|NO QAW=YES|NO. No tools."

| Role | DEVMARKER | QAWMARKER | cost |
|---|---|---|---|
| dev | YES | NO | $0.0041 |
| qa-whitebox | NO | YES | $0.0046 |

Init event of both: `squad` plugin from `source: squad@inline`, `path` = the runtime. Total spend $0.0087.
Cleanup: the replays exited on their own; no `p15` or stub process was left (`ps` grep empty; the stub herdr is a one-shot script, nothing started by PID). **`/tmp/p15` was not deleted**: the environment's safety check refused `rm -rf /tmp/p15`, so a person must remove it (`rm -rf /tmp/p15`, ~5 MB, scratch only).

### AC 6
No full suite run.
