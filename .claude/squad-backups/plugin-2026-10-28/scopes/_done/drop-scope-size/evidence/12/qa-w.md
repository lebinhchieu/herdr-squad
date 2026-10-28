# 12 QA whitebox, final 309cc49 (1aebbf8 evidence-only) — PASS
- Diff vs AC 10: scaffold (`legacy_scaffold`, `_size_facts`, `who_lines` size lines) gone, permanent CutoverTest greps for it; WHEN_KEYS drops size/qa-b; `size`/`qa-b`/`qa-whitebox` in a `when:` is lint error naming rule + new key (ran on mutated CLOSE-3a: exit 1); `size:`/`qa-b:` in unpinned scope.md: compose/team exit 2 naming `squad-process adopt`; undecided non-Manager compose raises; hostile `team:` value rejected as unknown token; upgrade --check lists `qa-b = no -> qa-black = no`, `size = L -> ba = yes`, files byte-identical, --apply refuses (exit 3, nothing written).
- Inventory test allow-list matches ticket; AC29 test; no "ticket 11" skip left. Lint 0.
- Tests (git-initialised archive of 1aebbf8): old_language_inventory, squadcompose, squadrules, squadupgrade, team_models, team_cli, team_duties, sizes, dev_rules_size, squadadopt, process_conversion, squad_spawn, squad_respawn: 462 OK, 2 skips.
- Non-blocking: inventory test counts per file, so an unrelated added/removed hit in an allow-listed file needs the count bumped.

## Delta 309cc49..59e2741 (re-HANDIN)
- squadupgrade `_other_l_role` + `alternative: team-lead = yes / tech-lead = yes` lines only when the op's `roles:` names team-lead/tech-lead and the translation is `ba = yes`; check writes nothing, --apply still refuses. test_squadcompose needle now raw `qa-b\b` (old non-raw was a backspace no-op), still passes. 169 tests OK (upgrade, compose, inventory, squadrules), lint 0.
- Verdict: pending Tech's final sha.
