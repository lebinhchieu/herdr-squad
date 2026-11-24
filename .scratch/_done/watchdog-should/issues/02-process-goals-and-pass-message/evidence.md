## Behaviour

Rule text only; no runtime change. Developer rule size (`test_dev_rules_size`): largest composed Developer rules 5580 B, LIMIT 5580 (base 5573); LC-20a/20b/20e reworded to `STATUS NN: passed <sha>` in the same net size. LC-20b "Every checker PASS" wording was cut to fit.

Whole-repo tests (SQ-10), from `tests/`: `python3 -B -m unittest test_windows_safe test_utf8_helpers test_instructions test_dev_rules_size test_rules_contract test_sizes test_small_files_equivalence test_processlint test_rules_wording`: 138 OK. `test_squad_watchdog test_squad_start`: 120 OK. `test_promotion_0_6_0`: OK. `squad-process lint` (worktree `bin/`): exit 0.

Test edit: `tests/test_dev_rules_size.py` needle for LC-20a/20b changed from "Tell the ..." to "STATUS NN: passed".

## Review

AC trace: see `## Checks`.

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | `python3 bin/squad-process rule START-19b`; FILE-6 row in files.md; columns as the watchdog docstring | | |
| AC2 | `grep -n "first goal row" templates/squad/process/starting.md` (both Managers) | | |
| AC3 | `grep -n "STATUS NN: passed" templates/squad/process/lifecycle.md` (3 rules); `grep -n "goal done or blocked" templates/squad/process/messages.md` | | |
| AC4 | `grep -n "not copied" agents/team-lead.md` | | |
| AC5 | `grep -n "v18" skills/squad-process-update/changelog.md`; `grep -rn '0\.9\.4' .claude-plugin skills bin templates agents` only changelog | | |
| AC6 | `wc -l docs/adr/0028-watchdog-follows-goals-file.md` (under 30); names 0022 line 9 | | |
| AC7 | `python3 bin/squad-process lint`: exit 0; no date or incident in rules | | |
| AC8 | `python3 -B -m unittest test_windows_safe test_utf8_helpers test_instructions`: OK (in `## Behaviour`) | | |
| AC9 | `squad-evidence checks <evidence.md>`: exit 0 | | |
| AC10 | `python3 -B -m unittest test_dev_rules_size`: OK, 5580 B of 5580 | | |
| AC11 | START-19b columns equal the bin/squad-watchdog docstring | | |
| AC12 | `squad-process rule START-19b` shows `roles: manager`; hits run: test_rules_contract test_sizes test_small_files_equivalence test_processlint test_rules_wording OK | | |
| AC13 | ADR names 0022 line 9 | | |
| AC14 | same STATUS wording in LC-20a/20b/20e; MSG-6 item "a goal done or blocked" | | |
