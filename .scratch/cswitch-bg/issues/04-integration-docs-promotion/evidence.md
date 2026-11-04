# 04 evidence

## Behaviour
- **Merge:** 02 (e8a7c5f) + 03 (7b34f06) merged with no conflict; `tests/ca_stubs.py` additions of both are kept (merge commit is a fast-forward-free merge of 7b34f06; `git log` shows 226ac18, 7b34f06 on top of 3c6a23f).
- **Docs diff** (`git diff 3c6a23f..c31825c -- HANDOFF.md skill/SKILL.md`: 2 files, +21 -7):
  - HANDOFF.md: new section "Skipped panes: background work, prompts, stuck panes" (skip + exit 75, log line `skipped: busy (<status>, <bg>)`, wait timeout `CSWITCH_WAIT_MS`, Escape on the dialog, SHORT_WAIT 60 s, MAX_INFLIGHT 2, backoff 2/4/8 capped at 10 ticks in memory, wake-step side effect, known limit); the autoswitch "Move" bullet no longer says "one at a time (unchanged)" or "a blocked pane is waited on"; the repro's "Recommended detection" is now "Detection" and says cswitch does it; the false "cswitch is untested end-to-end" note now says what is stub-tested and what is not live.
  - skill/SKILL.md: cautoswitch row says two at a time, 60 s each; new "Why was a pane not switched?" entry (shell/monitor/subagent/permission prompt is skipped, retried with backoff, how to read `skipped:` / `backoff:` / `deferred:` in `~/.claude-accounts/cswitch.log`). The skill is a symlink from `install.sh`, so no installed-copy note is needed.
- **promote.md:** nothing lasting beyond HANDOFF/skill; no CONTEXT.md term.
- **Suite** on c31825c: `PYTHONDONTWRITEBYTECODE=1 python3 tests/run_suite.py --receipt $SCOPE_DIR/evidence/04 --tz` (claude on PATH). Receipt: `/home/chieule/workspace/squad/.claude/squads/accounts/scopes/cswitch-bg/evidence/04/suite-tz.txt` and `suite-default.txt`. 1395 tests, 1 failure, 0 newly skipped: `test_squad_spawn.SpawnDryRunTest.test_a_failed_agent_start_leaves_the_old_overrides_file` (`0 == 0`). It fails the same way on the base 67d3543 (git archive in a temp dir, run alone), and this branch changes neither `bin/` nor `tests/test_squad_spawn.py`: not a regression. All `test_ca_*` files pass (autoswitch 53, launchers, install). `clean=no` in the receipt: the evidence files were not yet committed at run time.

## Review
- Claims in the new text checked against the code: `skip()` line format and exit 75, `CSWITCH_WAIT_MS` default 600000, Escape-only on the dialog, `SHORT_WAIT`/`POLL`/`MAX_INFLIGHT`/`BACKOFF_CAP` values, backoff formula `min(2**misses, cap)`.
- Found while writing: the skip at the dialog net happens after `cwake --mark`, so "a skipped pane has no marker" was wrong for that one path; HANDOFF now says so.
- Not run live: no real pane was switched. Stated in HANDOFF notes.
