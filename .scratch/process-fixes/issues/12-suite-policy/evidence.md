# Evidence 12 suite policy: targeted by default, ask Chieu before a full suite

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 statement once, others point | `git diff templates/squad/process/suites.md` | read the diff; `tests/test_rules_wording.py`, `tests/test_squadrules.py` (lint: 60 words, no repeated sentence) |
| AC2 ASK named in one place | SUITE-1 only; SUITE-1b points to it | `grep -n 'ASK <task>: full suite' templates/squad/process/suites.md CLAUDE.md` |
| AC3 grep rule and `--tz` stay | CLAUDE.md diff, SUITE-3/3b text | `git diff CLAUDE.md` |
| AC4 CLAUDE.md first + runner bullet | CLAUDE.md lines 46, 48; other bullets untouched | `git diff CLAUDE.md` |
| AC5 version 0.7.5 | grep below | `grep -rn '0\.7\.4' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude` |
| AC6 touched tests + hits pass | list below | `cd tests && python3 -m unittest <names>` |

## Behaviour

- AC1: SUITE-1 (Tech Lead owner) holds the whole statement: default targeted (touched files + `grep -rl` hits), full only after `ASK` and Chieu's yes through the Manager ([ITER-4]), `project.md` may redefine. SUITE-1b (QA whitebox owner) says the default and points to [SUITE-1] for the ask. SUITE-2d, 3, 3b, 4, 4b point to [SUITE-1] / [SUITE-1b] by ID. Words per rule: SUITE-1 57, SUITE-1b 49 (limit 60). SUITE-2a/2b/2c/2e/2f/5/6 never run the full suite and are unchanged.
- AC2: `grep -n 'ASK <task>: full suite'` hits suites.md once (SUITE-1) and CLAUDE.md once (first bullet, same text as the rule).
- AC3: the `templates/`/`bin/` grep bullet is untouched. SUITE-3 and 3b say the `--tz` run is full and Chieu is asked at the merge. CLAUDE.md runner bullet adds the same.
- AC4: only the first and runner bullets changed.
- AC5: `grep -rn '0\.7\.4'` (excluded dirs as in the AC) now hits only `.scratch/` history (tickets 09, 12 and evidence 09); `plugin.json:4` reads `"version": "0.7.5"`. No test pins the version.
- AC6: pinned strings updated in `tests/test_rules_contract.py` (3 needles) and `tests/test_dev_rules_size.py` (Manager byte budget for the qa-white team, +109 B). Ran test_rules_contract, test_dev_rules_size, test_sizes, test_rules_wording, test_squadrules, test_run_suite, test_qab_optional, test_squad_spawn, test_squad_respawn, test_squad_start, test_squadupgrade, test_promotion_0_6_0, test_squadruntime, test_team_cli, test_squadscaffold, test_squadboard_tasks: 1 failure, `test_squad_spawn...test_a_failed_agent_start_leaves_the_old_overrides_file`, same on base (see evidence 09, 11). Full suite NOT run (QA whitebox asks Chieu first).
- Reading note for QA: AC1 says "SUITE-1 and 1b" hold the statement. I put the ask text only in SUITE-1 (AC2 "one place") and let 1b point to it, to fit the 60-word lint.
