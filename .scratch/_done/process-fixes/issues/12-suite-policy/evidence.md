# Evidence 12 suite policy: targeted by default, ask Chieu before a full suite

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 statement once, others point | `git diff templates/squad/process/suites.md` | read the diff; `tests/test_rules_wording.py`, `tests/test_squadrules.py` (lint: 60 words, no repeated sentence) |
| AC2 ASK reaches each suite owner | SUITE-1 (Tech Lead), SUITE-1b (QA whitebox), SUITE-2d (Developer) each carry the ASK sentence; 3/3b/4/4b point | `grep -n 'ASK <task>: full suite' templates/squad/process/suites.md CLAUDE.md` |
| AC3 grep rule and `--tz` stay | CLAUDE.md diff, SUITE-3/3b text | `git diff CLAUDE.md` |
| AC4 CLAUDE.md first + runner bullet | CLAUDE.md lines 46, 48; other bullets untouched | `git diff CLAUDE.md` |
| AC5 version 0.7.5 | grep below | `grep -rn '0\.7\.4' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude` |
| AC6 touched tests + hits pass | list below | `cd tests && python3 -m unittest <names>` |

## Behaviour

- AC1: SUITE-1 (Tech Lead owner) holds the whole statement: default targeted (touched files + `grep -rl` hits), full only after `ASK` and Chieu's yes through the Manager ([ITER-4]), `project.md` may redefine. SUITE-1b (QA whitebox owner) and SUITE-2d (Developer owner) each carry the default and the one-sentence ASK (to the Manager, wait for Chieu's yes), pointing to [SUITE-1] for the full text (FAIL 12 F1 fix). SUITE-2d, 3, 3b, 4, 4b point to [SUITE-1] / [SUITE-1b] by ID. Words per rule: all within the 60-word lint. SUITE-2a/2b/2c/2e/2f/5/6 never run the full suite and are unchanged.
- AC2: each owner's composed rule has the ASK sentence: SUITE-1 (Tech Lead), SUITE-1b (QA whitebox), SUITE-2d (Developer). `grep -n 'ASK <task>: full suite' templates/squad/process/suites.md` hits those three; the rules that only point (3, 3b, 4, 4b) do not repeat it.
- AC3: the `templates/`/`bin/` grep bullet is untouched. SUITE-3 and 3b say the `--tz` run is full and Chieu is asked at the merge. CLAUDE.md runner bullet adds the same.
- AC4: only the first and runner bullets changed.
- AC5: `grep -rn '0\.7\.4'` (excluded dirs as in the AC) now hits only `.scratch/` history (tickets 09, 12 and evidence 09); `plugin.json:4` reads `"version": "0.7.5"`. No test pins the version.
- AC6: pinned strings updated in `tests/test_rules_contract.py` (3 needles) and `tests/test_dev_rules_size.py` (Manager byte budget for the qa-white team, +109 B). Ran test_rules_contract, test_dev_rules_size, test_sizes, test_rules_wording, test_squadrules, test_run_suite, test_qab_optional, test_squad_spawn, test_squad_respawn, test_squad_start, test_squadupgrade, test_promotion_0_6_0, test_squadruntime, test_team_cli, test_squadscaffold, test_squadboard_tasks: 1 failure, `test_squad_spawn...test_a_failed_agent_start_leaves_the_old_overrides_file`, same on base (see evidence 09, 11). Full suite NOT run (QA whitebox asks Chieu first).
- After FAIL F1: SUITE-2d trimmed so the dev composed rules stay under the 5 KiB test; budgets +156 B total for the qa-white Manager team; `test_rules_contract` needle `then once on your final sha`. Re-run: 137 tests OK (contract, dev_rules_size, sizes, wording, squadrules, scaffold, run_suite, qab_optional, team_cli).
