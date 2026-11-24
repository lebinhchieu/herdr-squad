# 06 Skill: refused home no longer blocks the move; log row no longer says scopes keep their pin: evidence
sha: fcb98c5
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

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | grep old text in bin skills README docs tests templates: no hit (exit 1); `--only` at SKILL.md:18,21 | grep for the old log text in bin skills README docs tests templates: no hit; grep --only in SKILL.md: lines 18 and 21 |live: log row reads "until squad-process homes moves them"; SKILL.md exit 2 flow read |
| AC2 | `python3 -m unittest test_squadupgrade`: OK (test_backup_log_and_scope_pin extended) | read test_backup_log_and_scope_pin diff; test_squadupgrade OK in my run |n/a: QA whitebox's |
| AC3 | `Homes.test_a_home_refused_at_read...` and `test_a_refused_compose_writes_nothing`: OK; scratch walk left to QA blackbox | from tests/: Homes tests for read-refused and refused-compose OK; scratch walk is QA blackbox's |live: check exit 2, no --only refuses and writes nothing, --only g1 s1 exit 0, s2 untouched, inbox add ok, no composing home (qa-b.md) |
| AC4 | 6 test files, 200 tests, OK; `git diff 117c442 -- .claude-plugin/` empty | from tests/: unittest test_windows_safe test_utf8_helpers test_instructions test_squadupgrade test_promotion_0_6_0 test_squad_spawn: 200 OK; git diff 117c442 on .claude-plugin: empty |n/a: QA whitebox's |
| AC5 | `git diff 117c442 -- bin/squadhomes.py` empty | git diff 117c442 fcb98c5 --stat on bin/squadhomes.py: empty |n/a: QA whitebox's |

## QA blackbox

### 06 QA blackbox on fcb98c5 (CLI output)
Scratch squad: old pin 0.10.1 (5aadae0), new plugin = fcb98c5 (0.10.2), goal g1 with scopes s1, s2 (no live agents but the Manager), s2 `plugin: garbage` (a refused home). I followed SKILL.md step 4's new Exit 2 bullet. Real herdr, live agents mid-turn and a new tab not run (Chieu's merge check).

| AC | What I did | What I saw | Result |
|---|---|---|---|
| AC1/log row | `upgrade --apply --yes`, read the new row in `process-log.md` | `Upgraded plugin 0.10.1 5aadae0... -> 0.10.2 fcb98c5...; open scopes and goals keep their own pin until squad-process homes moves them`; `applied:` line and `plugin.pin` write unchanged; old rows untouched | pass |
| AC3 check | `homes --check` | table: goal g1 `moves`, scope s1 `moves`, scope s2 `refused` + note `plugin: line 7: expected ...`; exit 2 | pass |
| AC3 no --only | `homes --apply --yes` | `refused scope s2: ... (deselect it with --only)`, table, exit 2; md5 listing of the squad identical before/after (nothing written) | pass |
| AC3 inbox | `squad-inbox add --kind answer --title "Move goal g1 to plugin 0.10.2: 2 homes (1 refused)" --body-file body.md --options "(a) move g1, s1 and respawn now; (b) move only g1; (c) leave them"`, body names the refused s2 and why | `1 new item in the inbox: Move goal g1 to plugin 0.10.2: 2 homes (1 refused)`, exit 0 | pass |
| AC3 (a) | `homes --apply --yes --only g1 s1` | exit 0: `moved goal g1`, `moved scope s1`, caller line; goal.md and s1 scope.md `plugin:` = 0.10.2; two new `Home ...` rows in process-log.md; s2 scope.md byte-identical (cmp) and no row for it; check after: g1 and s1 at-target, s2 still refused | pass |
| AC3 no composing home | lone scope s3 `plugin: garbage`, SCOPE_DIR=s3 | `homes --check` exit 2, only a `refused` row, no `moves` row; per the skill text "no home can move now", no item, step 5; (apply without --only refuses, nothing changed, no Home log rows) | pass |
| AC1 text | read SKILL.md step 4 | exit 2 bullet: show words, `moves` rows compose, none -> "no home can move now", else ONE item, (a) `--only <every composing home name>`, (b) `--only <goal home name>`, (c) stop, "without `--only` the apply refuses and writes nothing"; exit 3 flow unchanged | pass |

AC2, AC4, AC5 are QA whitebox's.

## QA whitebox

### QA whitebox 06 (fcb98c5): PASS

- AC1 no hit for the old log text in bin skills README docs tests templates; `--only` in the exit 2 flow (SKILL.md line 18) and the goal-only flow.
- AC2 log row in bin/squadupgrade.py:560-561 is "open scopes and goals keep their own pin until squad-process homes moves them"; prefix, cells and write order unchanged; the test asserts the new text and the absence of the old one (the literal is split so AC1's grep stays empty).
- AC3 code side: squadhomes.run() `bad` only counts refused homes inside `--only`, so `--apply --yes --only <composing names>` moves them and without `--only` raises `refused ... (deselect it with --only)`; both are covered by existing Homes tests. The scratch walk is QA blackbox's.
- AC4 6 files, 200 tests OK from tests/; `git diff 117c442 -- .claude-plugin` empty. AC5 `git diff 117c442 fcb98c5 -- bin/squadhomes.py` empty.
- Changelog v21 gets one line; its wording avoids the old phrase on purpose.
No follow-ups.
