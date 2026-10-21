# Evidence: 03 Convert the process into ID-tagged rule files (content v7)

**Result: 19 rule files, 255 rules, `squad-process lint` exits 0, `mapping.md` has 446 rows (every v6 line, log rows 33-49 and every card line). Developer composed size is 9.5 KB, over BD4's 5 KB line: an outcome question for the BA, not a FAIL.**

Files: `templates/squad/process/*.md`, `_removed.md` (empty), `skills/squad-process-update/changelog-v7.md`, `tests/test_process_conversion.py`; here `mapping.md`, `size-table.md`, `lint-cards-warn.txt`, `make_mapping.py`, `size_table.py`, `spec.txt`.

## Behaviour

**AC 1: lint exits 0 on `templates/squad/process/`.** Ran `python3 bin/squad-process lint --plugin-root "$PWD" --cards warn`: exit 0; stdout has only `warning:` lines (72 card duplicates, full list in `lint-cards-warn.txt`: ba 6, designer 4, dev 6, manager 25, qa-blackbox 5, qa-whitebox 8, team-lead 7, tech-lead 9, token-coach 2). `--cards error` exits 1 on those same 72, as designed until ticket 06 removes the card text. Pointers all resolve (02's pointer lint is merged: ed31b2b).

**AC 2: `mapping.md`, one row per source line.** `mapping.md` lists 446 rows: `templates/squad/process.md:<n>` for every non-blank, non-heading, non-table-header line, `agents/<role>.md:<n>` for every card line, `log row 33`..`log row 49`. Targets are rule IDs (comma list when a line is split across variants), `dropped: duplicate of <ID>`, `dropped: structure`, `dropped: replaced by compose`, or `stays in card`. `tests/test_process_conversion.py` checks every v6 line and every log row has a row, and every target ID exists. Log row numbers are the line numbers of the live `process-log.md` (untracked, so the test hard-codes 33-49: the non-`v<N>` rows dated 2026-10-16 to 2026-10-19).

**AC 3: rows 48 and 49.** `log row 48 | REV-16, REV-17` (Tech Lead writes `style-contract.md` for a scope with a UI mock; UI AC cite it; a QA lists all style findings of a sha in one return) and `log row 49 | REV-18a, REV-18b` (QA whitebox never asserts presentational values the mock fixes; QA blackbox owns them). Both live in `review.md`. The rest of rows 33-47 map to cost, lifecycle, starting, safety and message rules (live `process.md` wording); row 47 (ticket on files a live Developer changed goes to it under 120k) is missing from the live `process.md` too and is restored as `COST-6a`/`COST-6b`.

**AC 4: composed size per role and size** (stand-in script `size_table.py` over `squadrules.load_rules` and `matches`; facts: `design no` except Designer `yes`, `qa full`, `goal no`; bytes = heading plus body):

| Role | S bytes / rules | M bytes / rules | L bytes / rules |
|---|---|---|---|
| manager | 27910 / 94 | 27819 / 92 | 27819 / 92 |
| ba | 7235 / 31 | 8982 / 40 | 8982 / 40 |
| team-lead | 10302 / 40 | 16081 / 66 | 16081 / 66 |
| tech-lead | 14758 / 68 | 14179 / 63 | 14179 / 63 |
| qa-whitebox | 6098 / 31 | 9159 / 49 | 9159 / 49 |
| qa-blackbox | 6002 / 28 | 8447 / 44 | 8447 / 44 |
| designer | 5962 / 31 | 6267 / 33 | 6267 / 33 |
| dev | 9459 / 48 | 9513 / 48 | 9513 / 48 |
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
