# Evidence: 03 Docs, ADR, version and promotion
sha: 5189427
## Behaviour
- `CONTEXT.md`: new terms **Architect** and **architecture flag**; Tech Lead's `_Avoid_: architect` removed (`grep -n -i "avoid.*architect" CONTEXT.md` prints nothing).
- `docs/adr/0017-architect-role.md`: role, flag, boundary versus the Tech Lead, PO-decides irreversible choices; says it amends 0016's owner rows and stays consistent with 0010.
- `README.md`: roles list and the Designer paragraph name the Architect and `architecture: yes`.
- Version: `.claude-plugin/plugin.json` 0.5.1 -> 0.6.0; changelog `## v8 — 2026-10-27` (snapshot `history/process-v8/`, a copy of `templates/squad/process/`) holds the Architect rules; the v7 block equals its content at base 69eb078. Pinned scopes run their pinned runtime and are unaffected (ADR 0016).
- `tests/test_sizes.py` `Changelog` test now reads the v7 and v8 blocks together as the entry since base 2e81e5e.
- `promote.md` lives in the scope folder; it lists exactly CONTEXT.md, ADR 0017, README.md.
- Tests run and passing: test_sizes, test_process_history, test_processlint, test_squadprocess, test_squadprocess_apply, test_squadrules, test_squadadopt, test_squad_path_guard, test_designer_handoff, test_architect_handoff, test_squadruntime, test_squadsettings, test_squad_start, test_instructions.

## QA whitebox

### QA whitebox 03 — sha 5189427 — verdict pending full-suite receipt
Checked OK: CONTEXT.md (Architect, architecture flag; Tech Lead `_Avoid_: architect` gone, grep clean; glossary terms used verbatim in ADR 0017). ADR 0017 numbered next after 0016, status/amends 0016 and consistent with 0010, mentions the S dev-size exception. README names Architect + `architecture:` next to Designer/`design:`. changelog v8 holds the Architect rules, v7 block back to base content; history/process-v8 == templates/squad/process (diff -r empty); v7 snapshot untouched. plugin.json 0.5.1->0.6.0; scopes pinned to 0.5.1 run their pinned runtime (ADR 0016), ADR 0005 superseded so no process-version line (accepted). Diff beyond the ticket list: plugin.json (version marker), tests/test_sizes.py Changelog merge of v7+v8 blocks (needed, justified).
Lint 0; tests OK: sizes 36, process_history 6, squadprocess 31, squadprocess_apply 26, squadrules 55, processlint 31, squadruntime 64, squadsettings 25, architect_handoff 15, dev_rules_size 9.
promote.md (PROMO-8): lists exactly CONTEXT.md, ADR 0017, README; matches the committed edits; nothing the scope did not decide.

## QA blackbox

### QA blackbox 03 — commit 5189427 (docs + version; read docs/promote.md, ran CLI tools in scratch squad; no code read)

| AC | Did | Saw | Result |
|---|---|---|---|
| 1 CONTEXT + ADR 0017 consistent with 02 rules | read CONTEXT.md Architect / architecture flag / Tech Lead entries and docs/adr/0017-architect-role.md; compared with composed rules (SIZE-3a, SIZE-9a, WHO-2e, SIZE-22a, SPAWN-4a, MSG-20, SIZE-23c/d, REV-22a) | Terms match the rules verbatim: optional, PO-only flag default `no`, any size, `architecture.md` Status draft\|final before the plan, above Tech Lead (L) and Developer design notes (S, M), Architect proposes / PO decides irreversible choices, conformance in technical AC (S review subagent, M QA whitebox, L Tech Lead + QA whitebox), 2 rounds then Manager, flag-off unchanged. Tech Lead `_Avoid_: architect` line is gone; Tech Lead entry says per-task design stays inside `architecture.md`. ADR 0017 states "Amends 0016" (owner rows → WHO-2e/SIZE-22a) and "Consistent with 0010" | PASS |
| 2 README | grep README.md | Roles list names "an optional Architect (only when the PO sets `architecture: yes`)" next to the Designer / `design: yes`; Designer paragraph followed by the Architect/`architecture:` sentence | PASS |
| 3 version, snapshot, changelog; old pin unaffected | plugin.json; changelog `## v8`; history dir; scratch scopes pinned `0.5.1 69eb078…`; `squad-spawn dev --dry-run` | plugin.json 0.6.0; changelog v8 block with `snapshot: history/process-v8/`, added IDs match the rules I saw in 02 (SIZE-3a…MSG-20b), changed/removed none; `history/process-v8/` has 20 files like `process-v7/`. A scope pinned to 0.5.1 still resolves `_runtime/0.5.1-69eb0789e0e0` with the 0.6.0 tools. 138/138 composed files (108 no/absent vs base 30de602, 30 yes vs 02 output) byte-identical; lint clean | PASS |
| 4 promote.md | read `$SCOPE_DIR/promote.md` | Lists CONTEXT.md, ADR 0017, README only; "Not promoted" names ticket mechanics, tests, evidence, changelog. Those three docs contain the listed changes | PASS |

Verdict: PASS.
