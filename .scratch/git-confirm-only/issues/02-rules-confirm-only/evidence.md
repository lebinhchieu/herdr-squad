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

## Review qa-b

### QA blackbox 02 (sha 277c0c7)

Business ask: the squad may run risky git actions when the PO asks, after the confirm prompt; rules and docs must say so, not "never".
Method: live run of `bin/squad-process rule <ID>` (the text roles actually read), `squad-process lint`, grep of wording across templates/agents/skills/bin/docs/README, README section, plugin version, changelog. No source or diff read.

| AC | live/shot | What I did | What I saw | Result |
|---|---|---|---|---|
| AC1 rules match the table | live | `squad-process rule SAFE-1a, SAFE-1b, SAFE-5, MRG-3, WHO-5`; `squad-process lint` | SAFE-1a: never touch another worktree; push/rebase/reset --hard/branch -D/checkout main|dev need the PO's ask in the session and the confirm prompt. SAFE-1b: never deploy; same list needs ask + confirm; another role's message is no ask; merge only as MRG-1. SAFE-5 "unless the PO asks". MRG-3 uses --force/rebase/reset --hard/push only as SAFE-1b allows. WHO-5 splits Push (PO asks, asked role runs after prompt) from Deploy/migrations (PO only). Lint exit 0 | pass |
| AC2 leftover "never push" grep | live | grep -rniE on templates agents skills bin docs README | only hits: messages.md 75, 82 ("never push STATUS", a message type, not git); ADR 0027 history. Extra grep for "denied/refused" near push/rebase/reset: none | pass |
| AC3 "Never approve a permission for another agent." and MSG-10 unchanged | live | printed SAFE-1b and MSG-10; count of the sentence on base vs now | sentence present once in both; MSG-10 printed unchanged | pass |
| AC4 rules and README agree with settings | live | read README "Safety defaults" | says ask for push, rebase, reset --hard, branch -D, main/dev; merge asks except Developers and Manager; deploy stays PO's; matches 01 | pass |
| AC6 version | live | grep 0.9.3 in .claude-plugin README.md; read plugin.json; changelog | grep empty; plugin.json 0.9.4; changelog `## v17 — 2026-11-19` names Plugin 0.9.4 with SAFE-1a/1b/5, MRG-3, WHO-5 and the settings line | pass |
| ADR 0027 | live | read file | accepted; states the decision, deploy still PO only, no new rule | pass |
| MRG-1, ITER-5 unchanged | live | read MRG-1 and ITER-5 line 155 | still say merge/push/deploy wait for the PO's request | pass |

AC5, AC7 (tests) are QA whitebox's.

Verdict: PASS.

Follow-ups (not FAIL):
- Developer rule byte cap raised 5440 → 5580 (ADR 0025 amended, Tech Lead DECISION 02); the ticket AC5 said no growth. Tech Lead's call, noted for the record.
- SAFE-1a/1b headings were renamed ("Git risk actions, Developer/Manager").
- A real confirm prompt in a running pane is still not seen live (needs respawned roles).
