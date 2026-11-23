# Evidence: 04 rules, ADR, glossary, changelog, version 0.10.10

## Review

### Review

AC trace:
- AC1 | merge of 01 (22593e0), 02 (e1e4e88), 03 (c3edb63) into this branch, no conflict; tests below | `git log --merges`
- AC2 | tests/test_rules_wording.py `test_bundle_long_wait_and_experiment_rules` (COST-8b, `squad-respawn --lazy`) | python3 tests/test_rules_wording.py
- AC3 | same test, COST-15 strings; `git diff main -- templates/squad/process/cost.md` shows no edit to COST-3, COST-5, COST-10b | python3 tests/test_rules_wording.py
- AC4 | test_rules_wording, test_instructions, test_processlint, test_process_writing | python3 tests/<file>.py; compose for manager and dev lists COST-15 in the `rules:` line
- AC5 | docs/adr/0033-watchdog-respawns-roles.md | read
- AC6 | skills/squad-process-update/changelog.md `## v28` | read
- AC7 | CONTEXT.md **Lazy respawn**, **Cold cache**, **Idle** after **Watchdog** | read
- AC8 | `grep -rn '0\.10\.9' .claude-plugin tests/` empty | grep
- AC9 | ADR and glossary exist (promote.md rows 1-2) | ls, read
- AC10 | test_windows_safe, test_utf8_helpers, test_instructions | python3 tests/<file>.py
- AC11 | no watchdog, respawn or herdr run; compose ran on a mktemp -d home | read

### Behaviour

Tests run (all OK): test_rules_wording (30), test_rules_contract, test_squadupgrade, test_promotion_0_6_0, test_squadruntime, test_squad_start, test_squad_respawn, test_squad_spawn, test_lazy_hook, test_squad_watchdog (unittest discover), test_processlint (31), test_process_writing; SQ-10: test_windows_safe (14), test_utf8_helpers (14), test_instructions (16). No full suite (DECISION 0). The first lint run flagged COST-8b and COST-15 over 60 words; both shortened.

`grep -rln '0\.10\.9' . --exclude-dir=.git --exclude-dir=.scratch`: only `skills/squad-process-update/changelog.md` (past entries and the v28 rollback line): kept. `.claude-plugin/plugin.json` now 0.10.10; marketplace.json has no `version` (grep, 0 hits); no test pins 0.10.9.

Rule index: `squad-process compose` in a scratch home lists COST-15 for `manager` and `dev`.

Open follow-up: a real UserPromptSubmit `session_id` equal to `squad-spawn --session-id`, to be confirmed once on the first lazy respawn in a scratch squad (not run here, safety).

## Checks

| AC | Dev: test or capture | QA whitebox: check | QA blackbox: check |
|---|---|---|---|
| AC1 | git log --merges; targeted tests OK |  |  |
| AC2 | test_rules_wording OK |  |  |
| AC3 | test_rules_wording OK; cost.md diff |  |  |
| AC4 | 4 test files OK; compose index |  |  |
| AC5 | read ADR 0033 |  |  |
| AC6 | read changelog v28 |  |  |
| AC7 | read CONTEXT.md |  |  |
| AC8 | grep 0.10.9 |  |  |
| AC9 | files exist |  |  |
| AC10 | SQ-10 three files OK |  |  |
| AC11 | no live run |  |  |
