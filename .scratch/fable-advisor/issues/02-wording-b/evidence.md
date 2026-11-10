# Evidence 02 wording B

## Behaviour
- EVID-3a: "your confirmation (no `PASS`, [LC-27]) is the verdict" (AC1).
- REV-9 rewritten: shots/`## Behaviour` are a starting point; run the app for every AC a shot does not clearly prove and the obvious unhappy paths; never sign off from shots alone. SIZE-8b and SIZE-17d say the same; START-13 already says "walk ... on the running app" (unchanged, 60-word lint cap) (AC2).
- Irreversible choice: SIZE-22 row "recommend; the PO decides", closing line cites [ITER-2] (Manager-always attached; WHO-2e attaches only with an Architect). WHO-2d row: Manager recommends after an advisor call; the PO decides (AC3).
- when-keys: ITER-3b `team-lead = no` (qa-black dropped). REV-14a: an evidence-only commit ([MRG-2]) needs no diff check. EVID-2b/2d/2e: NOT widened, see Open below (AC4).
- Citations: ITER-2, ITER-17, CORE-3 -> [WHO-1a], [WHO-1d], [WHO-3a], [WHO-5]; GOAL-6b -> [SUITE-1], [SUITE-1b], [SUITE-2d]; SUITE-1b and 2d lose the [SUITE-1] cite; SIZE-24b inlines the promote.md sentence (AC5).
- Small: SPAWN-10a idles 10 minutes before STATUS? ([MSG-8a]); suite rules say the full run needs the PO's yes, "Chieu" -> "the PO" in all templates (`grep -rn Chieu templates/squad/process` empty); `--tz` clause no longer says "Chieu is asked"; MSG-9 example `DECISION 13, 14:` (AC6).

## Open (needs Manager/QA whitebox ruling)
Finding 7 EVID-2d/2e with `tech-ac = dev` and a QA blackbox: no rule says who assembles. A single `when:` key cannot say "QAs on team and tech-ac = dev" (lint: at most one duty key). Widening to `tech-ac in qa-white, dev` attaches EVID-2d to every Developer with no QA and pushes the Developer rules to 5740 B (cap 5400). So left as is; a fix needs a new fact key in `bin/squadrules.py` (outside this ticket's Files).

## Byte budgets
Developer max 5358 B (cap 5400 unchanged). Manager bases in test_dev_rules_size.py +20..+335 B.

## AC trace
| AC | Test | How run |
|---|---|---|
| AC1 | `WordingBTest.test_manager_confirmation_is_not_a_pass` | `PYTHONPATH=tests python3 tests/test_rules_wording.py` |
| AC2 | `test_blackbox_never_signs_off_from_shots_alone` | same |
| AC3 | `test_the_po_decides_irreversible_choices` | same |
| AC4 | `test_when_keys` (ITER-3b, REV-14a) | same |
| AC5, AC6 | `test_citations_and_small_items` | same |
| AC7 | `squad-process lint --plugin-root .` exit 0; wording 27, contract 13, dev_rules_size 9 OK | as written |
Hits also run, OK: test_sizes, test_squadrules, test_team_duties, test_small_files_equivalence, test_squad_manager_guard, test_architect_handoff, test_qab_optional, test_squadupgrade. Full suite not run.
