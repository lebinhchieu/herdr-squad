## Behaviour

Checker entry in CONTEXT.md (line 89) now ends: "With none on the team the HANDIN evidence check (squad-evidence check) decides; no role confirms."

- Diff: 1 line in CONTEXT.md, nothing else.
- Test: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_squadboard_tasks` → 26 tests OK. Full suite not run (see evidence/suite/summary.md, 07c4876).
- No bin/__pycache__ left.
