# Evidence 18: rules for the Opus advisor

Branch `squad/plugin/sizes-and-models/plugin-dev-sm-18`.

## Behaviour
1. **AC5, advisor tool present with Haiku.** `claude -p --settings '{"model":"haiku","advisorModel":"opus"}' "Is a tool named advisor present? Reply with one word: yes or no."` → `yes`.
2. **Off value** (QA whitebox probe, same command): `"advisorModel":""` → `no`, settings load; `null` → settings file refused ("Expected string, but received null"). The overlay test uses `""`.
3. **Rules.** `who`: LC-25 = all roles incl. dev (3rd FAIL for the Developer); LC-26 = manager, tech-lead (S, M, L). COST-11 replaced. LC-25 defines the 2 rounds (same `BLOCKED` twice, no `ANSWER`) and the advisor-off case.
4. **Notice.** 3rd failing sha → "...consult the advisor before the next HANDIN; note it in the task file [LC-25]" (`test_squad_ledger` pins the full text).

5. **Dev rules cap (5120 B, ticket 22) kept.** LC-24 merged into LC-25 (Tech Lead DECISION 18); NOTE-1 no longer targets dev (still one `squad-process rule NOTE-1` away, added to `test_lost_rules_are_one_command_away`); COST-5's "ticket touching at most 2 files goes first to a live Developer…" sentence dropped (duplicate of COST-6a/6b, which dev does not act on). Worst combo now fits.

## Commands
`cd tests; PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_advisor_rules test_model_effort_settings test_squad_log_message test_squad_ledger test_processlint test_dev_rules_size test_team_lead_role`; `squad-process lint`.
