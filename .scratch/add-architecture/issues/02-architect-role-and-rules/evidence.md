# Evidence 02 architect role card, settings and rules

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
