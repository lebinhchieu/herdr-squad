# Evidence 02: docs and promotion for the new rule

## Behaviour
Docs only. `HANDOFF.md`: new section "Autoswitch: which account is next" (3 steps, example, guard, ties, log reason, data, Windows note, restart note). `skill/SKILL.md`: the `cautoswitch` row no longer says "lower on both 5h and 7d"; it carries the same rule. The module docstring was already updated in 01. Installed copy not edited. `CONTEXT.md` unchanged (no new term). Promoted items match `tasks/promote.md`.

## Review
`grep -rl 'lower on both' tests/ tools/` has no hit left. Golden hit `tests/test_ca_install.py` (it copies SKILL.md and HANDOFF.md) passes with `PYTHONPATH=tests`: 22 tests OK. No code changed.
