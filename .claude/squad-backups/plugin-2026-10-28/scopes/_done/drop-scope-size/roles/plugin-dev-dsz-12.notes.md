# plugin-dev-dsz-12 notes (ticket 12), branch squad/plugin/drop-scope-size/plugin-dev-dsz-12

Done (committed, WIP commits on branch):
- bin/squadcompose.py: scaffold + size path + qa-b fact removed; read_home raises old_format_error for unpinned old home (source "old" if pinned); compose raises for "old", and for non-manager on undecided; who_lines no size lines.
- bin/squadrules.py: WHEN_KEYS drops size/qa-b; OLD_WHEN_KEYS + OldKeyError (lint msg "<RID>: when key 'x' is gone ... use <new>"); check_when_combination no longer skips old-key whens.
- bin/squadrules_cli.py (team "old" source, who/lint help), squadteam.py ("old"), squadupgrade.py (old_when_conditions, plan.old_when, printed in --check, exit 3, --apply refuses, writes nothing).
- fixtures rules/{clean,errors,compose}: when keys converted, hashes remapped (/tmp/hmap approach: recompute via sr.load_rules), goldens fixed.
- tests: rulesview (size shorthand = sr.legacy_team; who() adds S/M/L shapes via _size_shapes), test_squadcompose (CutoverTest permanent scaffold tests), test_squadrules (old-key lint cases), test_dev_rules_size, test_sizes (SIZE-17 orphans dropped), test_squad_spawn/respawn setUp `team: none`.
- Green: squadrules, squadcompose, and ~25 grep-hit files (run from tests/ dir: `cd tests && python3 -m unittest test_x`).

UPDATE (later): test_team_cli, test_squadadopt, test_team_duties, test_squad_spawn/respawn, test_squadupgrade (new class OldWhenLanguage = AC21) all green and committed.

TODO (remaining, in order):
1. S4 reader inventory: run `git grep -nE "size:|'size'|\"size\"|qa-b\b" -- bin hooks agents skills ':!skills/*/history' ':!skills/*/changelog.md'` (NEVER print whole output: huge; pipe through `awk -F: '{print $1":"$2}'` and filter). Source hits in bin/ to allow-list (file:line, reason): squad-log-message:44, squad-migrate:83, squad-respawn:29,37, squad-spawn:112,124, squadadopt.py (converter, 364-485), squadcompose.py:57 (_OLD_LINES),78,307,308, squadinbox.py:201, squadreport*.py (display), squadrules.py (OLD_WHEN_KEYS, legacy_team), squadruntime.py:368, squadteam.py:82,88, squadupgrade.py (old-when table); hooks/po-inbox/*.ts (check). Write allow-list into ticket file + a permanent test (tests/test_old_language_inventory.py) failing on a hit outside the list.
2. AC29: `grep -iw size` over PO-visible output (squad-start, squad-spawn, squad-process who, Manager proposal, new scope.md); reword "file size" etc.
3. Changelog v9 (skills/squad-process-update/changelog.md): confirm no rule IDs changed by me (fixtures only); add line if the BASE diff test needs.
4. `squad-process lint` on base 2175bd2 (git archive to mktemp -d) vs branch; record both in ticket file (G2b). Check tests/test_process_conversion.py line ~76 size sweep still passes.
5. Run `grep -rl` of touched paths in tests/ (bin/squadrules.py squadcompose.py squadupgrade.py squadteam.py squadrules_cli.py, tests/rulesview.py, fixtures/rules) and every hit (cd tests && python3 -m unittest test_x) .
6. evidence.md (## Behaviour) per EVID-2a; HANDIN to plugin-qaw-drop-scope-size, plugin-qab-drop-scope-size, plugin-tech-drop-scope-size; STATUS to plugin-tl-drop-scope-size.
