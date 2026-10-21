# Evidence: 03 Convert the process into ID-tagged rule files (content v7)

**Result: 19 rule files, 256 rules, `squad-process lint` exits 0, `mapping.md` has 446 rows (every v6 line, log rows 33-49 and every card line). Developer composed size is 9.5 KB, over BD4's 5 KB line: an outcome question for the BA, not a FAIL.**

Files: `templates/squad/process/*.md`, `_removed.md` (empty), `skills/squad-process-update/changelog-v7.md`, `tests/test_process_conversion.py`; here `mapping.md`, `size-table.md`, `lint-cards-warn.txt`, `make_mapping.py`, `size_table.py`, `spec.txt`.

## Behaviour

**AC 1: lint exits 0 on `templates/squad/process/`.** Ran `python3 bin/squad-process lint --plugin-root "$PWD" --cards warn`: exit 0; stdout has only `warning:` lines (73 card duplicates, full list in `lint-cards-warn.txt`: ba 6, designer 4, dev 6, manager 25, qa-blackbox 5, qa-whitebox 8, team-lead 7, tech-lead 9, token-coach 2). `--cards error` exits 1 on those same 73, as designed until ticket 06 removes the card text. Pointers all resolve (02's pointer lint is merged: ed31b2b).

**AC 2: `mapping.md`, one row per source line.** `mapping.md` lists 446 rows: `templates/squad/process.md:<n>` for every non-blank, non-heading, non-table-header line, `agents/<role>.md:<n>` for every card line, `log row 33`..`log row 49`. Targets are rule IDs (comma list when a line is split across variants), `dropped: duplicate of <ID>`, `dropped: structure`, `dropped: replaced by compose`, or `stays in card`. `tests/test_process_conversion.py` checks every v6 line and every log row has a row, and every target ID exists. Log row numbers are the line numbers of the live `process-log.md` (untracked, so the test hard-codes 33-49: the non-`v<N>` rows dated 2026-10-16 to 2026-10-19).

**AC 3: rows 48 and 49.** `log row 48 | REV-16, REV-17` (Tech Lead writes `style-contract.md` for a scope with a UI mock; UI AC cite it; a QA lists all style findings of a sha in one return) and `log row 49 | REV-18a, REV-18b` (QA whitebox never asserts presentational values the mock fixes; QA blackbox owns them). Both live in `review.md`. The rest of rows 33-47 map to cost, lifecycle, starting, safety and message rules (live `process.md` wording); row 47 (ticket on files a live Developer changed goes to it under 120k) is missing from the live `process.md` too and is restored as `COST-6a`/`COST-6b`.

**AC 4: composed size per role and size** (stand-in script `size_table.py` over `squadrules.load_rules` and `matches`; facts: `design no` except Designer `yes`, `qa full`, `goal no`; bytes = heading plus body):

| Role | S bytes / rules | M bytes / rules | L bytes / rules |
|---|---|---|---|
| manager | 27930 / 94 | 27839 / 92 | 27839 / 92 |
| ba | 7239 / 31 | 8986 / 40 | 8986 / 40 |
| team-lead | 10306 / 40 | 16085 / 66 | 16085 / 66 |
| tech-lead | 14778 / 68 | 14199 / 63 | 14199 / 63 |
| qa-whitebox | 6102 / 31 | 9163 / 49 | 9163 / 49 |
| qa-blackbox | 6006 / 28 | 8451 / 44 | 8451 / 44 |
| designer | 6341 / 32 | 6646 / 34 | 6646 / 34 |
| dev | 9463 / 48 | 9517 / 48 | 9517 / 48 |
| token-coach | 2926 / 13 | 2926 / 13 | 2926 / 13 |

BA, Team Lead, QA whitebox and QA blackbox do not exist at S; the S cells show what `compose` would give them. The Manager row includes its own duties from `manager.md` (spawning, health checks, inbox, check-in); the index of other rules is not counted (04). Developer is 9.5 KB against the spec's "about 3-4 KB" (BD4: report, over 5 KB goes to the BA; the biggest Developer rules are `MSG-1` 470 B, `NOTE-1` 460 B, `START-6` 381 B, `LC-18` 353 B).

**AC 5: no "(S:" and no "In M and L" in rule text.**

```
$ grep -rn "(S:\|In M and L" templates/squad/process/
$ echo $?
1
```

`core.md` is 31 lines (limit 40).

**AC 6** is the checkers' audit of `mapping.md` against the sources.

## Where the collapsed duplicates landed (AC 03-2)

| Duplicate group | Surviving rule(s) | Dropped or split rows |
|---|---|---|
| "two real samples" (process, QA whitebox, Tech Lead) | `REV-4` (all three), `REV-5a` (S, Tech Lead runs it live), `REV-5b` (M, L, QA whitebox) | `P:214`, `qa-whitebox.md:22`, `tech-lead.md:27` map to these IDs |
| Roster write recipe (Manager, Team Lead) | `FILE-4` (utf-8, `newline="\n"`, `grep -c $'\r'`), `FILE-5a/5b/5c` for who edits which row | `manager.md:28`, `team-lead.md:28` |
| Cost-rule reaction (7 cards) | `COST-1` | `ba.md:13`, `designer.md:13`, `qa-blackbox.md:12`, `qa-whitebox.md:12`, `team-lead.md:15`, `tech-lead.md:13`, `dev.md:14` |
| Start boilerplate (9 cards) | `START-6` (echo, project.md, scope.md, roster, notes, start fresh), `START-7` (goal.md and `shared/`), `START-8` (QA blackbox: behaviour files only); Manager `START-18`, Token Coach `START-17` kept separate | each card's `Start of every session` line 1 |
| Notes sections of the cards | `NOTE-1`, `NOTE-2`, `NOTE-3` | `dropped: duplicate of NOTE-1` rows |

## Fixes (a)-(e)

- (a) `REV-13a` (S): `HANDIN` to the Tech Lead; `REV-13b` (M, L): to QA whitebox and QA blackbox, copy the Team Lead. `REV-14a`/`14b` do the same for a diff check.
- (b) `START-2d`: the Tech Lead tells the Manager which tasks are ready in parallel (S); `START-2a` has the Manager's side.
- (c) `MSG-16a` (S): Designer business doubt is an `ASK` to the Manager; `MSG-16b` (M, L): to the BA. No rule says the Tech Lead writes `escalations.md` (BD6; ticket text corrected).
- (d) `SPAWN-7` does not repeat "the label shape is in process.md".
- (e) Token Coach rules are `ITER-6` to `ITER-10`; `grep` for a "Retro" section citation finds none.

## Deviations the Tech Lead settled or should see

- Mapping target `dropped: structure` and `dropped: replaced by compose` (Tech Lead ANSWER 03); a comma list of rule IDs for a split line is an addition.
- `changelog-v7.md` instead of an entry in `changelog.md` (a `## v7` block breaks `test_process_history`; Tech Lead ANSWER 03).
- `tests/test_squadrules.py`: the 02 test `test_template_has_no_rule_files_yet` now expects rule files and a clean lint.
- Rules refer to `process.local.md` where v6 said `process.md` for the squad's own edits (`FILE-6`, `WHO-6`); in a composed squad `process.md` does not exist.
- `SPAWN-7`: v6 said "In S, when you point a QA at a new ticket, relabel it"; S has no QA, so the rule says "an agent".
- Card sections `You own / you don't`, `Notes` and the skeptic stance are mapped as `dropped: duplicate of` the WHO/NOTE rules or `stays in card`; the Manager's Writing rule (`manager.md:34-40`) stays in the card (design §03).
- `aware:` is used sparingly (`MSG-5`, `MSG-6`, `REV-3`, `REV-18a/b`, `LC-7b`): a full body costs the role its bytes, and the Manager and Tech Lead get an index of the rest.

## Tests

`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_process_conversion test_squadrules test_windows_safe` pass (74 tests); also `test_processlint test_squadprocess test_squadprocess_apply test_squadprocess_show test_process_history test_process_writing test_instructions test_process_citations test_pod_rules_process test_templates test_squad_start` pass (unchanged).
