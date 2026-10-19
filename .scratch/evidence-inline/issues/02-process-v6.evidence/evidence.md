# Evidence: 02 process v6, evidence next to the ticket
sha: 32a970a5258e8c302030bc4db0fa8072e0972e55

## Behaviour

No screenshots: ticket has no UI. Output below is verbatim from the sha above.

### AC1: history guards pass
Ran (from `tests/`): `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_history test_processlint test_process_writing test_process_citations test_templates test_instructions test_squadprocess test_squadprocess_show test_squadprocess_apply` plus `test_pod_rules_process` (hard-coded `process-v5.md`; changed that one line to `process-v6.md`).
Saw (`test_instructions` alone): all pass except one test of it that needs ticket 01's `bin/squad-evidence` (process.md now tells agents to run it, the file lands with ticket 01):
```
FAIL: test_every_command_an_instruction_tells_agents_to_run_exists (test_instructions.InstructionsTest.test_every_command_an_instruction_tells_agents_to_run_exists)
Ran 22 tests in 0.006s
FAILED (failures=1)
```
Same set without `test_instructions`:
```
----------------------------------------------------------------------
Ran 149 tests in 2.135s

OK
```
Snapshot equals template: `cmp templates/squad/process.md skills/squad-process-update/history/process-v6.md` → no output, exit 0.

### AC2: processlint
```
$ python3 bin/processlint.py templates/squad/process.md
exit 0
```

### AC3: evidence sentences in process.md
`grep -n evidence templates/squad/process.md` (line numbers):
```
13 matches in 8F:

[file] 156 (1):
     0: ... Manager proposes it with evidence links, runs the Token Coach if Iterations say...

[file] 160 (1):
     0: ...ad>` archives everything, evidence included, to `.claude/squads/_done/<squad>/`.

[file] 219 (1):
     0: ...icket path with `.md` → `.evidence/` (a project without ticket files: next to `t...

[file] 265 (1):
     0: ...rs passed the sha, or the evidence sha after it (a later sha whose diff to the p...

[file] 272 (1):
     0: first line `sha <git rev-parse HEAD> clean=<yes|no>`, tail the OK line.

[file] 71 (1):
     0: ** the size's Done rule (Sizes), evidence saved, branches ready for PO review.

[file] 9 (1):
     0: also the task's `evidence.md`); the design sections the task cites (grep the hea...

[file] templates/squad/process.md (6):
    36: ...r roster, notes, logs and evidence live there. Touch nothing else unless this fi...
    55: ... `<ticket path minus .md>.evidence/` | Developer | `evidence.md`, the one file t...
    56: | `evidence/<task>/` | QAs, Tech Lead | Reviewers' working files `qa-w.md`, `qa-...
   116: ...oper saves Playwright/API evidence (`dev-evidence.md`); Tech Lead checks it | QA...
   118: ... screen and state in `dev-evidence.md`; Tech Lead checks them | QA blackbox | QA...
   220: ...reviewer file with `squad-evidence add` and commits; the Tech Lead checks that c...

```
Lines 55-56 files table, 219-221 lifecycle rules, 265 merge rule, 272 receipt path, 9 header row; 36/71/156/160 unchanged. Lines 116/118 (Sizes, `dev-evidence.md`) left unchanged per ticket item 4; flagged to the Tech Lead.

### AC4: diff stat vs previous commit
```
skills/squad-init/SKILL.md                        |   2 +-
 skills/squad-process-update/changelog.md          |  24 ++
 skills/squad-process-update/history/process-v6.md | 276 ++++++++++++++++++++++
 templates/squad/process.md                        |  15 +-
 templates/squad/project.md                        |   2 +-
 tests/test_pod_rules_process.py                   |   2 +-
 6 files changed, 312 insertions(+), 9 deletions(-)
```

### AC5: current squad is silent; plan on a v5 copy
```
$ squad-process check --squad-dir <copy of the v6 template>
process.md is current.

$ squad-process plan --squad-dir <throwaway squad with process-v5.md as process.md>
process.md is version 5; the plugin's is 6. Nothing is written until you confirm.

Changelog items:
- v6 Files table: evidence next to the ticket [## Files are the truth, messages are the talk] rule: PO wants evidence next to each ticket with screenshots shown in the markdown
- v6 Evidence rules in the task lifecycle [## Task lifecycle] rule: PO wants evidence next to each ticket with screenshots shown in the markdown
- v6 Merge accepts the evidence sha; receipts stay in the scope folder [## Safety] rule: PO wants evidence next to each ticket with screenshots shown in the markdown

Sections:
  clean         # How this squad works
  already       ## Work is grouped by scope
  clean         ## Files are the truth, messages are the talk
  already       ## Defaults
  already       ## Starting work
  already       ## Lifetimes: every scope starts fresh
  already       ## Sizes: not every scope runs the full pod
  already       ### When a role is left out, its duties move. They are never dropped.
  already       ### Changing size
  already       ## Inside a goal
  already       ## Promotion: knowledge goes up to the project
  already       ## Closing
  already       ## Messages
  already       ## Who decides
  clean         ## Task lifecycle
  already       ## Iterations
  already       ## Cost rules
  already       ## Notes
  clean         ## Safety
```
The three v6 items list sections that are `clean` (preamble, Files table, Task lifecycle, Safety).
