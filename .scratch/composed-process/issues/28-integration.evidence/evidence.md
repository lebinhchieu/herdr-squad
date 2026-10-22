# Evidence: 28 Integration of the sizes-and-models scope

## Developer: integration

### 28 integration (tickets 17,18,19,20,29,30,31)

Base: 20 branch @2267991 (Manager DECISION 28). Branch HEAD before this commit: 8bdad2f.

#### Merges
`git merge-base --is-ancestor <sha> HEAD` → exit 0 for 61d35ac (17/18), fb09501 (19), 2f56772 (30), f0a965a (31, chain 17/29/30/31). Nothing left to merge; no conflicts, none resolved.

#### Committed
Issue files from `.scratch/composed-process/issues/`: modified 17, 20; new 29, 30, 31 (no 28 file exists).

#### Lint
`python3 bin/processlint.py templates/squad/process.md` → exit 0. `squad-process check` → "process.md is current". (`squad-process lint` exists in this worktree's bin; the PATH copy is the main checkout's older one, which lacks it.)

#### Targeted tests (each file alone, `cd tests; python3 -m unittest test_X`, agent env unset), all OK
sizes 35, dev_rules_size 7, advisor_rules 6, qab_optional 13, manager_m_l 9, model_effort_settings 4, processlint 31, squadcompose 47, squad_evidence 48, squad_spawn 65, squad_start 48, team_models 20, suite_rules_process 11, squadsettings 25, process_citations 4, pod_rules_process 10, retro_rules 6, process_writing 7, process_history 6, process_conversion 14, squadprocess 31, squadrules 51, squadruntime 64, templates 10, squad_respawn 16, squad_usage_hook 10, squadupgrade 19. Full suite NOT run (Tech Lead, `--tz`).

#### Live probe (ticket 15 AC4), temp squad /tmp/sq28-probe
```
git init; squad-process scaffold --squad-dir /tmp/sq28-probe/.claude/squads/pr
scopes/s1/scope.md: size: M, design: no
squad-process compose dev        --home scopes/s1 --agent probe-dev        --squad-dir ... --plugin-root <wt> --out roles/probe-dev.rules.md
squad-process compose qa-whitebox --home scopes/s1 --agent probe-qa-whitebox ... --out roles/probe-qa-whitebox.rules.md
```
Headers: `scope: s1 (size M, design no, qa full, goal no)`; dev 733 words, qa-whitebox 1847 words.
Markers: A = `SUITE-2c Suites, Developer, M` (dev only); B = `SIZE-17c Joining after a move up, QA whitebox` (qaw only).
Asked each: `claude -p --model haiku --agent squad:<role> --plugin-dir <wt> --append-system-prompt-file <its rules> "…A? B? YES/NO"`

| session | A (own marker/other's) | B |
|---|---|---|
| dev | YES | NO |
| qa-whitebox | NO | YES |

Limit: composed with the same `squad-process compose` command squad-spawn runs, then `claude -p`; no herdr tab was opened (squad-start/squad-spawn dry paths covered by test_squad_start/test_squad_spawn).

## QA whitebox

### 28 QA whitebox — PASS @6f8ad30

Checked: clean worktree; 6f8ad30 = 20's tree (2267991) + 8bdad2f (20 evidence) + issue files only. `git diff 2267991 HEAD -- bin templates tests skills` empty. Ancestry of 61d35ac, fb09501, 2f56772, f0a965a, 2267991 → all ancestors (verified). Issue-file diffs (17, 20 Touches/Harness lines; 29-31 new) match the re-issue in tech-ac.md.
Ran: `squad-process lint` 0, processlint 0; 18 test files (sizes, qab_optional incl golden, squadcompose, squadrules, squadupgrade, squadinbox, team_models, squad_spawn, squad_start, windows_safe, process_history, squadruntime, dev_rules_size, advisor_rules, instructions, suite_rules_process, pod_rules_process, manager_m_l) → 505 OK. (One test_no_pyc red was my own __pycache__ from running processlint; cleaned, 55 OK.) Full suite not run (Tech Lead, --tz).
Probe: dev/qa-whitebox composed markers per integration.md read; consistent with test_sizes/test_squadcompose composed-text checks.

#### Notes (non-blocking)
- integration.md says "`squad-process lint` does not exist"; it does (`bin/squad-process lint` exits 0).
- Full-suite `--tz` receipt on the integration sha is still the Tech Lead's gate before the PO.

## QA blackbox

### QA blackbox — ticket 28 integration — sha 6f8ad30

Diff 2267991..6f8ad30 = issue files 17,20,29-31 + evidence only (no code change); 17,18,19,20,29,30,31 each passed earlier (evidence/{17,18,19,20,29,30,31}/qa-b.md). Re-checked key behaviour on this sha with scratch squads (/tmp/qab19/r, /tmp/qab28), stub claude/herdr, no code read.

| Check | Saw | Result |
|---|---|---|
| `squad-process lint` | rc 0 | PASS |
| compose per role at S/M/L (manager/dev/qaw/qab/tl/tech/ba) | sizes differ per role (e.g. team-lead 1841 S → 3158 L words); START-3b in Manager at S, M, L | PASS |
| Owners `who SUITE-1b` | M: qa-whitebox acts, manager aware; `who LC-7a/7b/7c`: S manager, M manager, L team-lead (manager aware) | PASS |
| 3-returns notice (squad-log-message, 3 HANDIN+FAIL) | none on fail 1,2. Fail 3: S "record the budget line and consult the advisor [LC-25]"; M "send BLOCKED 7: 3 returns to Manager [LC-7c]; dev consult advisor…[LC-25]"; L same to Team Lead [LC-7b] | PASS |
| `squad-start --resume --dry-run` | default `sonnet/high (from squad settings)`; flags `(from flag)`; scope.md `model manager: haiku low` `(from scope.md)` | PASS |
| squad-spawn scope.md line / malformed | `model dev: haiku low` → `--model haiku --effort low`; malformed/duplicate rc 2 | PASS |
| Targeted tests | test_sizes, team_models, advisor_rules, squad_start, squad_spawn, pod_rules_process all OK | PASS |
| Dev live probe (evidence/28/integration.md) | read: dev YES/NO, qaw NO/YES, matches role-specific rules | accepted |
