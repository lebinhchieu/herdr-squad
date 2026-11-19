# 02 evidence

## Review
| AC | Test or capture | How run |
|---|---|---|
| AC1 | `templates/squad/process/{safety,merge,who}.md` diff; `squad-process lint` | `python3 bin/squad-process lint` → lint ok |
| AC2 | grep below | `grep -rniE 'never push\|never use[sd]? .*push\|no push\|never (rebase\|reset)\|denied for every' templates agents skills bin docs README.md` |
| AC3 | "Never approve a permission for another agent." unchanged in SAFE-1b; MSG-10 untouched | `git diff HEAD~1 -- templates/squad/process/safety.md` |
| AC4 | README and rules say "ask"; no "denied" for these actions | same grep |
| AC5 | `tests/test_dev_rules_size.py`, `tests/test_sizes.py` | `python3 -m unittest discover -s tests -p <file>` |
| AC6 | `plugin.json` 0.9.4; changelog v17 | `grep -rn '0\.9\.3' .claude-plugin README.md` → empty |
| AC7 | `test_windows_safe`, `test_utf8_helpers`, `test_instructions` | same runner |

## Behaviour
- Tech Lead DECISION 02 overrides AC 5 "may not grow past the caps": SAFE-1a shortened; measured Dev maximum 5574 B (base 5433), `LIMIT` 5440 → 5580, ADR 0025 amended (ceiling 5620).
- `test_dev_rules_size.py`: 9 tests OK. `test_sizes.py`: 8 tests OK.
- SQ-10: `test_windows_safe` 14 OK, `test_utf8_helpers` 14 OK, `test_instructions` 16 OK.
- Also OK: test_rules_wording 30, test_processlint 31, test_small_files_equivalence 2, test_rules_contract 14, test_squadrules 44, test_squadsettings 25 (before the final SAFE-1a text; unaffected). `squad-process lint` ok.
- AC 2 grep hits that stay: `messages.md` lines 75 and 82, "never push `STATUS`" (about the STATUS message, not git). No hit in ITER-5, LC-13, tech-lead card or ADR history.
- SAFE-1a/1b headings renamed ("Git risk actions, Developer/Manager") since "No push" would now be false; IDs and headers unchanged.
