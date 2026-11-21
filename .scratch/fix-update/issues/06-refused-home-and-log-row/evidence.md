# 06 Skill: refused home no longer blocks the move; log row no longer says scopes keep their pin: evidence
sha: see HANDIN
## Review
AC trace:
- AC1 | `grep -rn 'keep their scope.md pin\|running scopes keep' bin skills README.md docs tests templates` prints nothing (exit 1); `grep -n -- '--only' skills/squad-process-update/SKILL.md` hits lines 18 and 21 | grep
- AC2 | `tests/test_squadupgrade.py::test_backup_log_and_scope_pin` (extended: log has `until squad-process homes moves them`, lacks the old text; old asserts kept) | `cd tests; python3 -m unittest test_squadupgrade`
- AC3 | QA blackbox walk; CLI behaviour already covered by `Homes.test_a_home_refused_at_read_is_named_by_apply_and_exits_2` and `test_a_refused_compose_writes_nothing` | unittest + QA walk
- AC4 | `## Behaviour` | unittest
- AC5 | `git diff 117c442 -- bin/squadhomes.py` empty | git diff

## Behaviour
Changes: `bin/squadupgrade.py` row text; SKILL.md step 4 (the exit 2 sentence now points to a refused-home bullet, 1 line added); changelog v21 one `changed:` line; one test extended.
Deviation, told to QA: the ticket's changelog line quotes the old text, which AC1's grep also searches (`skills/`). The line is worded "instead of the old claim that scopes in progress hold their scope.md pin" so AC1 prints nothing. The test's `assertNotIn` string is split in two literals for the same reason.
AC1: grep prints nothing, exit 1.
AC4: `cd tests; python3 -m unittest test_windows_safe test_utf8_helpers test_instructions test_squadupgrade test_promotion_0_6_0 test_squad_spawn`: Ran 200 tests, OK. `git diff 117c442 -- .claude-plugin/` and `-- bin/squadhomes.py`: empty.
Compatibility: no other file matches the old text; the `Upgraded plugin` prefix and first cell are unchanged.
Not done by me: the real `squad-inbox add` line and the three-command walk in a scratch squad are for QA blackbox (AC3); no Manager inbox session here.
