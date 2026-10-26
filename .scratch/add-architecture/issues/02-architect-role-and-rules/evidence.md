# Evidence 02 architect role card, settings and rules
sha: a4a70ab
## Behaviour
- `agents/architect.md`: identity, stance (writes `architecture.md` and ADR drafts only, never code, edits no project file, checks no built code), tools `squad-respawn`. `templates/squad/settings/architect.json`: sonnet high, advisor opus; writes only `scopes/*/architecture.md` and `scopes/*/tasks/**`; denies `scope.md`, `roster.md`, `escalations.md` (not `scopes/*/*.md`, which would shadow `architecture.md`).
- Rules, all `when: architecture = yes`, existing blocks untouched: SIZE-3a flag (PO only, Manager never proposes, logged in iteration file), SIZE-9a deliverable (`Status: draft|final`, listed contents, ADR drafts in `tasks/`, advisor before an irreversible recommendation), SPAWN-4a (after goal check, before plan; retire when final; respawn for a question; also adds `architect` to SPAWN-2a/b/c), LC-11c (S, M) / LC-11d (L) plan gate, LC-19c Developer, MSG-20 feedback (`ASK` the Architect, 2 rounds then Manager), MSG-20a/b doubts and final, START-4a `arch`, START-5a lifetime, START-20 start.
- Above the Tech Lead: WHO-2e (Architect owns the architecture; "Irreversible" rows: Architect lists and recommends, PO decides, Manager escalates) and SIZE-22a (rows replace SIZE-22's); the Developer's design notes (S, M) and each task's design (L) stay inside it.
- Conformance joins the technical AC, checked by the existing checker: SIZE-23c (M, QA whitebox), SIZE-23d (L, Tech Lead + QA whitebox), REV-22a (S, review subagent). The Architect checks no code.
- `architect` added to the unconditional rules that list `designer` (cost, messages, files, notes, safety, start, LC-25), so it carries the common rules.

### No leakage (AC5), byte-for-byte
Snapshot at base 30de602, then at this branch: 9 roles x S/M/L x design x goal x qa-b, for scopes with no `architecture:` line and with `architecture: no` = 324 composed files (timestamp line stripped). `diff -r base new` : identical, 0 differences. Needed one `bin/squadcompose.py` expression: the Manager/Tech Lead "Index of other rules" skips architecture-gated rules and the `architect` role name unless the scope has `architecture: yes`.
Dev rules size with the flag: M/L +186 B (under 5 KiB); S +340 B (S + `design: yes` + flag = 5.4 KiB, over the 5120 B limit that `test_dev_rules_size` holds for flag-off scopes; flag-off unchanged).

## Red run (new tests on base 30de602)
`git archive 30de602` + `tests/test_architect_handoff.py` + `tests/rulesview.py`: 15 tests, 8 failures + 3 errors (no card, no settings, no rules).

## Green run (unittest, one file at a time, at the handed-in sha)
Touched: test_architect_handoff 15, test_templates 10, test_model_effort_settings 4 (1 skipped: base not in clone), test_instructions 29, test_sizes 36, test_squad_spawn 72, test_squadadopt 29, test_task_id_rule 2 — OK. `squad-process lint` before and after: OK. `bash -n bin/squad-spawn` clean.
Every grep hit (process/rule text, `architect`, `settings`, `agents/`, `rules:`) run, all OK: process_conversion, manager_m_l, dev_rules_size 7, squadlabel, suite_rules_process, qab_optional 13, process_history, process_writing, squadsettings, squad_respawn, squadprocess, process_citations, squadcompose 51, squadrules 55, squadruntime 64, team_lead_role, designer_handoff, advisor_rules, retro_rules, pod_rules_process, processlint.
Tests edited only for legitimate count changes: settings files 9 to 10 (test_instructions, test_squad_spawn TABLE, test_squadadopt), `all` roles 8 to 9 (test_task_id_rule), ROLES lists, `ANY_SIZE` += architect. No golden edited.

## Files outside the ticket's list (T4 counters)
`bin/squadcompose.py` (index no-leak), `tests/rulesview.py` (`architecture` kwarg), `tests/test_squadadopt.py`, `tests/test_task_id_rule.py` (counts), `skills/squad-process-update/changelog.md` (v7 entry lists each changed rule ID; `test_sizes.Changelog` requires it; precedent e44b6f4). Version bump and history snapshot stay in 03.

## QA whitebox

### QA whitebox 02 — sha 2de2487 — FAIL (1 finding)

Checked and OK: lint exit 0; own byte-identity run vs base 30de602: 9 roles x S/M/L x design x goal x qa-b x (absent|no) = 324 composed files, 0 diffs. Tests re-run OK: architect_handoff 15, templates 10, model_effort_settings 4, instructions 29, squad_spawn 72, squadadopt 29, task_id_rule 2, squadcompose 51, squadrules 55, processlint 31, dev_rules_size 7, process_history 6, process_writing 7, process_citations 4. Card/settings match designer's shape; deny set does not shadow architecture.md. All new rules are yes-gated blocks, one statement each. Override-row design (SIZE-22a, WHO-2e) accepted.

#### F1 — flag-on Developer size is unguarded (Manager ruling FINAL 02, option a)
tests/test_dev_rules_size.py:15 LIMIT=5120 covers flag-off only. Flag-on: S+design yes = ~5.36 KiB+ (over), M/L flag-on 4.98 KiB (under); nothing stops later growth.
Pass: (1) add a test in tests/test_dev_rules_size.py (or test_architect_handoff.py) that composes the Developer file with `architecture: yes`, using the same fixture as `compose()` there (pin, live-length names), for every size x design x goal: M and L each <= 5120; S+design yes pinned at its current byte value (equality or <= that number, number written in the test); S+design no <= 5120. (2) Note the exception in the ticket's Design notes (last bullet) citing the ruling. Show red-then-green not needed; show the test run in evidence.

#### Re-check a4a70ab — PASS
F1 fixed: flag-on M/L <=5120 test, all four flag-on S combos pinned exactly (5151/5152/5442/5443), exception noted in design notes citing the ruling. test_dev_rules_size 9 OK, test_sizes 36 OK. Diff 2de2487..a4a70ab = test + ticket note only.

## QA blackbox

### QA blackbox 02 — final sha a4a70ab (checked 2de2487 in full; re-checked a4a70ab per LC-3b)
CLI only; scratch squad: 18 scopes = size S/M/L × architecture yes/no/absent × design yes/no. Method: `squad-process compose <role> --home <scope> --now <fixed>` with the plugin under test and with a `git archive` of base 30de602; `squad-process lint`; `squad-spawn architect --dry-run`; read card + settings. No code read.

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 card + settings | read `agents/architect.md`, `settings/architect.json`; dry-run spawn S/M/L yes | Card: identity, stance (writes `architecture.md` + ADR drafts only, never code, never edits scope.md/rules/tickets/others' files, checks no built code), tools, rules pointer. Settings: sonnet / high / advisor opus; allow Write/Edit only `scopes/*/architecture.md` and `scopes/*/tasks/**`; denies scope.md, roster.md, escalations.md, goal files, settings. Dry-run `--agent squad:architect --model sonnet --effort high`, no warning; `model architect: opus max` honoured; no/absent refused exit 1 | PASS |
| 2 rules | compose manager/architect/dev/tech-lead/qa-whitebox/team-lead at S/M/L, diff vs no-scope | New blocks, `architecture yes` only: SIZE-3a flag (PO only, any size, Manager never proposes, logged in iteration file), SIZE-9a role (architecture.md, Status draft\|final, the 5 contents, ADR drafts in tasks/), SPAWN-4a (after goal check, before plan/split, retire when final, respawn for a question; names SPAWN-2a/b/c), LC-11c (S, M) / LC-11d (L) plan gate on Status final, START-4a `arch`, START-5a lifetime row, START-20, MSG-20 (ASK the Architect, 2 rounds → Manager), MSG-20a/b, LC-19c | PASS |
| 3 above Tech Lead / irreversible | read WHO-2e, SIZE-22a, WHO-2d, SIZE-22 in composed Manager | WHO-2e: Architect owns architecture; irreversible = "Architect lists and recommends; Manager escalates; PO decides"; replaces the Irreversible rows of WHO-2/WHO-2d. SIZE-22a rows: Architecture = Architect (all sizes), design notes inside it, irreversible = Architect proposes, PO decides. CORE-3 text itself not edited (byte-identity; carried by WHO-2e/SIZE-3a): intent met, literal "update CORE-3" not | PASS with note |
| 4 conformance | read SIZE-23c/23d/REV-22a | M: QA whitebox SIZE-23c; L: Tech Lead + QA whitebox SIZE-23d; S: Developer REV-22a (review subagent). Architect checks no code | PASS |
| 5 no leakage | 9 roles × 12 no/absent scopes vs base 30de602 | 108/108 byte-identical. With yes: Manager, Architect, Dev, Tech Lead, Team Lead, QA whitebox carry new rules; BA, QA blackbox, Designer, Token Coach unchanged. Header `architecture yes` only on yes. Lint clean; 10 roles compose at L yes + design yes | PASS |

Re-check a4a70ab: all 138 composed files (108 no/absent vs base, 30 yes vs 2de2487 output) byte-identical, 0 diffs, so no behaviour change. `python3 tests/test_dev_rules_size.py`: 9 tests OK.
Notes (not findings): old WHO-2d/SIZE-22 "Irreversible" rows still print in yes scopes, overridden by "replaces" in WHO-2e/SIZE-22a.
Verdict: PASS.
