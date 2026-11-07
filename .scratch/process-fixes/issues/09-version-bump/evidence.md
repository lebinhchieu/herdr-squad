# Evidence 09 version bump 0.7.3 -> 0.7.4

## Review

| AC | Test or capture | How run |
|---|---|---|
| AC1 version reads 0.7.4 everywhere 0.7.3 was named | grep output below | `grep -rn '0\.7\.3' . --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=_runtime --exclude-dir=.claude` (no hit); `grep -n '"version"' .claude-plugin/plugin.json` |
| AC2 tests that pin the version pass | no test pins 0.7.3; the 7 test files naming `plugin.json` pass (one pre-existing failure, below) | `grep -rl 'plugin\.json' tests/ --include=*.py`, then `cd tests && python3 -m unittest <name>` per hit |
| AC3 nothing else changes | `git diff --stat main..HEAD` | plugin.json (1 line), the ticket file, this evidence |

## Behaviour

- AC1: before the edit the grep found only `.claude-plugin/plugin.json:4: "version": "0.7.3"`. After: the same grep finds nothing; `grep -n '"version"' .claude-plugin/plugin.json` prints `4:  "version": "0.7.4",`. README and changelog never named the version.
- AC2: `grep -rl 'plugin\.json' tests/` hits `squadtest.py` (helper, no tests) and 6 test files. Results: test_squad_start 44 OK, test_squadupgrade 29 OK, test_promotion_0_6_0 3 OK, test_squad_respawn 21 OK, test_squadruntime 68 OK, test_squad_spawn 94 run, 1 failure.
  - The failure is `SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (`assertNotEqual(r.returncode, 0)`: got 0). It fails the same way on a `git archive HEAD` copy of the base (0.7.3), so it is not caused by this bump. Cause not investigated (outside AC3).
- AC3: one line in `plugin.json`; the ticket file and this evidence are the only other additions.
