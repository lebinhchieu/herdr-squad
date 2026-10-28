# QA whitebox 02 — sha 2de2487 — FAIL (1 finding)

Checked and OK: lint exit 0; own byte-identity run vs base 30de602: 9 roles x S/M/L x design x goal x qa-b x (absent|no) = 324 composed files, 0 diffs. Tests re-run OK: architect_handoff 15, templates 10, model_effort_settings 4, instructions 29, squad_spawn 72, squadadopt 29, task_id_rule 2, squadcompose 51, squadrules 55, processlint 31, dev_rules_size 7, process_history 6, process_writing 7, process_citations 4. Card/settings match designer's shape; deny set does not shadow architecture.md. All new rules are yes-gated blocks, one statement each. Override-row design (SIZE-22a, WHO-2e) accepted.

## F1 — flag-on Developer size is unguarded (Manager ruling FINAL 02, option a)
tests/test_dev_rules_size.py:15 LIMIT=5120 covers flag-off only. Flag-on: S+design yes = ~5.36 KiB+ (over), M/L flag-on 4.98 KiB (under); nothing stops later growth.
Pass: (1) add a test in tests/test_dev_rules_size.py (or test_architect_handoff.py) that composes the Developer file with `architecture: yes`, using the same fixture as `compose()` there (pin, live-length names), for every size x design x goal: M and L each <= 5120; S+design yes pinned at its current byte value (equality or <= that number, number written in the test); S+design no <= 5120. (2) Note the exception in the ticket's Design notes (last bullet) citing the ruling. Show red-then-green not needed; show the test run in evidence.

## Re-check a4a70ab — PASS
F1 fixed: flag-on M/L <=5120 test, all four flag-on S combos pinned exactly (5151/5152/5442/5443), exception noted in design notes citing the ruling. test_dev_rules_size 9 OK, test_sizes 36 OK. Diff 2de2487..a4a70ab = test + ticket note only.
