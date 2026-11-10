## Behaviour
Merged `plugin-dev-fable-c` (b35c5d0) then `plugin-dev-fable-b` (b54f582) into the 09 branch (tip 136f92f). Both merges ran clean, no conflicts. Merged tip: 2da9234 (the HANDIN sha ec5ebc0 is 2da9234 plus this evidence file).

- AC1: `git merge-base --is-ancestor <sha> HEAD` is true for 136f92f, b35c5d0, b54f582, d0a112f, 52da3ef, 07a7be3, ea90150.
- AC2: no conflicts. Measured max composed Developer rules after merge is 5433 B, rounded up to 20 B = 5440, so `LIMIT` stays 5440 (cap 5480).
- AC3: `PYTHONPATH=tests python3 tests/<file>.py` (watchdog: `python3 -m unittest test_squad_watchdog`) for every test file touched by 01-10: architect_handoff, dev_rules_size, rules_contract, rules_wording, small_files_equivalence, squad_close, squad_evidence, squad_merge_check, squad_report_cli, squad_report_query, squad_review_pack, squad_spawn, squad_watchdog, squadcompose, squadreport_digest, squadreport_tasks, squadrules: all OK except one in squad_spawn. `squad-process lint --plugin-root .`: 0 problems. No full suite.
- Known failure: `test_squad_spawn.test_a_failed_agent_start_leaves_the_old_overrides_file` (returncode 0, expected nonzero). It fails the same on 136f92f and on b35c5d0 before this merge, so it is not caused by the merge.
