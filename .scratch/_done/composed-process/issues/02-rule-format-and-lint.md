Status: ready-for-agent
Type: task
Task ID: 02
Touches: `bin/squadrules.py` (new), `bin/squadrules_cli.py` (new), `bin/squad-process` (thin delegation, `lint`), `tests/test_squadrules.py` (new), `tests/fixtures/rules/` (new)
Does not touch: `templates/squad/process.md`, `templates/squad/process/` (ticket 03), `agents/*`, `bin/squad-spawn`
Harness: `cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_squadrules test_processlint test_windows_safe`
Blocked by: none

# 02: Rule file parser and `squad-process lint`

**Done when `bin/squadrules.py` parses rule files and overlays exactly as the `spec.md` contracts say, and `squad-process lint` reports every listed problem as `file:line: problem` with exit 1.**

## What
- Parse `process/*.md` rule blocks (ID, title, attributes, body, file and line), `_removed.md` tombstones, and `process.local.md` operations.
- Evaluate `when:` with `matches(when, facts) -> bool`, where a missing fact counts as true.
- Compute the rule hash as defined in the contract.
- `lint` covers every check listed in spec → CLI → `lint`. Reuse the Writing-rule checks of `bin/processlint.py` per rule body, imported, not copied.
- Stdlib only; follow the `bin/squad-report` wrapper pattern.

## Technical AC
1. A fixture rule set with core, two topic files, `_removed.md` and an overlay parses to the expected objects (IDs, attributes, bodies, line numbers).
2. Each lint error class has a fixture that triggers it and only it: duplicate ID; missing `roles:`; missing `topic:`; unknown role; unknown `when` key or value; ID prefix not matching its file; body over 60 words per bullet; an overlay operation on a missing ID; two operations on one ID; operation without `why:` or `upstream:`; a 12-word sentence in two rules; a 12-word sentence in a rule and a fixture `agents/x.md`; `[ID]` cited in a fixture agents/skills/bin file that does not exist; tombstone ID still present as a rule.
3. Bare ids such as `SEC-04` and `UTF-8` in a cited file are not reported; only the `[ID]` form is checked.
4. `matches` truth table: `size in M, L` with facts {size: S} false, {size: M} true, {} true; `size = S and design = yes`; an unknown key raises.
5. The hash is stable across CRLF and LF input and across trailing spaces, and changes when one word of the body or one attribute changes.
6. `squad-process lint` with no rule folder present exits 0 and prints "no rule files". The template has none until 03.
