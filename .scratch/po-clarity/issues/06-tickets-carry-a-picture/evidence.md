# Evidence 06

## Behaviour

Rule `LC-9c` (manager, tech-lead, ba, architect; no `when:`, so `squad-process who LC-9c` prints no lines, it is unconditional). New `templates/squad/ticket.md`, changelog v29 entry, no version bump (rides 05).

- `python3 bin/squad-process lint` → exit 0 (first draft failed the 60-word limit; shortened).
- `sc.find_rule(..., 'LC-9c').roles` → `['manager', 'tech-lead', 'ba', 'architect']`.
- `cd tests && python3 -m unittest test_processlint test_instructions test_rules_wording test_windows_safe test_utf8_helpers` → Ran 105 tests, OK (SQ-10 trio included).
- Template has Problem / Change / AC / Comments, plus `Aim:`, `Estimate:`, `Depends on:`; the rule names it.
