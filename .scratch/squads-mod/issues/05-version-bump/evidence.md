## Review
AC trace:
- T3.1 | `.claude-plugin/plugin.json` 0.9.0, `skills/squad-process-update/changelog.md` v14 | `git diff 5d7af34 -- .claude-plugin skills`
- T3.1b | `grep -rn "0\.8\.1" .claude-plugin` | no hit (exit 1)
- T2.10 | `hooks/squads/fixtures/real.json` already present (from 03) | `ls hooks/squads/fixtures`
- SQ-6b | merge of 04 (66f78c5) into this branch, no conflict | `git log --merges -2`
- SQ-10 | the three files below | `python3 tests/<file>.py`

## Behaviour
- test_windows_safe 14 OK; test_utf8_helpers 14 OK; test_instructions 16 OK.
- Targeted: test_processlint 31 OK, test_promotion_0_6_0 3 OK, test_squadupgrade 29 OK, test_old_language_inventory 2 OK (one allow-list line added for `hooks/squads/testkit.ts`, a false positive: `fs.stat size`).
- `claude plugin test`: 644 pass, 0 fail.
- Version 0.9.0 (new feature, minor bump). Changelog block v14 has no rule changes.
