# Evidence: 03 Docs, ADR, version and promotion

## Behaviour
- `CONTEXT.md`: new terms **Architect** and **architecture flag**; Tech Lead's `_Avoid_: architect` removed (`grep -n -i "avoid.*architect" CONTEXT.md` prints nothing).
- `docs/adr/0017-architect-role.md`: role, flag, boundary versus the Tech Lead, PO-decides irreversible choices; says it amends 0016's owner rows and stays consistent with 0010.
- `README.md`: roles list and the Designer paragraph name the Architect and `architecture: yes`.
- Version: `.claude-plugin/plugin.json` 0.5.1 -> 0.6.0; changelog `## v8 — 2026-10-27` (snapshot `history/process-v8/`, a copy of `templates/squad/process/`) holds the Architect rules; the v7 block equals its content at base 69eb078. Pinned scopes run their pinned runtime and are unaffected (ADR 0016).
- `tests/test_sizes.py` `Changelog` test now reads the v7 and v8 blocks together as the entry since base 2e81e5e.
- `promote.md` lives in the scope folder; it lists exactly CONTEXT.md, ADR 0017, README.md.
- Tests run and passing: test_sizes, test_process_history, test_processlint, test_squadprocess, test_squadprocess_apply, test_squadrules, test_squadadopt, test_squad_path_guard, test_designer_handoff, test_architect_handoff, test_squadruntime, test_squadsettings, test_squad_start, test_instructions.
