
sha: e0eacd0
## Behaviour
Docs and one version string only. Base: 11 passed sha ec5ebc0.

- T1: `grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md` prints nothing.
- T2 figures read from the tip: `grep -n "^phase:" templates/squad/process/*.md` gives 8 rules (MRG-2..5, CLOSE-2, CLOSE-4, CLOSE-5, ITER-6c); `grep LIMIT tests/test_dev_rules_size.py` gives 5440 (measured max 5433); `squad-process compose manager` is 566 lines and 47079 B, `compose tech-lead` 277 lines (promote.md said 278); the index is 20 lines (Manager) and 24 lines (Tech Lead) with the header, where promote.md said 20 and 25. The ADRs use the tip's numbers.
- T2 note: the squad report phase table holds turns and tokens per phase (ticket 07), not time windows as promote.md said; CONTEXT.md and README say what the tip does.
- T3: `grep -n '"version"' .claude-plugin/plugin.json` gives 0.8.0; `grep -rIn '0\.7\.7' --exclude-dir=.git --exclude-dir=.worktrees --exclude-dir=.scratch --exclude-dir=__pycache__ .` prints nothing. The changelog block is `## v12 — 2026-11-11`, first line "Plugin 0.8.0."
- Return (SUITE-5): the three new full-suite failures now pass. `python3 tests/test_windows_safe.py` OK (squadmergecheck.py `encoding="utf-8"`); `python3 tests/test_utf8_helpers.py` OK (token-coach stderr must hold ITER-6c; stdout stays one JSON line, so the tool is unchanged); `python3 tests/test_instructions.py` OK (the `--goal` token is read from `templates/squad/process/closing.md`, CLOSE-4's phase file). Also OK: test_squad_close, test_squad_merge_check, test_squad_review_pack, test_small_files_equivalence. test_squad_spawn: 1 failure, `test_a_failed_agent_start_leaves_the_old_overrides_file`, fails on main too.
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

## QA blackbox

### QA blackbox 12 (sha e0eacd0, dev-fable-w)
Docs and version only. I read CONTEXT.md, ADRs, README and changelog diffs (docs, not code) and ran the commands below read-only in the dev-w worktree.

| AC | live | what I did | what I saw | result |
|---|---|---|---|---|
| AC1 promote.md entries committed, no `<fill>` | live | `grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md`; read each entry against `promote.md` | no hits (rc 1). Glossary (passed sentence, Check table, Phase rule, Review pack, shots, irreversible choice, ticket phase, task prompt, merge check), ADR 0023-0025, README rows, changelog v12 all present. Figures: `grep -n "^phase:"` 8 rules (MRG-2..5, CLOSE-2/4/5, ITER-6c); `LIMIT = 5440`. No "Follow-ups" became a doc, except the ADR 0024 line on `|` cells, which restates a follow-up (harmless) | pass |
| AC2 ADR shape | live | `grep -n "^## "` and `head -3` on 0022 and 0023-0025 | `# NNNN: <sentence>`, `Status: accepted`, Context / Decision / Consequences in all three; numbers 0023-0025 | pass |
| AC3 version 0.8.0, changelog v12 | live | `grep -n '"version"' .claude-plugin/plugin.json`; `grep -rIn '0\.7\.7' ...` ; changelog head | 0.8.0; no 0.7.7 left (rc 1); `## v12 — 2026-11-11`, first line "Plugin 0.8.0." | pass |
| AC4 lint, evidence | live | `squad-process lint --plugin-root .`; read evidence.md | rc 0; evidence has `## Behaviour`, `## Review` | pass |
| Extra: no code change | live | `git diff ec5ebc0..HEAD --stat -- bin templates tests` | empty | pass |
| Extra: README tools | live | `ls bin/<tool>`, `--help` of merge-check, review-pack, task-prompt | all exist; usage in README matches | pass |
| Extra: no "Chieu" | live | `grep -n Chieu CONTEXT.md docs/adr/002[345]*` | none | pass |

#### Follow-ups (not AC breaks)
- README rows run two sentences together with no full stop: `squad-watchdog` ("...the log tail Besides the idle wake-ups..."), `squad-spawn` ("...has the details) `squad-spawn --task NN`..."), `squad-close` ("none is deleted It prints..."), `squad-process` ("...squad-process-update drives it `phase <name>`..."). Cosmetic; fix with a "." or ";".
- The `## Review` stat in the Developer's evidence.md shows 9 files and omits `docs/adr/0024-...`; the real diff `ec5ebc0..HEAD` is 11 files (also ticket 11 evidence).

## QA whitebox

### QA whitebox: 12 promotion, sha e0eacd0 (base ec5ebc0)
Verdict: PASS. Checked in a detached worktree, read-only.

- T1 `grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md`: 0 hits.
- T2 figures re-measured on the tip: `grep -n "^phase:" templates/squad/process/*.md` = 8 (MRG-2..5, CLOSE-2/4/5, ITER-6c) as ADR 0023 says; LIMIT 5440; composing manager and tech-lead with this scope's team (tech-lead, qa-white, qa-black, qa full) gives manager 566 lines 47048 B index 20, tech-lead 277 lines index 24: matches ADR 0023.
- T3 `"version": "0.8.0"` (the only change in plugin.json); `grep -rIn '0\.7\.7'` (excluding .git .worktrees .scratch __pycache__) prints nothing; changelog `## v12 — 2026-11-11`, first line "Plugin 0.8.0."
- T4 `git diff ec5ebc0..HEAD --name-only` has no bin/, templates/ or tests/ path; only CONTEXT.md, docs/adr/0023-0025, README.md, changelog, plugin.json and the 11/12 ticket and evidence files.
- T5 `--help` of squad-merge-check and squad-review-pack match the README usage; squad-task-prompt usage (its error line) matches; squad-evidence has path/add/check/checks as the README says.
- T6 `squad-process lint --plugin-root .` exit 0. Tests (grep hits): old_language_inventory 2, processlint 31, promotion_0_6_0 3, squad_respawn 21, squadruntime 68, squad_start 49, squadupgrade 29: OK. squad_spawn 106: 1 failure, the known pre-existing `test_a_failed_agent_start_leaves_the_old_overrides_file`.
- T7 `grep -n Chieu CONTEXT.md docs/adr/002[345]*`: nothing. ADRs have the title, Status: accepted, Context, Decision, Consequences.

Follow-ups (not blocking, wording only)
- README.md `bin/squad-close` row: "none is deleted It prints the close-phase rules" has no full stop; `bin/squad-process` row: "drives it `phase <name>`..." has no separator.
- CONTEXT.md "Passed" says "the watchdog and the board read..."; the Dashboard entry says avoid "board" (0009). Say "dashboard".
- 12 evidence `## Review` stat lists 7 of 9 files (the 0024 ADR line is missing).

## Tech Lead review

### Tech Lead review 12, sha e0eacd0 (dev-w)
- T1 `grep -rn "<fill>" CONTEXT.md docs/adr README.md skills/squad-process-update/changelog.md`: empty.
- T2 `grep -n "^phase:" templates/squad/process/*.md`: 8 rules (merge.md x4, closing.md x3, iterations.md x1). `LIMIT = 5440`. Compose for this team on the tip: Manager 566 lines / 46991 B, Tech Lead 277 lines, index 20 and 24 incl. header. The ADR numbers match the tip; differences from promote.md (index 20/24, TL 277, report phases are turns+tokens) are right.
- T3 plugin.json version 0.8.0; `grep -rIn '0\.7\.7' ...` empty. Changelog v12 first line "Plugin 0.8.0."; every rule ID in it exists (COST-8b, LC-6c, ITER-18, EVID-9..9e).
- T4 `git diff 651755a..e0eacd0 --stat`: only listed Files + ticket 12 file + its evidence. No bin/, templates/, tests/.
- T5 four README tools exist; usage lines match `--help`.
- T6 `squad-process lint` rc 0. Targeted tests (processlint, squadupgrade, old_language_inventory, promotion_0_6_0, squad_respawn, squadruntime, squad_start, squad_spawn): 309 run, 1 fail = known pre-existing test_a_failed_agent_start_leaves_the_old_overrides_file.
- T7 no "Chieu" in CONTEXT.md / ADR 0023-0025.
- EVID-2c: `squad-evidence check .scratch/fable-advisor/issues/12-promotion --base e0eacd0` rc 0 (evidence is in e0eacd0; accept again if later commits are evidence-only).
Verdict: PASS (Tech Lead). QAs give their own.
