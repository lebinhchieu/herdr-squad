## Behaviour
Docs and one version string only. Base: 11 passed sha ec5ebc0.

- T1: `grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md` prints nothing.
- T2 figures read from the tip: `grep -n "^phase:" templates/squad/process/*.md` gives 8 rules (MRG-2..5, CLOSE-2, CLOSE-4, CLOSE-5, ITER-6c); `grep LIMIT tests/test_dev_rules_size.py` gives 5440 (measured max 5433); `squad-process compose manager` is 566 lines and 47079 B, `compose tech-lead` 277 lines (promote.md said 278); the index is 20 lines (Manager) and 24 lines (Tech Lead) with the header, where promote.md said 20 and 25. The ADRs use the tip's numbers.
- T2 note: the squad report phase table holds turns and tokens per phase (ticket 07), not time windows as promote.md said; CONTEXT.md and README say what the tip does.
- T3: `grep -n '"version"' .claude-plugin/plugin.json` gives 0.8.0; `grep -rIn '0\.7\.7' --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=.scratch --exclude-dir=__pycache__ .` prints nothing. The changelog block is `## v12 — 2026-11-11`, first line "Plugin 0.8.0."
- T5: `bin/squad-merge-check`, `bin/squad-review-pack`, `bin/squad-task-prompt`, `bin/squad-evidence` exist; README usage copied from their `--help` (`squad-merge-check <branch-or-sha> [--base REF] [--scope DIR]`, `squad-review-pack NN [--sha S] [--base REF] [--scope DIR] [--max-lines N]`). README had no `squad-evidence` row, so I added one.
- T6: `squad-process lint --plugin-root .` exit 0. Hits of `grep -rl "CONTEXT.md\|changelog\|plugin.json\|docs/adr" tests/` run: test_squadupgrade, test_promotion_0_6_0, test_squadruntime, test_processlint, test_squad_start, test_squad_spawn, test_old_language_inventory, test_squad_respawn: all OK except the known `test_squad_spawn.test_a_failed_agent_start_leaves_the_old_overrides_file` (fails the same on 136f92f and b35c5d0, not caused here).
- T7: `grep -n Chieu CONTEXT.md docs/adr/002[345]*` prints nothing.
- Nothing from "Follow-ups" became a doc. SQ-2 stays for the Manager (remove after re-pin, WHO-6).

## Review
`git diff ec5ebc0..HEAD --stat` (this commit):
```
 .claude-plugin/plugin.json                         |  2 +-
 .scratch/fable-advisor/issues/12-promotion.md      | 29 ++++++++++++++++++++++
 CONTEXT.md                                         | 26 ++++++++++++++++++-
 README.md                                          | 14 +++++++----
 docs/adr/0023-phase-rules.md                       | 18 ++++++++++++++
 docs/adr/0025-developer-rule-byte-cap.md           | 16 ++++++++++++
 skills/squad-process-update/changelog.md           | 23 +++++++++++++++++
 9 files changed, 152 insertions(+), 7 deletions(-)
```
